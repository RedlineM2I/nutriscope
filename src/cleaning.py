from dataclasses import dataclass, field

import pandas as pd

KCAL_MAX = 900.0
SALT_PER_SODIUM = 2.5
KJ_PER_KCAL = 4.184

RATIO_KCAL_LOW = 3.9
RATIO_KCAL_HIGH = 4.5
NUTRIMENT_MAX = 100.0
SODIUM_MAX = 40.0
COHERENCE_DELTA = 0.5

@dataclass
class CompteRendu:
    regle: str
    lignes_avant: int
    lignes_apres: int
    lignes_touchees: int
    details: dict[str, int] = field(default_factory=dict)
    
def normalize_units(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Règle de normalisation des unités :
    - Convertit les kJ en kcal si ces derniers sont absents (kcal = kJ / 4,184) ou si le rapport kJ / kcal 
      sort de l'intervalle [3,9 ; 4,5]
    - Calcule le sel ou le sodium si l'un est manquant (sel = sodium x 2,5), et recalcule le sodium depuis le sel s'il est incohérent""" 

    # Copie de df
    res = df.copy()

    lignes_avant = len(df)

    kj = res["energy_100g"]
    kcal = res["energy-kcal_100g"]
    sel = res["salt_100g"]
    sodium = res["sodium_100g"]

    # Calcul de kcal depuis kJ si absent
    kcal_derivees_mask = kcal.isna() & kj.notna()
    kcal.loc[kcal_derivees_mask] = (kj.loc[kcal_derivees_mask] / KJ_PER_KCAL).round(1)

    # Recalcul de kcal si ratio kJ/kcal hors de l'interval [3.9 ; 4.5].
    ratio_kj_kcal = kj / kcal
    kcal_recalculees_mask = (
        kj.notna()
        & kcal.notna()
        & (kcal != 0)
        & ((ratio_kj_kcal < RATIO_KCAL_LOW) | (ratio_kj_kcal > RATIO_KCAL_HIGH))
    )
    kcal.loc[kcal_recalculees_mask] = (kj.loc[kcal_recalculees_mask] / KJ_PER_KCAL).round(1)

    # Dérivations sel <-> sodium dans les deux sens
    sel_derive_mask = sel.isna() & sodium.notna()
    sel.loc[sel_derive_mask] = (sodium.loc[sel_derive_mask] * SALT_PER_SODIUM).round(4)

    sodium_derive_mask = sodium.isna() & sel.notna()
    sodium.loc[sodium_derive_mask] = (sel.loc[sodium_derive_mask] / SALT_PER_SODIUM).round(4)

    # Sodium recalculé depuis le sel si incoherent.
    sodium_recalcule_mask = (
        sodium.notna() & sel.notna() & ~sodium_derive_mask & ((sel - sodium * SALT_PER_SODIUM).abs() > 1e-6)
    )
    sodium.loc[sodium_recalcule_mask] = (sel.loc[sodium_recalcule_mask] / SALT_PER_SODIUM).round(4)

    res["energy-kcal_100g"] = kcal
    res["salt_100g"] = sel
    res["sodium_100g"] = sodium

    lignes_touchees = (kcal_derivees_mask | kcal_recalculees_mask | sel_derive_mask | sodium_derive_mask | sodium_recalcule_mask).sum()

    compte_rendu = CompteRendu(
        regle="normalize_units",
        lignes_avant=lignes_avant,
        lignes_apres=len(res),
        lignes_touchees=int(lignes_touchees),
        details={
            "kcal_derivees": int(kcal_derivees_mask.sum()),
            "kcal_recalculees": int(kcal_recalculees_mask.sum()),
            "sel_derive": int(sel_derive_mask.sum()),
            "sodium_derive": int(sodium_derive_mask.sum()),
            "sodium_recalcule": int(sodium_recalcule_mask.sum()),
        },
    )

    return res, compte_rendu
    

def limit_nutriments(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Règle de bornage des nutriments :
    - Si des nutriments sont négatifs, ces derniers sont déclarés NA à la place
    - Si des nutriments sont au-dessus de 100 g/100 g -> NA (exception pour le sodium borné à 40 g/100 g).
    - Si sucres > glucides + 0,5 -> sucres = NA.
    - Si saturés > lipides + 0,5 -> saturés = NA.
    """
    res = df.copy(deep=True)

    lignes_avant = len(df)
    details: dict[str, int] = {}

    colonnes_nutriments = [
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
    lignes_touchees_mask = pd.Series(False, index=res.index)

    for col in colonnes_nutriments:
        if col not in res.columns:
            continue

        serie = pd.to_numeric(res[col], errors="coerce")
        borne_max = SODIUM_MAX if col == "sodium_100g" else NUTRIMENT_MAX

        negatifs_mask = serie < 0
        au_dessus_mask = serie > borne_max
        invalides_mask = negatifs_mask | au_dessus_mask

        serie.loc[invalides_mask] = pd.NA
        res[col] = serie

        lignes_touchees_mask |= invalides_mask
        details[f"{col}_negatifs"] = int(negatifs_mask.sum())
        details[f"{col}_au_dessus"] = int(au_dessus_mask.sum())

    # Cohérence sucres vs glucides
    sucres_mask = pd.Series(False, index=res.index)
    if "sugars_100g" in res.columns and "carbohydrates_100g" in res.columns:
        sucres = pd.to_numeric(res["sugars_100g"], errors="coerce")
        glucides = pd.to_numeric(res["carbohydrates_100g"], errors="coerce")
        sucres_mask = sucres.notna() & glucides.notna() & (sucres > glucides + COHERENCE_DELTA)
        sucres.loc[sucres_mask] = pd.NA
        res["sugars_100g"] = sucres
        lignes_touchees_mask |= sucres_mask

    # Cohérence saturés vs lipides
    satures_mask = pd.Series(False, index=res.index)
    if "saturated-fat_100g" in res.columns and "fat_100g" in res.columns:
        satures = pd.to_numeric(res["saturated-fat_100g"], errors="coerce")
        lipides = pd.to_numeric(res["fat_100g"], errors="coerce")
        satures_mask = satures.notna() & lipides.notna() & (satures > lipides + COHERENCE_DELTA)
        satures.loc[satures_mask] = pd.NA
        res["saturated-fat_100g"] = satures
        lignes_touchees_mask |= satures_mask

    details["sucres"] = int(sucres_mask.sum())
    details["satures"] = int(satures_mask.sum())

    compte_rendu = CompteRendu(
        regle="limit_nutriments",
        lignes_avant=lignes_avant,
        lignes_apres=len(res),
        lignes_touchees=int(lignes_touchees_mask.sum()),
        details=details,
    )

    return res, compte_rendu
    
def fix_energy(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Règle de correction de l'énergie :
    - Recalcule les kcal nulles avec les macronutriments en utilisant la formule de recalcul 4/4/9
    - Pareil pour les kcal supérieurs à 900, si imposssible : NA
    - Si des valeur kcal sont incohérentes (> 50% d'écart vs calcul 4/4/9 ou si calcul >= 50) : on recalcule
    - Aucune correction sur le rayon Alcoholic beverages
    - kJ réalignés sur les kcal finales
    """
    res = df.copy(deep=True)

    lignes_avant = len(df)

    kcal = pd.to_numeric(res["energy-kcal_100g"], errors="coerce")
    kj = pd.to_numeric(res["energy_100g"], errors="coerce")
    carbs = pd.to_numeric(res["carbohydrates_100g"], errors="coerce")
    proteins = pd.to_numeric(res["proteins_100g"], errors="coerce")
    fat = pd.to_numeric(res["fat_100g"], errors="coerce")

    # Calcul 4/4/9 (possible si au moins un macronutriment est présent)
    calc = carbs.fillna(0) * 4 + proteins.fillna(0) * 4 + fat.fillna(0) * 9
    has_macros = carbs.notna() | proteins.notna() | fat.notna()

    # Exception rayon alcool.
    if "rayon" in res.columns:
        alcool_mask = res["rayon"].astype("string").eq("Alcoholic beverages")
    else:
        alcool_mask = pd.Series(False, index=res.index)
    eligible_mask = ~alcool_mask

    # Si kcal nulles -> recalcul si macronutriments disponibles
    nulles_recalculees_mask = eligible_mask & kcal.isna() & has_macros
    kcal.loc[nulles_recalculees_mask] = calc.loc[nulles_recalculees_mask].round(1)

    # Si kcal > 900 -> recalcul si macronurtiments disponibles, sinon NA
    over_900_mask = eligible_mask & kcal.notna() & (kcal > KCAL_MAX)
    over_900_recalculees_mask = over_900_mask & has_macros
    over_900_invalidees_mask = over_900_mask & ~has_macros
    kcal.loc[over_900_recalculees_mask] = calc.loc[over_900_recalculees_mask].round(1)
    kcal.loc[over_900_invalidees_mask] = pd.NA

    # Si kcal incoherentes > 50% du calcul 4/4/9 si calcul >= 50.
    calc_eligible_mask = has_macros & (calc >= 50)
    ecart_relatif = (kcal - calc).abs() / calc.where(calc != 0)
    incoherentes_recalculees_mask = (
        eligible_mask
        & kcal.notna()
        & calc_eligible_mask
        & (ecart_relatif > 0.5)
        & ~over_900_mask
    )
    kcal.loc[incoherentes_recalculees_mask] = calc.loc[incoherentes_recalculees_mask].round(1)

    res["energy-kcal_100g"] = kcal

    # Réalignement des kJ depuis kcal finales.
    kj.loc[kcal.notna()] = (kcal.loc[kcal.notna()] * KJ_PER_KCAL).round(1)
    res["energy_100g"] = kj

    lignes_touchees_mask = (
        nulles_recalculees_mask
        | over_900_recalculees_mask
        | over_900_invalidees_mask
        | incoherentes_recalculees_mask
    )

    compte_rendu = CompteRendu(
        regle="fix_energy",
        lignes_avant=lignes_avant,
        lignes_apres=len(res),
        lignes_touchees=int(lignes_touchees_mask.sum()),
        details={
            "nulles_recalculees": int(nulles_recalculees_mask.sum()),
            ">900_recalculees": int(over_900_recalculees_mask.sum()),
            ">900_invalidees": int(over_900_invalidees_mask.sum()),
            "incoherentes_recalculees": int(incoherentes_recalculees_mask.sum()),
        },
    )

    return res, compte_rendu