import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.cleaning import (
	KEY_NUTRIENTS,
	deduplicate_codes,
	handle_empty_categories,
	missing_values_strategy,
	set_column_types,
)


def _product(**overrides):
	product = {
		"code": "1111111111111",
		"product_name": "Pates nature",
		"quantity": "500 g",
		"nutrition_data_per": "100g",
		"brands_tags": ["fr:marque-a"],
		"categories_tags": ["fr:epicerie", "fr:pates"],
		"labels_tags": ["fr:bio"],
		"origins_tags": ["fr:france"],
		"food_groups_tags": ["en:cereals-and-potatoes"],
		"ingredients_tags": ["en:durum-wheat-semolina"],
		"additives_tags": ["en:none"],
		"energy_100g": 420.0,
		"energy-kcal_100g": 100.4,
		"fat_100g": 4.0,
		"saturated-fat_100g": 1.2,
		"carbohydrates_100g": 20.0,
		"sugars_100g": 3.0,
		"fiber_100g": 2.0,
		"proteins_100g": 6.0,
		"salt_100g": 0.8,
		"sodium_100g": 0.32,
		"fruits-vegetables-legumes_100g": 0.0,
		"nutriscore_grade": "b",
		"nutriscore_score": 2,
		"nova_group": 2,
		"environmental_score_grade": "b",
		"environmental_score_score": 35,
		"completeness": 0.9,
		"last_modified_t": 100,
		"images": ["front_fr.1.400"],
		"rayon": "Epicerie",
	}
	product.update(overrides)
	return product


@pytest.fixture
def tordu():
	rows = [
		_product(),
		_product(
			code=" 2222222222222 ",
			product_name="BISCUITS CHOCO",
			sugars_100g=74000.0,
			nutriscore_score=4,
			nova_group=2,
			rayon="Biscuits",
		),
		_product(
			code="3333333333333",
			product_name="Doublon ancien",
			completeness=0.4,
			last_modified_t=200,
			brands_tags=["fr:marque-b"],
		),
		_product(
			code="3333333333333 ",
			product_name="Doublon retenu",
			completeness=0.95,
			last_modified_t=150,
			brands_tags=["fr:marque-c"],
		),
		_product(
			code="   ",
			product_name="Produit sans code",
			salt_100g=5000.0,
			rayon="Conserves",
			**{"energy-kcal_100g": 24000.0},
		),
		_product(
			code="4444444444444",
			product_name="Sans categorie ni rayon",
			categories_tags=None,
			food_groups_tags=None,
			rayon=None,
		),
		_product(
			code="5555555555555",
			product_name="Categorie vide mais groupe connu",
			categories_tags=None,
			food_groups_tags=["en:beverages"],
			rayon="Boissons",
		),
		_product(
			code="6666666666666",
			product_name="Rayon manquant",
			fat_100g=None,
			rayon=None,
		),
		_product(
			code="7777777777777",
			product_name="Sans nutriment",
			energy_100g=None,
			fat_100g=None,
			carbohydrates_100g=None,
			sugars_100g=None,
			fiber_100g=None,
			proteins_100g=None,
			salt_100g=None,
			sodium_100g=None,
			rayon="Epicerie",
			**{
				"energy-kcal_100g": None,
				"saturated-fat_100g": None,
				"fruits-vegetables-legumes_100g": None,
			},
		),
		_product(
			code="8888888888888",
			product_name="Groupe alimentaire manquant",
			food_groups_tags=None,
			rayon="Ultra-frais",
		),
	]
	return pd.DataFrame(rows)


def _idempotence_payload(rule_name, tordu):
	if rule_name == "set_column_types":
		df = tordu.iloc[[0, 1, 7]].copy(deep=True)
		df.loc[df.index[1], "nova_group"] = pd.NA
		return set_column_types, df, {}

	if rule_name == "deduplicate_codes":
		df = tordu.iloc[[0, 2, 3, 4]].copy(deep=True)
		return deduplicate_codes, df, {}

	if rule_name == "handle_empty_categories":
		df = tordu.iloc[[0, 5]].copy(deep=True)
		return handle_empty_categories, df, {}

	if rule_name == "missing_values_strategy":
		df = tordu.iloc[[0, 1, 2]].copy(deep=True)
		df.loc[df.index[0], "brands_tags"] = None
		df.loc[df.index[1], "nova_group"] = pd.NA
		df.loc[df.index[2], "fat_100g"] = pd.NA
		strategy = {
			"brands_tags": "constant:unknown",
			"nova_group": "mode",
			"fat_100g": "foodgroup_median",
			"quantity": "drop_column",
		}
		return missing_values_strategy, df, {"strategy": strategy}

	raise AssertionError(f"Règle inconnue: {rule_name}")


def _purity_payload(rule_name, tordu):
	if rule_name == "set_column_types":
		df = tordu.iloc[[0, 1, 7]].copy(deep=True)
		df.loc[df.index[2], "nutriscore_score"] = pd.NA
		return set_column_types, df, {}

	if rule_name == "deduplicate_codes":
		return deduplicate_codes, tordu.iloc[[0, 2, 3, 4]].copy(deep=True), {}

	if rule_name == "handle_empty_categories":
		return handle_empty_categories, tordu.iloc[[0, 5, 6, 9]].copy(deep=True), {}

	if rule_name == "missing_values_strategy":
		df = tordu.iloc[[0, 1, 8]].copy(deep=True)
		df.loc[df.index[0], "brands_tags"] = None
		df.loc[df.index[1], "energy-kcal_100g"] = pd.NA
		strategy = {
			"brands_tags": "constant:unknown",
			"energy-kcal_100g": "flag",
			"quantity": "drop_column",
		}
		return missing_values_strategy, df, {"strategy": strategy}

	raise AssertionError(f"Règle inconnue: {rule_name}")


def test_set_column_types_nominal_and_report(tordu):
	source = tordu.iloc[[0, 1, 7]].copy(deep=True)
	source.loc[source.index[1], "nova_group"] = pd.NA
	source.loc[source.index[2], "nutriscore_score"] = pd.NA

	result, report = set_column_types(source)

	assert str(result["code"].dtype) == "string"
	assert str(result["nutriscore_score"].dtype) == "Int64"
	assert str(result["nova_group"].dtype) == "Int64"
	for column in KEY_NUTRIENTS:
		assert str(result[column].dtype) == "float64"

	assert result["code"].tolist() == source["code"].astype("string").tolist()
	assert report.rule == "typer_colonnes"
	assert report.lines_before == 3
	assert report.lines_after == 3
	assert report.affected_lines == 0
	assert report.details == {}


def test_set_column_types_twisted_keeps_values_and_nullables(tordu):
	source = tordu.iloc[[1, 7]].copy(deep=True)
	source.loc[source.index[1], "nova_group"] = pd.NA

	result, _ = set_column_types(source)

	assert result.loc[source.index[0], "code"] == " 2222222222222 "
	assert result.loc[source.index[0], "product_name"] == "BISCUITS CHOCO"
	assert pd.isna(result.loc[source.index[1], "nova_group"])
	assert pd.isna(result.loc[source.index[1], "fat_100g"])


def test_deduplicate_codes_nominal_keeps_most_complete_and_counts_report(tordu):
	source = tordu.iloc[[0, 2, 3, 4]].copy(deep=True)

	result, report = deduplicate_codes(source)

	assert set(result["code"].tolist()) == {"1111111111111", "3333333333333"}
	kept_duplicate = result.loc[result["code"] == "3333333333333"].iloc[0]
	assert kept_duplicate["product_name"] == "Doublon retenu"
	assert kept_duplicate["completeness"] == pytest.approx(0.95)

	assert report.rule == "Dédupliquer les codes"
	assert report.lines_before == 4
	assert report.lines_after == 2
	assert report.affected_lines == 2
	assert report.details == {"sans_code": 1, "doublons_supprimes": 1}


def test_deduplicate_codes_twisted_strips_spaces_without_touching_neighbor_code(tordu):
	source = tordu.iloc[[0, 1]].copy(deep=True)

	result, report = deduplicate_codes(source)

	assert result["code"].tolist() == ["1111111111111", "2222222222222"]
	assert result.loc[result["code"] == "2222222222222", "product_name"].iloc[0] == "BISCUITS CHOCO"
	assert report.affected_lines == 0


def test_handle_empty_categories_nominal_derives_columns_and_drops_unclassifiable(tordu):
	source = tordu.iloc[[0, 5, 6]].copy(deep=True)

	result, report = handle_empty_categories(source)

	assert "4444444444444" not in result["code"].tolist()
	assert result.loc[result["code"] == "1111111111111", "main_category"].iloc[0] == "fr:pates"
	kept_empty_category = result.loc[result["code"] == "5555555555555"].iloc[0]
	assert bool(kept_empty_category["category_empty"])
	assert kept_empty_category["food_group"] == "en:beverages"

	assert report.rule == "traiter_categories_vides"
	assert report.lines_before == 3
	assert report.lines_after == 2
	assert report.affected_lines == 2
	assert report.details == {
		"categorie_vide": 2,
		"food_group_derive_de_vide": 1,
		"food_group_unknown_total": 1,
		"inclassables_supprimes": 1,
	}


def test_handle_empty_categories_twisted_keeps_product_with_unknown_food_group_if_category_exists(tordu):
	source = tordu.iloc[[0, 5, 9]].copy(deep=True)

	result, _ = handle_empty_categories(source)

	assert "4444444444444" not in result["code"].tolist()
	kept_unknown_group = result.loc[result["code"] == "8888888888888"].iloc[0]
	assert kept_unknown_group["main_category"] == "fr:pates"
	assert kept_unknown_group["food_group"] == "unknown"
	assert not bool(kept_unknown_group["category_empty"])


def test_missing_values_strategy_nominal_applies_flag_constant_mode_and_drop_column(tordu):
	source = tordu.iloc[[0, 1, 2]].copy(deep=True)
	source.loc[source.index[0], "brands_tags"] = None
	source.loc[source.index[1], "energy-kcal_100g"] = pd.NA
	source.loc[source.index[2], "nova_group"] = pd.NA
	source.loc[source.index[0], "nova_group"] = 2
	source.loc[source.index[1], "nova_group"] = 2

	result, report = missing_values_strategy(
		source,
		strategy={
			"brands_tags": "constant:unknown",
			"energy-kcal_100g": "flag",
			"nova_group": "mode",
			"quantity": "drop_column",
		},
	)

	assert "quantity" not in result.columns
	assert result.loc[source.index[0], "brands_tags"] == "unknown"
	assert pd.isna(result.loc[source.index[1], "energy-kcal_100g"])
	assert result.loc[source.index[1], "energy-kcal_100g_manquant"]
	assert not result.loc[source.index[0], "energy-kcal_100g_manquant"]
	assert result.loc[source.index[2], "nova_group"] == 2

	assert report.rule == "strategie_manquants"
	assert report.lines_before == 3
	assert report.lines_after == 3
	assert report.affected_lines == 3
	assert report.details["brands_tags:constant"] == 1
	assert report.details["energy-kcal_100g:flag"] == 1
	assert report.details["nova_group:mode"] == 1
	assert report.details["quantity:drop_column"] == 1
	assert report.details["dropped_columns"] == ["quantity"]
	assert report.details["rows_dropped_no_nutrient"] == 0


def test_missing_values_strategy_twisted_drops_only_row_without_nutrients_and_imputes_by_rayon(tordu):
	source = tordu.iloc[[0, 1, 7, 8]].copy(deep=True)
	source.loc[source.index[0], "fat_100g"] = pd.NA
	source.loc[source.index[0], "rayon"] = "Epicerie"
	source.loc[source.index[1], "fat_100g"] = 7.0
	source.loc[source.index[1], "rayon"] = "Epicerie"
	source.loc[source.index[2], "fat_100g"] = pd.NA
	source.loc[source.index[3], "rayon"] = "Sans groupe"
	for column in KEY_NUTRIENTS:
		if column != "fiber_100g":
			source.loc[source.index[2], column] = pd.NA
	source.loc[source.index[2], "fiber_100g"] = 0.0

	result, report = missing_values_strategy(
		source,
		strategy={"fat_100g": "foodgroup_median"},
	)

	assert "7777777777777" not in result["code"].tolist()
	assert result.loc[source.index[0], "fat_100g"] == pytest.approx(7.0)
	assert pd.isna(result.loc[source.index[2], "fat_100g"])
	assert "6666666666666" in result["code"].tolist()

	assert report.lines_before == 4
	assert report.lines_after == 3
	assert report.affected_lines == 3
	assert report.details["fat_100g:foodgroup_median"] == 3
	assert report.details["rows_dropped_no_nutrient"] == 1


@pytest.mark.parametrize(
	"rule_name",
	[
		"set_column_types",
		"deduplicate_codes",
		"handle_empty_categories",
		"missing_values_strategy",
	],
)
def test_rules_are_pure(rule_name, tordu):
	rule, source, kwargs = _purity_payload(rule_name, tordu)
	snapshot = source.copy(deep=True)

	rule(source, **kwargs)

	assert_frame_equal(source, snapshot)


@pytest.mark.parametrize(
	"rule_name",
	[
		"set_column_types",
		"deduplicate_codes",
		"handle_empty_categories",
		"missing_values_strategy",
	],
)
def test_rules_are_idempotent(rule_name, tordu):
	rule, source, kwargs = _idempotence_payload(rule_name, tordu)

	first_result, _ = rule(source, **kwargs)
	second_result, second_report = rule(first_result, **kwargs)

	assert_frame_equal(first_result, second_result)
	assert second_report.affected_lines == 0
  

"""Tests pour les règles de nettoyage des nutriments : normalize_units,
limit_nutriments, fix_energy.

Chaque règle est testée selon le contrat du TP 9 (étape 4) :
nominal, cas tordu (valeurs aux bornes exactes), pureté, idempotence.
"""

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
