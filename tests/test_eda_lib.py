import numpy as np
import pandas as pd

from src.eda_lib import (
    clean_minimal_tp10,
    comparer_deux_groupes,
    completude_par_groupe,
    correlations_nutriscore,
    extremes_restants,
    incoherences_metier,
    paires_redondantes,
    profil_par_rayon,
    resume_univarie,
    zscore_robuste,
)


def test_resume_univarie_known_values():
    s = pd.Series([1, 2, 3, np.nan])
    out = resume_univarie(s)
    assert out["n"] == 4
    assert out["n_missing"] == 1
    assert np.isclose(out["mean"], 2.0)
    assert np.isclose(out["median"], 2.0)


def test_resume_univarie_all_nan():
    s = pd.Series([np.nan, np.nan])
    out = resume_univarie(s)
    assert out["n_valid"] == 0
    assert np.isnan(out["mean"])


def test_profil_par_rayon_drops_small_groups():
    df = pd.DataFrame(
        {
            "pnns_groups_1": ["A", "A", "A", "B"],
            "sugars_100g": [1, 2, 3, 10],
            "salt_100g": [0.1, 0.2, 0.3, 0.4],
        }
    )
    prof, dropped = profil_par_rayon(df, ["sugars_100g", "salt_100g"], min_n=2)
    assert dropped == ["B"]
    assert set(prof["pnns_groups_1"].unique()) == {"A"}


def test_completude_par_groupe_rates():
    df = pd.DataFrame(
        {
            "pnns_groups_1": ["A", "A", "A", "A"],
            "sugars_100g": [1, np.nan, 2, 3],
            "salt_100g": [0.1, 0.2, np.nan, 0.4],
            "nutriscore_score": [1, 2, np.nan, 4],
        }
    )
    out = completude_par_groupe(df, "pnns_groups_1", ["sugars_100g", "salt_100g"], min_n=1)
    row = out.iloc[0]
    assert np.isclose(row["presence_sugars_100g"], 0.75)
    assert np.isclose(row["presence_salt_100g"], 0.75)
    assert np.isclose(row["taux_fiches_completes"], 0.5)


def test_incoherences_metier_flags():
    df = pd.DataFrame(
        {
            "sugars_100g": [20],
            "carbohydrates_100g": [10],
            "saturated-fat_100g": [8],
            "fat_100g": [5],
            "salt_100g": [5.0],
            "sodium_100g": [0.1],
            "energy-kcal_100g": [0],
            "proteins_100g": [10],
            "fiber_100g": [5],
        }
    )
    out = incoherences_metier(df)
    assert bool(out.loc[0, "sucres_sup_glucides"])
    assert bool(out.loc[0, "satures_sup_lipides"])
    assert bool(out.loc[0, "sel_diff_sodium"])
    assert bool(out.loc[0, "energie_nulle_avec_macros"])


def test_correlations_nutriscore_perfect_relations():
    df = pd.DataFrame(
        {
            "nutriscore_score": [1, 2, 3, 4, 5],
            "x_lin": [2, 4, 6, 8, 10],
            "x_mono": [10, 20, 30, 40, 50],
        }
    )
    out = correlations_nutriscore(df, ["x_lin", "x_mono"], min_n=3)
    assert np.allclose(out["pearson"].abs().to_numpy(), 1.0)
    assert np.allclose(out["spearman"].abs().to_numpy(), 1.0)


def test_paires_redondantes_detects_pair():
    mat = pd.DataFrame(
        [[1.0, 0.95, 0.2], [0.95, 1.0, 0.1], [0.2, 0.1, 1.0]],
        columns=["sel", "sodium", "sucres"],
        index=["sel", "sodium", "sucres"],
    )
    out = paires_redondantes(mat, seuil=0.8)
    assert len(out) == 1
    assert {out.loc[0, "var_a"], out.loc[0, "var_b"]} == {"sel", "sodium"}


def test_zscore_robuste_constant_series():
    s = pd.Series([5.0, 5.0, 5.0])
    z = zscore_robuste(s)
    assert (z == 0).all()


def test_extremes_restants_detect_intruder():
    rows = [{"pnns_groups_1": "A", "code": str(i), "product_name": "x", "sugars_100g": 10} for i in range(20)]
    rows.append({"pnns_groups_1": "A", "code": "999", "product_name": "out", "sugars_100g": 90})
    df = pd.DataFrame(rows)
    out = extremes_restants(df, ["sugars_100g"], seuil=3.5)
    assert "999" in set(out["code"])


def test_extremes_restants_empty_result_is_well_formed():
    df = pd.DataFrame(
        {
            "pnns_groups_1": ["A", "A", "A"],
            "code": ["1", "2", "3"],
            "product_name": ["a", "b", "c"],
            "sugars_100g": [10, 10, 10],
        }
    )
    out = extremes_restants(df, ["sugars_100g"], seuil=3.5)
    assert list(out.columns) == ["pnns_groups_1", "code", "product_name", "variable", "value", "z_robuste"]
    assert out.empty


def test_clean_minimal_tp10_removes_invalid_ranges():
    df = pd.DataFrame(
        {
            "code": ["a", "b", "c"],
            "sugars_100g": [20, 120, 5],
            "energy-kcal_100g": [100, 200, 950],
        }
    )
    out = clean_minimal_tp10(df)
    assert list(out["code"]) == ["a"]


def test_comparer_deux_groupes_returns_effect_and_pvalue():
    a = pd.Series([1, 2, 3, 4, 5])
    b = pd.Series([10, 11, 12, 13, 14])
    out = comparer_deux_groupes(a, b)
    assert out.n_a == 5
    assert out.n_b == 5
    assert out.delta_median < 0
    assert out.p_value < 0.05