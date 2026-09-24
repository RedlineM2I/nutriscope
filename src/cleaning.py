from dataclasses import dataclass, field

import pandas as pd

KCAL_MAX = 900.0
SALT_PER_SODIUM = 2.5
KJ_PER_KCAL = 4.184

RATIO_KCAL_LOW = 3.9
RATIO_KCAL_HIGH = 4.5

@dataclass
class CompteRendu:
    regle: str
    lignes_avant: int
    lignes_apres: int
    lignes_touchees: int
    details: dict[str, int] = field(default_factory=dict)
    
def normalize_units(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """Règle de normalisation des unités:
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

    # 3) Derivations sel <-> sodium dans les deux sens.
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
    """"""
    
def fix_energy(df: pd.DataFrame) -> tuple[pd.DataFrame, CompteRendu]:
    """"""
    res = df.copy()
    calc = 4 * res["carbohydrates_100g"] + 4 * res["proteins_100g"] + 9 * res["fat_100g"]
    depuis_macros = kcal.isna() & calc.notna() & (calc <= KCAL_MAX)
    kcal = kcal.mask(depuis_macros, calc.round(1))
    res["energy-kcal_100g"] = kcal
    
    