from dataclasses import dataclass, field

import pandas as pd
from pandas import DataFrame

from src.strategie import DEFAULT_STRATEGY

COLONNES_COMPTEURS = ["nutriscore_score", "nova_group"]

KEY_NUTRIENTS = ["energy_100g",
                 "sugars_100g",
                 "carbohydrates_100g",
                 "fat_100g",
                 "saturated-fat_100g",
                 "salt_100g",
                 "proteins_100g",
                 "fiber_100g",
                 "sodium_100g",
                 "fruits-vegetables-legumes_100g"]


@dataclass
class CompteRendu:
    regle: str
    lignes_avant: int
    lignes_apres: int
    lignes_touchees: int
    details: dict[str, int] = field(default_factory=dict)


def typer_colonnes(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Fixe les types de colonnes attendus par la suite du pipeline :
    code en string, compteurs (nova_group, nutriscore_score) en
    Int64 nullable, nutriments en float64. Ne modifie aucune valeur,
    seulement le dtype.
    """
    lignes_avant = len(df)
    df = df.copy()
    df["code"] = df["code"].astype("string")
    for col in COLONNES_COMPTEURS:
        df[col] = df[col].astype("Int64")
    for col in KEY_NUTRIENTS:
        df[col] = df[col].astype("float64")

    compte_rendu = CompteRendu(
        regle="typer_colonnes",
        lignes_avant=lignes_avant,
        lignes_apres=len(df),
        lignes_touchees=0,  # aucune valeur changée, que des dtypes
        details={},
    )
    return df, compte_rendu


def dedupliquer_codes(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """
    Normalise les codes-barres (espaces), écarte les lignes sans code,
    et ne garde qu'une fiche par code : en cas de doublon, on retient
    la plus complète (`completeness` la plus haute), puis en cas d'égalité
    la plus récente (`last_modified_t` le plus grand).
    :param df: DataFrame à nettoyer
    :return: DataFrame nettoyé et compte rendu de ce qui a été modifié
    """
    res = df.copy()
    res["code"] = res["code"].str.strip()

    # Ecarte les lignes sans code
    masque_sans_code = df["code"].isna() | (df["code"].str.strip() == "")
    nb_sans_code = int(masque_sans_code.sum())
    res = res.loc[~masque_sans_code]
    print(f"{nb_sans_code} lignes sans code supprimés")

    # Supprime les doublons de code
    res_trie = res.sort_values(["completeness", "last_modified_t"], ascending=[False, False], kind="stable")
    masque_code_duplique = res_trie.duplicated(subset="code", keep="first")
    nb_dupliques = int(masque_code_duplique.sum())
    res = res.loc[~masque_code_duplique]
    print(f"{nb_dupliques} lignes avec un code en double supprimés")

    cr = CompteRendu(
        regle="Dédupliquer les codes",
        lignes_avant=len(df),
        lignes_apres=len(res),
        lignes_touchees=nb_sans_code + nb_dupliques,
        details={
            "sans_code": nb_sans_code,
            "doublons_supprimes": nb_dupliques,
        }
    )
    return res, cr


def traiter_categories_vides(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """
    Ajout de 'main_category' dérivé du dernier tag de 'categories_tags'
    Ajout d'un drapeau 'category_empty' pour les categories vides
    Ajout d'une colonne 'food_group' pour le rayon dérivé du premier élément de 'food_groups_tags'
    ayant 'unknown pour les rayons vide
    Suppression de tous les produits ayant une categorie vide et un rayon unknown
    :param df: DataFrame à nettoyer
    :return: DataFrame nettoyé et compte rendu de ce qui a été modifié
    """
    res = df.copy()

    # Ajoute 'main_category' et un drapeau
    res["main_category"] = res["categories_tags"].str[-1]
    res["category_empty"] = res["main_category"].isna()
    nb_category_empty = int(res["category_empty"].sum())

    # Nettoie le food_group
    food_group_sale = res["food_groups_tags"].str[0]
    nb_food_group_vide = int(food_group_sale.isna().sum())
    res["food_group"] = food_group_sale.fillna("unknown")

    drop_mask = res["category_empty"] & (res["food_group"] == "unknown")
    nb_inclassables = int(drop_mask.sum())

    lignes_touchees = int((res["category_empty"] | (res["food_group"] == "unknown")).sum())

    res = res[~drop_mask]

    cr = CompteRendu(
        regle="traiter_categories_vides",
        lignes_avant=len(df),
        lignes_apres=len(res),
        lignes_touchees=lignes_touchees,
        details={
            "categorie_vide": nb_category_empty,
            "food_group_derive_de_vide": nb_food_group_vide,
            "food_group_unknown_total": int((res["food_group"] == "unknown").sum()) + nb_inclassables,
            "inclassables_supprimes": nb_inclassables,
        }
    )
    return res, cr


def _apply_flag(df: pd.DataFrame, column: str) -> tuple[DataFrame, int]:
    """Crée `<colonne>_empty` (booléen) sans toucher à la colonne d'origine.
    Retourne le nombre de valeurs manquantes détectées.
    """
    res = df.copy()
    mask = res[column].isna()
    res[f"{column}_empty"] = mask
    return res, int(mask.sum())


def _apply_constant(df: pd.DataFrame, column: str, raw_value: str) -> int | tuple[DataFrame, int]:
    """Remplace les manquants de `colonne` par une constante, castée au dtype
    de la colonne pour éviter de polluer une colonne numérique avec une string.
    """
    res = df.copy()
    mask = res[column].isna()
    nb_missing = int(mask.sum())
    if nb_missing == 0:
        return 0
    value = pd.Series([raw_value]).astype(res[column].dtype).iloc[0]
    res[column] = res[column].fillna(value)
    return res, nb_missing


def _apply_median_by_department(df: pd.DataFrame, column: str) -> int | tuple[DataFrame, int]:
    """Remplace chaque manquant par la médiane de son propre rayon (`res['rayon']`).
    Usage applicatif uniquement (affichage/substitution) : ne remplace pas
    l'imputation ML, qui se fait après le split, dans le pipeline dédié.
    """
    res = df.copy()
    mask = res[column].isna()
    nb_missing = int(mask.sum())
    if nb_missing == 0:
        return 0
    res[column] = res.groupby("rayon")[column].transform(lambda s: s.fillna(s.median()))
    return res, nb_missing


def _apply_mode(df: pd.DataFrame, column: str) -> int | tuple[DataFrame, int]:
    """Remplace les manquants par la valeur la plus fréquente de la colonne.
    En cas d'égalité entre plusieurs modes, la première (ordre pandas) est retenue.
    """
    res = df.copy()
    mask = res[column].isna()
    nb_missing = int(mask.sum())
    if nb_missing == 0:
        return 0
    mode_value = res[column].mode(dropna=True).iloc[0]
    res[column] = res[column].fillna(mode_value)
    return res, nb_missing


def missing_values_strategy(df: pd.DataFrame, strategy: dict[str, str] = DEFAULT_STRATEGY) -> tuple[pd.DataFrame, CompteRendu]:
    """Applique une décision par colonne pour traiter les valeurs manquantes.

    Vocabulaire fermé pour `strategy[colonne]` :
        - "keep"            : ne rien faire.
        - "flag"           : ajoute `<colonne>_manquant` (booléen), sans imputer.
        - "constant:<v>"     : remplace les manquants par la valeur `<v>`.
        - "foodgroup_median"     : impute par la médiane du rayon (usage applicatif,
                                 pas une imputation ML — voir docstring des helpers).
        - "mode"              : impute par la valeur la plus fréquente.
        - "drop_column" : retire la colonne du DataFrame.

    En complément, toute ligne n'ayant AUCUN nutriment clé renseigné est supprimée
    (un produit sans aucune valeur nutritionnelle n'a pas sa place dans le catalogue).

    Lève `ValueError` si une décision ne fait partie d'aucune des six catégories.
    """
    res = df.copy()
    rows_before = len(res)
    details: dict[str, int] = {}
    dropped_columns: list[str] = []
    global_touched_mask = pd.Series(False, index=res.index)

    for column, decision in strategy.items():
        match decision:
            case "keep":
                continue

            case "flag":
                res, nb = _apply_flag(res, column)
                global_touched_mask |= res[f"{column}_manquant"]

            case "foodgroup_median":
                mask_before = res[column].isna()
                res, nb = _apply_median_by_department(res, column)
                global_touched_mask |= mask_before

            case "mode":
                mask_before = res[column].isna()
                res, nb = _apply_mode(res, column)
                global_touched_mask |= mask_before

            case "drop_column":
                nb = 1
                dropped_columns.append(column)
                res = res.drop(columns=[column])

            case _ if decision.startswith("constant:"):
                mask_before = res[column].isna()
                res, nb = _apply_constant(res, column, decision.split(":", 1)[1])
                global_touched_mask |= mask_before

            case _:
                raise ValueError(f"Décision inconnue '{decision}' pour la colonne '{column}'")

        details[f"{column}:{decision.split(':')[0]}"] = nb

    # Suppression des lignes sans aucun nutriment clé
    no_key_nutrient_mask = res[KEY_NUTRIENTS].isna().all(axis=1)
    nb_no_key_nutrient = int(no_key_nutrient_mask.sum())
    res = res.loc[~no_key_nutrient_mask]

    rows_touched = int(global_touched_mask.reindex(res.index, fill_value=False).sum()) + nb_no_key_nutrient
    details["dropped_columns"] = dropped_columns
    details["rows_dropped_no_nutrient"] = nb_no_key_nutrient

    cr = CompteRendu(
        regle="strategie_manquants",
        lignes_avant=rows_before,
        lignes_apres=len(res),
        lignes_touchees=rows_touched,
        details=details,
    )
    return res, cr