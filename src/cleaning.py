from dataclasses import dataclass, field

import pandas as pd

COLONNES_COMPTEURS = ["nutriscore_score", "nova_group"]

COLONNES_NUTRIMENTS = ["energy_100g",
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
    for col in COLONNES_NUTRIMENTS:
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
    masque_code_duplique = res_trie.duplicated(subset="code",keep="first")
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

    #Ajoute 'main_category' et un drapeau
    res["main_category"] = res["categories_tags"].str[-1]
    res["category_empty"] = res["main_category"].isna()
    nb_category_empty = int(res["category_empty"].sum())

    #Nettoie le food_group
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