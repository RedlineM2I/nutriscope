from typing import Dict, Tuple

from src.models import Report
from src.strategie import DEFAULT_STRATEGY

import pandas as pd

KCAL_MAX = 900.0
SALT_PER_SODIUM = 2.5
KJ_PER_KCAL = 4.184

RATIO_KCAL_LOW = 3.9
RATIO_KCAL_HIGH = 4.5
NUTRIMENT_MAX = 100.0
SODIUM_MAX = 40.0
CONSISTENCY_DELTA = 0.5

COUNTER_COLUMNS = ["nutriscore_score", "nova_group"]

KEY_NUTRIENTS = ["energy_100g",
    "sugars_100g",
    "carbohydrates_100g",
    "fat_100g",
    "saturated-fat_100g",
    "salt_100g",
    "proteins_100g",
    "fiber_100g",
    "sodium_100g",
    "fruits-vegetables-legumes_100g"
]   

def normalize_units(df: pd.DataFrame) -> Tuple[pd.DataFrame, Report]:
    """Règle de normalisation des unités :
    - Convertit les kJ en kcal si ces derniers sont absents (kcal = kJ / 4,184) ou si le rapport kJ / kcal 
      sort de l'intervalle [3,9 ; 4,5]
    - Calcule le sel ou le sodium si l'un est manquant (sel = sodium x 2,5), et recalcule le sodium depuis le sel s'il est incohérent""" 

    # Copie de df
    res = df.copy()

    rows_before = len(df)

    kj = res["energy_100g"].copy()
    kcal = res["energy-kcal_100g"].copy()
    sel = res["salt_100g"].copy()
    sodium = res["sodium_100g"].copy()

    # Calcul de kcal depuis kJ si absent
    kcal_derived_mask = kcal.isna() & kj.notna()
    kcal.loc[kcal_derived_mask] = (kj.loc[kcal_derived_mask] / KJ_PER_KCAL).round(1)

    # Recalcul de kcal si ratio kJ/kcal hors de l'interval [3.9 ; 4.5].
    ratio_kj_kcal = kj / kcal
    kcal_recomputed_mask = (
        kj.notna()
        & kcal.notna()
        & (kcal != 0)
        & ((ratio_kj_kcal < RATIO_KCAL_LOW) | (ratio_kj_kcal > RATIO_KCAL_HIGH))
    )
    kcal.loc[kcal_recomputed_mask] = (kj.loc[kcal_recomputed_mask] / KJ_PER_KCAL).round(1)

    # Dérivations sel <-> sodium dans les deux sens
    salt_derived_mask = sel.isna() & sodium.notna()
    sel.loc[salt_derived_mask] = (sodium.loc[salt_derived_mask] * SALT_PER_SODIUM).round(4)

    sodium_derived_mask = sodium.isna() & sel.notna()
    sodium.loc[sodium_derived_mask] = (sel.loc[sodium_derived_mask] / SALT_PER_SODIUM).round(4)

    # Sodium recalculé depuis le sel si incoherent.
    sodium_recomputed_mask = (
        sodium.notna() & sel.notna() & ~sodium_derived_mask & ((sel - sodium * SALT_PER_SODIUM).abs() > 1e-6)
    )
    sodium.loc[sodium_recomputed_mask] = (sel.loc[sodium_recomputed_mask] / SALT_PER_SODIUM).round(4)

    res["energy-kcal_100g"] = kcal
    res["salt_100g"] = sel
    res["sodium_100g"] = sodium

    touched_rows = (kcal_derived_mask | kcal_recomputed_mask | salt_derived_mask | sodium_derived_mask | sodium_recomputed_mask).sum()

    report = Report(
        rule="normalize_units",
        lines_before=rows_before,
        lines_after=len(res),
        affected_lines=int(touched_rows),
        details={
            "kcal_derivees": int(kcal_derived_mask.sum()),
            "kcal_recalculees": int(kcal_recomputed_mask.sum()),
            "sel_derive": int(salt_derived_mask.sum()),
            "sodium_derive": int(sodium_derived_mask.sum()),
            "sodium_recalcule": int(sodium_recomputed_mask.sum()),
        },
    )

    return res, report
    

def normalize_texts(df: pd.DataFrame) -> Tuple[pd.DataFrame, Report]:
    return df, None 


def limit_nutriments(df: pd.DataFrame) -> Tuple[pd.DataFrame, Report]:
    """Règle de bornage des nutriments :
    - Si des nutriments sont négatifs, ces derniers sont déclarés NA à la place
    - Si des nutriments sont au-dessus de 100 g/100 g -> NA (exception pour le sodium borné à 40 g/100 g).
    - Si sucres > glucides + 0,5 -> sucres = NA.
    - Si saturés > lipides + 0,5 -> saturés = NA.
    """
    res = df.copy(deep=True)

    rows_before = len(df)
    details: Dict[str, int] = {}

    nutrient_columns = [
        "carbohydrates_100g",
        "sugars_100g",
        "fat_100g",
        "saturated-fat_100g",
        "salt_100g",
        "sodium_100g",
        "proteins_100g",
        "fiber_100g",
    ]

    # Nombre de lignes touchées (au moins une modification sur la ligne).
    touched_rows_mask = pd.Series(False, index=res.index)

    for col in nutrient_columns:
        if col not in res.columns:
            continue

        series = pd.to_numeric(res[col], errors="coerce").copy()
        max_bound = SODIUM_MAX if col == "sodium_100g" else NUTRIMENT_MAX

        negatives_mask = series < 0
        above_bound_mask = series > max_bound
        invalid_values_mask = negatives_mask | above_bound_mask

        series.loc[invalid_values_mask] = pd.NA
        res[col] = series

        touched_rows_mask |= invalid_values_mask
        details[f"{col}_negatifs"] = int(negatives_mask.sum())
        details[f"{col}_au_dessus"] = int(above_bound_mask.sum())

    # Cohérence sucres vs glucides
    sugars_inconsistent_mask = pd.Series(False, index=res.index)
    if "sugars_100g" in res.columns and "carbohydrates_100g" in res.columns:
        sugars = pd.to_numeric(res["sugars_100g"], errors="coerce").copy()
        carbs = pd.to_numeric(res["carbohydrates_100g"], errors="coerce")
        sugars_inconsistent_mask = sugars.notna() & carbs.notna() & (sugars > carbs + CONSISTENCY_DELTA)
        sugars.loc[sugars_inconsistent_mask] = pd.NA
        res["sugars_100g"] = sugars
        touched_rows_mask |= sugars_inconsistent_mask

    # Cohérence saturés vs lipides
    saturated_inconsistent_mask = pd.Series(False, index=res.index)
    if "saturated-fat_100g" in res.columns and "fat_100g" in res.columns:
        saturated_fat = pd.to_numeric(res["saturated-fat_100g"], errors="coerce").copy()
        fat = pd.to_numeric(res["fat_100g"], errors="coerce")
        saturated_inconsistent_mask = saturated_fat.notna() & fat.notna() & (saturated_fat > fat + CONSISTENCY_DELTA)
        saturated_fat.loc[saturated_inconsistent_mask] = pd.NA
        res["saturated-fat_100g"] = saturated_fat
        touched_rows_mask |= saturated_inconsistent_mask

    details["sucres"] = int(sugars_inconsistent_mask.sum())
    details["satures"] = int(saturated_inconsistent_mask.sum())

    report = Report(
        rule="limit_nutriments",
        lines_before=rows_before,
        lines_after=len(res),
        affected_lines=int(touched_rows_mask.sum()),
        details=details,
    )

    return res, report
    
def fix_energy(df: pd.DataFrame) -> Tuple[pd.DataFrame, Report]:
    """Règle de correction de l'énergie :
    - Recalcule les kcal nulles avec les macronutriments en utilisant la formule de recalcul 4/4/9
    - Pareil pour les kcal supérieurs à 900, si imposssible : NA
    - Si des valeur kcal sont incohérentes (> 50% d'écart vs calcul 4/4/9 ou si calcul >= 50) : on recalcule
    - Aucune correction sur le rayon Alcoholic beverages
    - kJ réalignés sur les kcal finales
    """
    res = df.copy(deep=True)

    rows_before = len(df)

    kcal = pd.to_numeric(res["energy-kcal_100g"], errors="coerce").copy()
    kj = pd.to_numeric(res["energy_100g"], errors="coerce").copy()
    carbs = pd.to_numeric(res["carbohydrates_100g"], errors="coerce")
    proteins = pd.to_numeric(res["proteins_100g"], errors="coerce")
    fat = pd.to_numeric(res["fat_100g"], errors="coerce")

    # Calcul 4/4/9 (possible si au moins un macronutriment est présent)
    calc = carbs.fillna(0) * 4 + proteins.fillna(0) * 4 + fat.fillna(0) * 9
    has_macros = carbs.notna() | proteins.notna() | fat.notna()

    # Exception rayon alcool.
    if "rayon" in res.columns:
        alcohol_mask = res["rayon"].astype("string").eq("Alcoholic beverages")
    else:
        alcohol_mask = pd.Series(False, index=res.index)
    eligible_mask = ~alcohol_mask

    # Si kcal nulles -> recalcul si macronutriments disponibles
    missing_kcal_recomputed_mask = eligible_mask & kcal.isna() & has_macros
    kcal.loc[missing_kcal_recomputed_mask] = calc.loc[missing_kcal_recomputed_mask].round(1)

    # Si kcal > 900 -> recalcul si macronurtiments disponibles, sinon NA
    over_900_mask = eligible_mask & kcal.notna() & (kcal > KCAL_MAX)
    over_900_recomputed_mask = over_900_mask & has_macros
    over_900_invalidated_mask = over_900_mask & ~has_macros
    kcal.loc[over_900_recomputed_mask] = calc.loc[over_900_recomputed_mask].round(1)
    kcal.loc[over_900_invalidated_mask] = pd.NA

    # Si kcal incoherentes > 50% du calcul 4/4/9 si calcul >= 50.
    calc_eligible_mask = has_macros & (calc >= 50)
    relative_gap = (kcal - calc).abs() / calc.where(calc != 0)
    inconsistent_recomputed_mask = (
        eligible_mask
        & kcal.notna()
        & calc_eligible_mask
        & (relative_gap > 0.5)
        & ~over_900_mask
    )
    kcal.loc[inconsistent_recomputed_mask] = calc.loc[inconsistent_recomputed_mask].round(1)

    res["energy-kcal_100g"] = kcal

    # Réalignement des kJ depuis kcal finales.
    kj.loc[kcal.notna()] = (kcal.loc[kcal.notna()] * KJ_PER_KCAL).round(1)
    res["energy_100g"] = kj

    touched_rows_mask = (
        missing_kcal_recomputed_mask
        | over_900_recomputed_mask
        | over_900_invalidated_mask
        | inconsistent_recomputed_mask
    )

    report = Report(
        rule="fix_energy",
        lines_before=rows_before,
        lines_after=len(res),
        affected_lines=int(touched_rows_mask.sum()),
        details={
            "nulles_recalculees": int(missing_kcal_recomputed_mask.sum()),
            ">900_recalculees": int(over_900_recomputed_mask.sum()),
            ">900_invalidees": int(over_900_invalidated_mask.sum()),
            "incoherentes_recalculees": int(inconsistent_recomputed_mask.sum()),
        },
    )

    return res, report


def set_column_types(df: pd.DataFrame) -> tuple[pd.DataFrame, Report]:
    """Fixe les types de colonnes attendus par la suite du pipeline :
    code en string, compteurs (nova_group, nutriscore_score) en
    Int64 nullable, nutriments en float64. Ne modifie aucune valeur,
    seulement le dtype.
    """
    rows_before = len(df)
    df = df.copy()
    df["code"] = df["code"].astype("string")
    for col in COUNTER_COLUMNS:
        df[col] = df[col].astype("Int64")
    for col in KEY_NUTRIENTS:
        df[col] = df[col].astype("float64")

    report = Report(
        rule="typer_colonnes",
        lines_before=rows_before,
        lines_after=len(df),
        affected_lines=0,  # aucune valeur changée, que des dtypes
        details={},
    )
    return df, report


def deduplicate_codes(df: pd.DataFrame) -> tuple[pd.DataFrame, Report]:
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
    missing_code_mask = df["code"].isna() | (df["code"].str.strip() == "")
    nb_missing_code = int(missing_code_mask.sum())
    res = res.loc[~missing_code_mask]

    # Supprime les doublons de code
    sorted_res = res.sort_values(["completeness", "last_modified_t"], ascending=[False, False], kind="stable")
    duplicate_code_mask = sorted_res.duplicated(subset="code", keep="first")
    nb_duplicates = int(duplicate_code_mask.sum())
    res = res.loc[~duplicate_code_mask]

    report = Report(
        rule="Dédupliquer les codes",
        lines_before=len(df),
        lines_after=len(res),
        affected_lines=nb_missing_code + nb_duplicates,
        details={
            "sans_code": nb_missing_code,
            "doublons_supprimes": nb_duplicates,
        }
    )
    return res, report


def handle_empty_categories(df: pd.DataFrame) -> tuple[pd.DataFrame, Report]:
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
    nb_empty_category = int(res["category_empty"].sum())

    # Nettoie le food_group
    raw_food_group = res["food_groups_tags"].str[0]
    nb_missing_food_group = int(raw_food_group.isna().sum())
    res["food_group"] = raw_food_group.fillna("unknown")

    drop_mask = res["category_empty"] & (res["food_group"] == "unknown")
    nb_unclassifiable = int(drop_mask.sum())

    rows_touched = int((res["category_empty"] | (res["food_group"] == "unknown")).sum())

    res = res[~drop_mask]

    report = Report(
        rule="traiter_categories_vides",
        lines_before=len(df),
        lines_after=len(res),
        affected_lines=rows_touched,
        details={
            "categorie_vide": nb_empty_category,
            "food_group_derive_de_vide": nb_missing_food_group,
            "food_group_unknown_total": int((res["food_group"] == "unknown").sum()) + nb_unclassifiable,
            "inclassables_supprimes": nb_unclassifiable,
        }
    )
    return res, report


def _apply_flag(df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, int]:
    """Crée `<colonne>_empty` (booléen) sans toucher à la colonne d'origine.
    Retourne le nombre de valeurs manquantes détectées.
    """
    res = df.copy()
    mask = res[column].isna()
    res[f"{column}_empty"] = mask
    return res, int(mask.sum())


def _apply_constant(df: pd.DataFrame, column: str, raw_value: str) -> int | tuple[pd.DataFrame, int]:
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


def _apply_median_by_department(df: pd.DataFrame, column: str) -> int | tuple[pd.DataFrame, int]:
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


def _apply_mode(df: pd.DataFrame, column: str) -> int | tuple[pd.DataFrame, int]:
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


def missing_values_strategy(df: pd.DataFrame, strategy: dict[str, str] = DEFAULT_STRATEGY) -> tuple[pd.DataFrame, Report]:
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

    cr = Report(
        rule="strategie_manquants",
        lines_before=rows_before,
        lines_after=len(res),
        affected_lines=rows_touched,
        details=details,
    )
    return res, cr
