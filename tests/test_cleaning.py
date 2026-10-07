"""Tests pour les règles de nettoyage des nutriments : normalize_units,
limit_nutriments, fix_energy.

Chaque règle est testée selon le contrat du TP 9 (étape 4) :
nominal, cas tordu (valeurs aux bornes exactes), pureté, idempotence.
"""

import pandas as pd
import pytest
import numpy as np

from src.cleaning import normalize_units, limit_nutriments, fix_energy


def make_df(**columns) -> pd.DataFrame:
    """Construit un DataFrame d'une seule ligne à partir de colonnes nommées.
    Évite de répéter le même squelette dans chaque test.
    """
    return pd.DataFrame({k: [v] for k, v in columns.items()})


# ============================================================
# normalize_units
# ============================================================

class TestNormalizeUnitsNominal:
    """Un test par sous-règle de normalize_units, chacune isolée des autres
    (les colonnes non concernées sont mises à NA pour ne déclencher qu'une
    seule sous-règle à la fois).
    """

    def test_derives_kcal_from_kj(self):
        """kcal manquante + kJ présent -> kcal dérivée par division par KJ_PER_KCAL."""
        df = make_df(**{
            "energy_100g": 418.4, "energy-kcal_100g": np.nan,
            "salt_100g": np.nan, "sodium_100g": np.nan,
        })
        res, report = normalize_units(df)

        assert res["energy-kcal_100g"].iloc[0] == pytest.approx(100.0, abs=0.1)
        assert report.details["kcal_derivees"] == 1
        assert report.affected_lines == 1

    def test_recalculates_kcal_if_ratio_out_of_bounds(self):
        """kJ et kcal présents mais ratio kJ/kcal hors de [3.9 ; 4.5] -> kcal recalculée depuis kJ."""
        # kj=1000, kcal=100 -> ratio = 10, largement hors borne
        df = make_df(**{
            "energy_100g": 1000.0, "energy-kcal_100g": 100.0,
            "salt_100g": np.nan, "sodium_100g": np.nan,
        })
        res, report = normalize_units(df)

        assert res["energy-kcal_100g"].iloc[0] == pytest.approx(239.0, abs=0.1)
        assert report.details["kcal_recalculees"] == 1

    def test_derives_salt_from_sodium(self):
        """sel manquant + sodium présent -> sel dérivé (sodium x SALT_PER_SODIUM)."""
        df = make_df(**{
            "energy_100g": np.nan, "energy-kcal_100g": np.nan,
            "salt_100g": np.nan, "sodium_100g": 1.0,
        })
        res, report = normalize_units(df)
        assert res["salt_100g"].iloc[0] == pytest.approx(2.5)
        assert report.details["sel_derive"] == 1

    def test_derives_sodium_from_salt(self):
        """sodium manquant + sel présent -> sodium dérivé (sel / SALT_PER_SODIUM)."""
        df = make_df(**{
            "energy_100g": np.nan, "energy-kcal_100g": np.nan,
            "salt_100g": 5.0, "sodium_100g": np.nan,
        })
        res, report = normalize_units(df)

        assert res["sodium_100g"].iloc[0] == pytest.approx(2.0)
        assert report.details["sodium_derive"] == 1

    def test_recalculates_sodium_if_inconsistent(self):
        """sel et sodium présents mais incohérents entre eux -> sodium recalculé depuis le sel."""
        # sel=5 -> sodium cohérent attendu = 2.0, mais sodium déclaré = 1.0
        df = make_df(**{
            "energy_100g": np.nan, "energy-kcal_100g": np.nan,
            "salt_100g": 5.0, "sodium_100g": 1.0,
        })
        res, report = normalize_units(df)

        assert res["sodium_100g"].iloc[0] == pytest.approx(2.0)
        assert report.details["sodium_recalcule"] == 1


class TestNormalizeUnitsEdgeCases:
    """Valeurs volontairement placées sur les bornes exactes de normalize_units,
    pour vérifier que les comparaisons strictes (<, >) sont bien respectées.
    """

    def test_ratio_at_lower_bound_is_not_recalculated(self):
        """Ratio kJ/kcal exactement à 3.9 (borne basse incluse) -> pas de recalcul."""
        # kj=390, kcal=100 -> ratio exactement 3.9
        df = make_df(**{
            "energy_100g": 390.0, "energy-kcal_100g": 100.0,
            "salt_100g": np.nan, "sodium_100g": np.nan,
        })
        res, report = normalize_units(df)

        assert res["energy-kcal_100g"].iloc[0] == 100.0  # inchangé
        assert report.details["kcal_recalculees"] == 0

    def test_kcal_at_zero_is_never_recalculated(self):
        """kcal déclarée à 0 -> exclue du recalcul pour éviter une division par zéro."""
        df = make_df(**{
            "energy_100g": 100.0, "energy-kcal_100g": 0.0,
            "salt_100g": np.nan, "sodium_100g": np.nan,
        })
        res, report = normalize_units(df)

        assert res["energy-kcal_100g"].iloc[0] == 0.0
        assert report.details["kcal_recalculees"] == 0


# ============================================================
# limit_nutriments
# ============================================================

def make_nutrient_row(**overrides) -> dict:
    """Ligne de base avec tous les nutriments à NA, pour n'activer qu'une
    seule sous-règle à la fois en ne passant que les colonnes concernées
    dans `overrides`.
    """
    base = {
        "sugars_100g": np.nan, "carbohydrates_100g": np.nan, "fat_100g": np.nan,
        "saturated-fat_100g": np.nan, "salt_100g": np.nan, "sodium_100g": np.nan,
        "proteins_100g": np.nan, "fiber_100g": np.nan,
    }
    base.update(overrides)
    return base


class TestLimitNutrimentsNominal:
    """Un test par sous-règle de limit_nutriments."""

    def test_negative_becomes_na(self):
        """Valeur négative sur un nutriment -> devient NA."""
        df = make_df(**make_nutrient_row(sugars_100g=-5.0))
        res, report = limit_nutriments(df)

        assert pd.isna(res["sugars_100g"].iloc[0])
        assert report.details["sugars_100g_negatifs"] == 1

    def test_above_100_becomes_na(self):
        """Valeur au-dessus de 100 g/100 g -> devient NA."""
        df = make_df(**make_nutrient_row(sugars_100g=150.0, carbohydrates_100g=200.0))
        res, report = limit_nutriments(df)

        assert pd.isna(res["sugars_100g"].iloc[0])
        assert report.details["sugars_100g_au_dessus"] == 1

    def test_sodium_bounded_at_40_not_100(self):
        """Le sodium a une borne spécifique à 40 g/100 g, pas la borne générale à 100."""
        df = make_df(**make_nutrient_row(sodium_100g=50.0))
        res, report = limit_nutriments(df)

        assert pd.isna(res["sodium_100g"].iloc[0])
        assert report.details["sodium_100g_au_dessus"] == 1

    def test_sugars_inconsistent_with_carbs(self):
        """Sucres > glucides + tolérance -> sucres devient NA."""
        df = make_df(**make_nutrient_row(sugars_100g=50.0, carbohydrates_100g=40.0))
        res, report = limit_nutriments(df)

        assert pd.isna(res["sugars_100g"].iloc[0])
        assert report.details["sucres"] == 1


class TestLimitNutrimentsEdgeCases:
    """Valeurs placées exactement sur les bornes, pour vérifier les comparaisons strictes."""

    def test_exactly_100_is_not_touched(self):
        """100 g/100 g pile -> valeur plausible, pas de modification."""
        df = make_df(**make_nutrient_row(sugars_100g=100.0, carbohydrates_100g=100.0))
        res, report = limit_nutriments(df)

        assert res["sugars_100g"].iloc[0] == 100.0
        assert report.details["sugars_100g_au_dessus"] == 0

    def test_sodium_exactly_40_is_not_touched(self):
        """40 g/100 g pile pour le sodium -> borne spécifique incluse."""
        df = make_df(**make_nutrient_row(sodium_100g=40.0))
        res, report = limit_nutriments(df)

        assert res["sodium_100g"].iloc[0] == 40.0

    def test_sugars_at_exact_tolerance_is_not_touched(self):
        """sucres = glucides + tolérance pile -> comparaison stricte, donc pas flagué."""
        # sugars = carbs + 0.5 exactement -> condition stricte ">" donc pas flagué
        df = make_df(**make_nutrient_row(sugars_100g=40.5, carbohydrates_100g=40.0))
        res, report = limit_nutriments(df)

        assert res["sugars_100g"].iloc[0] == 40.5
        assert report.details["sucres"] == 0


# ============================================================
# fix_energy
# ============================================================

def make_energy_row(**overrides) -> dict:
    """Ligne de base pour fix_energy : macronutriments à NA, rayon neutre,
    pour n'activer qu'une seule sous-règle à la fois.
    """
    base = {
        "energy-kcal_100g": np.nan, "energy_100g": np.nan,
        "carbohydrates_100g": np.nan, "proteins_100g": np.nan, "fat_100g": np.nan,
        "rayon": "Snacks",
    }
    base.update(overrides)
    return base


class TestFixEnergyNominal:
    """Un test par sous-règle de fix_energy."""

    def test_recomputes_missing_kcal_from_macros(self):
        """kcal manquante avec macronutriments disponibles -> recalcul via la formule 4/4/9."""
        df = make_df(**make_energy_row(
            carbohydrates_100g=10.0, proteins_100g=5.0, fat_100g=2.0,
        ))
        res, report = fix_energy(df)

        # calc = 10*4 + 5*4 + 2*9 = 78
        assert res["energy-kcal_100g"].iloc[0] == pytest.approx(78.0)
        assert report.details["nulles_recalculees"] == 1

    def test_above_900_recomputed_if_macros(self):
        """kcal > 900 avec macronutriments disponibles -> recalcul via 4/4/9."""
        df = make_df(**make_energy_row(
            **{"energy-kcal_100g": 1200.0},
            carbohydrates_100g=10.0, proteins_100g=5.0, fat_100g=2.0,
        ))
        res, report = fix_energy(df)

        assert res["energy-kcal_100g"].iloc[0] == pytest.approx(78.0)
        assert report.details[">900_recalculees"] == 1

    def test_above_900_without_macros_becomes_na(self):
        """kcal > 900 sans aucun macronutriment -> impossible à recalculer, devient NA."""
        df = make_df(**make_energy_row(**{"energy-kcal_100g": 1200.0}))
        res, report = fix_energy(df)

        assert pd.isna(res["energy-kcal_100g"].iloc[0])
        assert report.details[">900_invalidees"] == 1

    def test_alcohol_exception_skips_all_subrules(self):
        """Rayon 'Alcoholic beverages' -> aucune sous-règle ne s'applique, même avec kcal > 900."""
        df = make_df(**make_energy_row(
            **{"energy-kcal_100g": 1200.0, "rayon": "Alcoholic beverages"},
        ))
        res, report = fix_energy(df)

        assert res["energy-kcal_100g"].iloc[0] == 1200.0  # inchangé malgré >900
        assert report.affected_lines == 0

    def test_realigns_kj_on_final_kcal(self):
        """Après toute correction de kcal, les kJ sont recalculés en cohérence (kcal x KJ_PER_KCAL)."""
        df = make_df(**make_energy_row(
            carbohydrates_100g=10.0, proteins_100g=0.0, fat_100g=0.0,
        ))
        res, _ = fix_energy(df)

        # calc = 40 kcal -> kJ attendu = 40 * 4.184
        assert res["energy_100g"].iloc[0] == pytest.approx(40 * 4.184, abs=0.1)


class TestFixEnergyEdgeCases:
    """Valeurs placées sur les bornes exactes de fix_energy (900 kcal, calc = 50,
    écart relatif = 50 %), pour vérifier que les comparaisons strictes sont respectées.
    """

    def test_exactly_900_is_not_touched(self):
        """900 kcal pile -> valeur plausible, inégalité stricte donc pas de correction."""
        df = make_df(**make_energy_row(**{"energy-kcal_100g": 900.0}))
        res, report = fix_energy(df)

        assert res["energy-kcal_100g"].iloc[0] == 900.0
        assert report.affected_lines == 0

    def test_calc_below_50_is_never_corrected_even_if_inconsistent(self):
        """Calcul 4/4/9 < 50 -> ligne inéligible à la correction d'incohérence,
        même si la kcal déclarée est totalement absurde.
        """
        # calc = 10*4 = 40 (< 50) -> inéligible, malgré une kcal déclarée absurde
        df = make_df(**make_energy_row(
            **{"energy-kcal_100g": 500.0},
            carbohydrates_100g=10.0, proteins_100g=0.0, fat_100g=0.0,
        ))
        res, report = fix_energy(df)

        assert res["energy-kcal_100g"].iloc[0] == 500.0
        assert report.details["incoherentes_recalculees"] == 0

    def test_relative_gap_exactly_50_percent_is_not_corrected(self):
        """Écart relatif entre kcal déclarée et calcul 4/4/9 exactement à 50 % -> pas de correction (borne stricte)."""
        # calc = 100 (>= 50, éligible), kcal déclarée = 150 -> écart relatif = 0.5 pile
        df = make_df(**make_energy_row(
            **{"energy-kcal_100g": 150.0},
            carbohydrates_100g=25.0, proteins_100g=0.0, fat_100g=0.0,
        ))
        res, report = fix_energy(df)

        assert res["energy-kcal_100g"].iloc[0] == 150.0
        assert report.details["incoherentes_recalculees"] == 0


# ============================================================
# Pureté : aucune des règles ne doit modifier son DataFrame d'entrée
# ============================================================

@pytest.mark.parametrize("cleaning_function, row", [
    (normalize_units, {
        "energy_100g": 418.4, "energy-kcal_100g": np.nan,
        "salt_100g": np.nan, "sodium_100g": np.nan,
    }),
    (limit_nutriments, make_nutrient_row(sugars_100g=-5.0)),
    (fix_energy, make_energy_row(
        carbohydrates_100g=10.0, proteins_100g=5.0, fat_100g=2.0,
    )),
])
def test_purity_does_not_modify_input(cleaning_function, row):
    """Chaque règle reçoit une copie et ne doit jamais muter le DataFrame
    passé en entrée (contrat du TP 9, étape 1).
    """
    df = make_df(**row)
    original_copy = df.copy(deep=True)

    cleaning_function(df)

    pd.testing.assert_frame_equal(df, original_copy)


# ============================================================
# Idempotence : rejouer une règle sur sa propre sortie ne doit plus rien changer
# ============================================================

@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Échantillon réel partagé par l'équipe, utilisé pour le test
    d'idempotence sur des données représentatives plutôt que synthétiques.
    """
    return pd.read_csv("tests/data-test/echantillon_france.csv")

RATIO_KCAL_LOW = 3.9
RATIO_KCAL_HIGH = 4.5

@pytest.mark.parametrize("cleaning_function", [normalize_units, limit_nutriments, fix_energy])
def test_idempotence_on_real_sample(cleaning_function, sample_dataframe):
    """Appliquer une règle deux fois de suite doit produire le même résultat,
    et le second passage ne doit toucher aucune ligne.
    """
    first_pass, first_report = cleaning_function(sample_dataframe)
    second_pass, second_report = cleaning_function(first_pass)

    pd.testing.assert_frame_equal(first_pass, second_pass)
    assert second_report.affected_lines == 0
