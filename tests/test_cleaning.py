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
