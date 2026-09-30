from dataclasses import dataclass, field
from typing import Dict, Tuple

import pandas as pd

KCAL_MAX = 900.0
SALT_PER_SODIUM = 2.5
KJ_PER_KCAL = 4.184

RATIO_KCAL_LOW = 3.9
RATIO_KCAL_HIGH = 4.5
NUTRIMENT_MAX = 100.0
SODIUM_MAX = 40.0
CONSISTENCY_DELTA = 0.5

@dataclass
class CompteRendu:
    regle: str
    lignes_avant: int
    lignes_apres: int
    lignes_touchees: int
    details: Dict[str, int] = field(default_factory=dict)
    
    
def normalize_units(df: pd.DataFrame) -> Tuple[pd.DataFrame, CompteRendu]:
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

    report = CompteRendu(
        regle="normalize_units",
        lignes_avant=rows_before,
        lignes_apres=len(res),
        lignes_touchees=int(touched_rows),
        details={
            "kcal_derivees": int(kcal_derived_mask.sum()),
            "kcal_recalculees": int(kcal_recomputed_mask.sum()),
            "sel_derive": int(salt_derived_mask.sum()),
            "sodium_derive": int(sodium_derived_mask.sum()),
            "sodium_recalcule": int(sodium_recomputed_mask.sum()),
        },
    )

    return res, report
    

def limit_nutriments(df: pd.DataFrame) -> Tuple[pd.DataFrame, CompteRendu]:
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

    report = CompteRendu(
        regle="limit_nutriments",
        lignes_avant=rows_before,
        lignes_apres=len(res),
        lignes_touchees=int(touched_rows_mask.sum()),
        details=details,
    )

    return res, report
    
def fix_energy(df: pd.DataFrame) -> Tuple[pd.DataFrame, CompteRendu]:
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

    report = CompteRendu(
        regle="fix_energy",
        lignes_avant=rows_before,
        lignes_apres=len(res),
        lignes_touchees=int(touched_rows_mask.sum()),
        details={
            "nulles_recalculees": int(missing_kcal_recomputed_mask.sum()),
            ">900_recalculees": int(over_900_recomputed_mask.sum()),
            ">900_invalidees": int(over_900_invalidated_mask.sum()),
            "incoherentes_recalculees": int(inconsistent_recomputed_mask.sum()),
        },
    )

    return res, report