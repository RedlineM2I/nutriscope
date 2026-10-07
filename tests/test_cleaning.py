"""Tests des règles de nettoyage (src/cleaning.py).

Chaque règle est testée selon le contrat du TP 9 :
    - nominal     : la règle fait ce qu'elle annonce, et son Report compte juste ;
    - cas tordu   : valeurs pièges (espaces, bornes exactes, colonnes vides...) ;
    - pureté      : la règle ne modifie jamais le DataFrame qu'on lui passe ;
    - idempotence : rejouer la règle sur sa propre sortie ne change plus rien.

Organisation du fichier :
    1. Données de test (produits nommés + petites fabriques)
    2. Une classe de tests par règle
    3. Pureté et idempotence, vérifiées pour toutes les règles d'un coup
"""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.cleaning import (
    KEY_NUTRIENTS,
    deduplicate_codes,
    fix_energy,
    handle_empty_categories,
    limit_nutriments,
    missing_values_strategy,
    normalize_units,
    set_column_types,
)


# ============================================================
# 1. Données de test
# ============================================================

def make_product(**overrides) -> dict:
    """Produit complet et valide. On ne passe que les champs à modifier."""
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


# Catalogue de produits pièges, chacun nommé d'après ce qu'il teste.
PRODUCTS = {
    "nominal": make_product(),
    "biscuits": make_product(
        code=" 2222222222222 ",  # espaces autour du code
        product_name="BISCUITS CHOCO",
        sugars_100g=74000.0,  # valeur absurde
        nutriscore_score=4,
        rayon="Biscuits",
    ),
    "doublon_ancien": make_product(
        code="3333333333333",
        product_name="Doublon ancien",
        completeness=0.4,  # moins complet -> doit être écarté
        last_modified_t=200,
        brands_tags=["fr:marque-b"],
    ),
    "doublon_retenu": make_product(
        code="3333333333333 ",  # même code une fois les espaces retirés
        product_name="Doublon retenu",
        completeness=0.95,
        last_modified_t=150,
        brands_tags=["fr:marque-c"],
    ),
    "sans_code": make_product(
        code="   ",
        product_name="Produit sans code",
        salt_100g=5000.0,
        rayon="Conserves",
        **{"energy-kcal_100g": 24000.0},
    ),
    "sans_categorie_ni_groupe": make_product(
        code="4444444444444",
        product_name="Sans categorie ni rayon",
        categories_tags=None,
        food_groups_tags=None,
        rayon=None,
    ),
    "categorie_vide_groupe_connu": make_product(
        code="5555555555555",
        product_name="Categorie vide mais groupe connu",
        categories_tags=None,
        food_groups_tags=["en:beverages"],
        rayon="Boissons",
    ),
    "rayon_manquant": make_product(
        code="6666666666666",
        product_name="Rayon manquant",
        fat_100g=None,
        rayon=None,
    ),
    "sans_nutriment": make_product(
        code="7777777777777",
        product_name="Sans nutriment",
        rayon="Epicerie",
        **{column: None for column in KEY_NUTRIENTS},
        **{"energy-kcal_100g": None},
    ),
    "groupe_manquant": make_product(
        code="8888888888888",
        product_name="Groupe alimentaire manquant",
        food_groups_tags=None,
        rayon="Ultra-frais",
    ),
}


def pick(*names: str) -> pd.DataFrame:
    """DataFrame des produits demandés, indexé par leur nom.

    Exemple : pick("nominal", "biscuits").loc["biscuits", "code"]
    """
    return pd.DataFrame([PRODUCTS[name] for name in names], index=list(names))


def one_row(values: dict) -> pd.DataFrame:
    """DataFrame d'une seule ligne pour tester les nutriments.

    Tous les nutriments valent NA sauf ceux passés dans `values` :
    ainsi une seule sous-règle se déclenche à la fois.
    """
    row = {
        "energy_100g": np.nan,
        "energy-kcal_100g": np.nan,
        "carbohydrates_100g": np.nan,
        "sugars_100g": np.nan,
        "fat_100g": np.nan,
        "saturated-fat_100g": np.nan,
        "proteins_100g": np.nan,
        "fiber_100g": np.nan,
        "salt_100g": np.nan,
        "sodium_100g": np.nan,
        "rayon": "Snacks",
    }
    row.update(values)
    return pd.DataFrame([row])


# ============================================================
# 2. Tests règle par règle
# ============================================================

class TestSetColumnTypes:

    def test_nominal_sets_dtypes_without_changing_values(self):
        source = pick("nominal", "biscuits", "rayon_manquant")
        source.loc["biscuits", "nova_group"] = pd.NA
        source.loc["rayon_manquant", "nutriscore_score"] = pd.NA

        result, report = set_column_types(source)

        assert result["code"].dtype == "string"
        assert result["nutriscore_score"].dtype == "Int64"
        assert result["nova_group"].dtype == "Int64"
        for column in KEY_NUTRIENTS:
            assert result[column].dtype == "float64"
        assert result["code"].tolist() == source["code"].tolist()

        assert report.rule == "typer_colonnes"
        assert report.lines_before == 3
        assert report.lines_after == 3
        assert report.affected_lines == 0
        assert report.details == {}

    def test_edge_keeps_spaces_uppercase_and_missing_values(self):
        """Typer ne doit rien nettoyer : espaces, majuscules et NA restent tels quels."""
        source = pick("biscuits", "rayon_manquant")
        source.loc["rayon_manquant", "nova_group"] = pd.NA

        result, _ = set_column_types(source)

        assert result.loc["biscuits", "code"] == " 2222222222222 "
        assert result.loc["biscuits", "product_name"] == "BISCUITS CHOCO"
        assert pd.isna(result.loc["rayon_manquant", "nova_group"])
        assert pd.isna(result.loc["rayon_manquant", "fat_100g"])


class TestDeduplicateCodes:

    def test_nominal_keeps_most_complete_duplicate_and_drops_empty_code(self):
        source = pick("nominal", "doublon_ancien", "doublon_retenu", "sans_code")

        result, report = deduplicate_codes(source)

        assert set(result["code"]) == {"1111111111111", "3333333333333"}
        assert "doublon_retenu" in result.index
        assert "doublon_ancien" not in result.index

        assert report.rule == "Dédupliquer les codes"
        assert report.lines_before == 4
        assert report.lines_after == 2
        assert report.affected_lines == 2
        assert report.details == {"sans_code": 1, "doublons_supprimes": 1}

    def test_edge_strips_spaces_without_counting_a_change(self):
        """Retirer les espaces d'un code n'est pas une suppression de ligne."""
        source = pick("nominal", "biscuits")

        result, report = deduplicate_codes(source)

        assert result["code"].tolist() == ["1111111111111", "2222222222222"]
        assert result.loc["biscuits", "product_name"] == "BISCUITS CHOCO"
        assert report.affected_lines == 0


class TestHandleEmptyCategories:

    def test_nominal_derives_columns_and_drops_unclassifiable(self):
        source = pick("nominal", "sans_categorie_ni_groupe", "categorie_vide_groupe_connu")

        result, report = handle_empty_categories(source)

        assert "sans_categorie_ni_groupe" not in result.index
        assert result.loc["nominal", "main_category"] == "fr:pates"
        assert result.loc["categorie_vide_groupe_connu", "category_empty"]
        assert result.loc["categorie_vide_groupe_connu", "food_group"] == "en:beverages"

        assert report.rule == "traiter_categories_vides"
        assert report.lines_before == 3
        assert report.lines_after == 2
        assert report.affected_lines == 1
        assert report.details == {
            "categorie_vide": 2,
            "food_group_derive_de_vide": 1,
            "food_group_unknown_total": 1,
            "inclassables_supprimes": 1,
        }

    def test_edge_keeps_unknown_food_group_when_category_exists(self):
        """Seul le cas « ni catégorie ni groupe » est supprimé."""
        source = pick("nominal", "sans_categorie_ni_groupe", "groupe_manquant")

        result, _ = handle_empty_categories(source)

        assert "sans_categorie_ni_groupe" not in result.index
        assert result.loc["groupe_manquant", "main_category"] == "fr:pates"
        assert result.loc["groupe_manquant", "food_group"] == "unknown"
        assert not result.loc["groupe_manquant", "category_empty"]


class TestMissingValuesStrategy:

    def test_nominal_applies_constant_flag_mode_and_drop_column(self):
        source = pick("nominal", "biscuits", "doublon_ancien")
        source.loc["nominal", "brands_tags"] = None
        source.loc["biscuits", "energy-kcal_100g"] = pd.NA
        source.loc["doublon_ancien", "nova_group"] = pd.NA

        result, report = missing_values_strategy(
            source,
            strategy={
                "brands_tags": "constant:unknown",
                "energy-kcal_100g": "flag",
                "nova_group": "mode",
                "quantity": "drop_column",
            },
        )

        assert result.loc["nominal", "brands_tags"] == "unknown"           # constant
        assert pd.isna(result.loc["biscuits", "energy-kcal_100g"])         # flag : pas d'imputation...
        assert result.loc["biscuits", "energy-kcal_100g_manquant"]         # ...mais un drapeau
        assert not result.loc["nominal", "energy-kcal_100g_manquant"]
        assert result.loc["doublon_ancien", "nova_group"] == 2             # mode
        assert "quantity" not in result.columns                            # drop_column

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

    def test_edge_drops_only_rows_without_any_nutrient_and_imputes_by_rayon(self):
        source = pick("nominal", "biscuits", "rayon_manquant", "sans_nutriment")
        source.loc["nominal", "fat_100g"] = pd.NA       # à imputer par la médiane du rayon...
        source.loc["biscuits", "fat_100g"] = 7.0
        source.loc["biscuits", "rayon"] = "Epicerie"    # ...qui vaut 7.0
        source.loc["sans_nutriment", "rayon"] = "Sans groupe"
        # Une seule valeur renseignée (fibres = 0) suffit à garder la ligne
        for column in KEY_NUTRIENTS:
            source.loc["rayon_manquant", column] = pd.NA
        source.loc["rayon_manquant", "fiber_100g"] = 0.0

        result, report = missing_values_strategy(source, strategy={"fat_100g": "foodgroup_median"})

        assert result.loc["nominal", "fat_100g"] == pytest.approx(7.0)
        assert pd.isna(result.loc["rayon_manquant", "fat_100g"])  # pas de rayon -> pas de médiane
        assert "rayon_manquant" in result.index
        assert "sans_nutriment" not in result.index

        assert report.lines_before == 4
        assert report.lines_after == 3
        assert report.affected_lines == 3
        assert report.details["fat_100g:foodgroup_median"] == 3
        assert report.details["rows_dropped_no_nutrient"] == 1


class TestNormalizeUnits:

    def test_nominal_derives_kcal_from_kj(self):
        result, report = normalize_units(one_row({"energy_100g": 418.4}))

        assert result["energy-kcal_100g"].iloc[0] == pytest.approx(100.0, abs=0.1)
        assert report.details["kcal_derivees"] == 1
        assert report.affected_lines == 1

    def test_nominal_recomputes_kcal_when_ratio_out_of_bounds(self):
        # ratio kJ/kcal = 1000 / 100 = 10, hors de [3.9 ; 4.5]
        result, report = normalize_units(one_row({"energy_100g": 1000.0, "energy-kcal_100g": 100.0}))

        assert result["energy-kcal_100g"].iloc[0] == pytest.approx(239.0, abs=0.1)
        assert report.details["kcal_recalculees"] == 1

    def test_nominal_derives_salt_from_sodium(self):
        result, report = normalize_units(one_row({"sodium_100g": 1.0}))

        assert result["salt_100g"].iloc[0] == pytest.approx(2.5)
        assert report.details["sel_derive"] == 1

    def test_nominal_derives_sodium_from_salt(self):
        result, report = normalize_units(one_row({"salt_100g": 5.0}))

        assert result["sodium_100g"].iloc[0] == pytest.approx(2.0)
        assert report.details["sodium_derive"] == 1

    def test_nominal_recomputes_inconsistent_sodium(self):
        # sel = 5 -> sodium attendu 2.0, mais 1.0 déclaré
        result, report = normalize_units(one_row({"salt_100g": 5.0, "sodium_100g": 1.0}))

        assert result["sodium_100g"].iloc[0] == pytest.approx(2.0)
        assert report.details["sodium_recalcule"] == 1

    def test_edge_ratio_exactly_at_lower_bound_is_kept(self):
        # ratio = 390 / 100 = 3.9 pile : borne incluse
        result, report = normalize_units(one_row({"energy_100g": 390.0, "energy-kcal_100g": 100.0}))

        assert result["energy-kcal_100g"].iloc[0] == 100.0
        assert report.details["kcal_recalculees"] == 0

    def test_edge_zero_kcal_is_never_recomputed(self):
        """kcal = 0 est exclue du recalcul (sinon division par zéro)."""
        result, report = normalize_units(one_row({"energy_100g": 100.0, "energy-kcal_100g": 0.0}))

        assert result["energy-kcal_100g"].iloc[0] == 0.0
        assert report.details["kcal_recalculees"] == 0


class TestLimitNutriments:

    def test_nominal_negative_becomes_na(self):
        result, report = limit_nutriments(one_row({"sugars_100g": -5.0}))

        assert pd.isna(result["sugars_100g"].iloc[0])
        assert report.details["sugars_100g_negatifs"] == 1

    def test_nominal_above_100_becomes_na(self):
        result, report = limit_nutriments(one_row({"sugars_100g": 150.0, "carbohydrates_100g": 200.0}))

        assert pd.isna(result["sugars_100g"].iloc[0])
        assert report.details["sugars_100g_au_dessus"] == 1

    def test_nominal_sodium_is_bounded_at_40(self):
        result, report = limit_nutriments(one_row({"sodium_100g": 50.0}))

        assert pd.isna(result["sodium_100g"].iloc[0])
        assert report.details["sodium_100g_au_dessus"] == 1

    def test_nominal_sugars_above_carbs_become_na(self):
        result, report = limit_nutriments(one_row({"sugars_100g": 50.0, "carbohydrates_100g": 40.0}))

        assert pd.isna(result["sugars_100g"].iloc[0])
        assert report.details["sucres"] == 1

    def test_edge_exactly_100_is_kept(self):
        result, report = limit_nutriments(one_row({"sugars_100g": 100.0, "carbohydrates_100g": 100.0}))

        assert result["sugars_100g"].iloc[0] == 100.0
        assert report.details["sugars_100g_au_dessus"] == 0

    def test_edge_sodium_exactly_40_is_kept(self):
        result, _ = limit_nutriments(one_row({"sodium_100g": 40.0}))

        assert result["sodium_100g"].iloc[0] == 40.0

    def test_edge_sugars_exactly_at_tolerance_are_kept(self):
        # sucres = glucides + 0.5 pile : comparaison stricte, donc pas touché
        result, report = limit_nutriments(one_row({"sugars_100g": 40.5, "carbohydrates_100g": 40.0}))

        assert result["sugars_100g"].iloc[0] == 40.5
        assert report.details["sucres"] == 0


class TestFixEnergy:

    # Macronutriments qui donnent 10*4 + 5*4 + 2*9 = 78 kcal
    MACROS_78_KCAL = {"carbohydrates_100g": 10.0, "proteins_100g": 5.0, "fat_100g": 2.0}

    def test_nominal_computes_missing_kcal_from_macros(self):
        result, report = fix_energy(one_row(self.MACROS_78_KCAL))

        assert result["energy-kcal_100g"].iloc[0] == pytest.approx(78.0)
        assert report.details["nulles_recalculees"] == 1

    def test_nominal_recomputes_kcal_above_900(self):
        result, report = fix_energy(one_row({"energy-kcal_100g": 1200.0, **self.MACROS_78_KCAL}))

        assert result["energy-kcal_100g"].iloc[0] == pytest.approx(78.0)
        assert report.details[">900_recalculees"] == 1

    def test_nominal_kcal_above_900_without_macros_becomes_na(self):
        result, report = fix_energy(one_row({"energy-kcal_100g": 1200.0}))

        assert pd.isna(result["energy-kcal_100g"].iloc[0])
        assert report.details[">900_invalidees"] == 1

    def test_nominal_alcohol_is_never_corrected(self):
        result, report = fix_energy(one_row({"energy-kcal_100g": 1200.0, "rayon": "Alcoholic beverages"}))

        assert result["energy-kcal_100g"].iloc[0] == 1200.0
        assert report.affected_lines == 0

    def test_nominal_realigns_kj_on_final_kcal(self):
        # 10 g de glucides -> 40 kcal -> 40 * 4.184 kJ
        result, _ = fix_energy(one_row({"carbohydrates_100g": 10.0, "proteins_100g": 0.0, "fat_100g": 0.0}))

        assert result["energy_100g"].iloc[0] == pytest.approx(40 * 4.184, abs=0.1)

    def test_edge_exactly_900_is_kept(self):
        result, report = fix_energy(one_row({"energy-kcal_100g": 900.0}))

        assert result["energy-kcal_100g"].iloc[0] == 900.0
        assert report.affected_lines == 0

    def test_edge_macros_below_50_kcal_are_not_used_for_consistency(self):
        # calcul 4/4/9 = 40 kcal (< 50) : trop faible pour juger, même face à 500 kcal déclarées
        result, report = fix_energy(one_row({
            "energy-kcal_100g": 500.0,
            "carbohydrates_100g": 10.0, "proteins_100g": 0.0, "fat_100g": 0.0,
        }))

        assert result["energy-kcal_100g"].iloc[0] == 500.0
        assert report.details["incoherentes_recalculees"] == 0

    def test_edge_gap_exactly_50_percent_is_kept(self):
        # calcul = 100 kcal, déclaré = 150 -> écart de 50 % pile : borne stricte
        result, report = fix_energy(one_row({
            "energy-kcal_100g": 150.0,
            "carbohydrates_100g": 25.0, "proteins_100g": 0.0, "fat_100g": 0.0,
        }))

        assert result["energy-kcal_100g"].iloc[0] == 150.0
        assert report.details["incoherentes_recalculees"] == 0


# ============================================================
# 3. Pureté et idempotence, pour toutes les règles
# ============================================================

def _types_source():
    source = pick("nominal", "biscuits", "rayon_manquant")
    source.loc["biscuits", "nova_group"] = pd.NA
    source.loc["rayon_manquant", "nutriscore_score"] = pd.NA
    return source


def _missing_values_source():
    source = pick("nominal", "biscuits", "doublon_ancien")
    source.loc["nominal", "brands_tags"] = None
    source.loc["biscuits", "nova_group"] = pd.NA
    source.loc["doublon_ancien", "fat_100g"] = pd.NA
    return source


# Le flag est exclu : il recrée sa colonne à chaque passage et compterait
# donc toujours des lignes touchées (testé à part dans TestMissingValuesStrategy).
MISSING_VALUES_STRATEGY = {
    "brands_tags": "constant:unknown",
    "nova_group": "mode",
    "fat_100g": "foodgroup_median",
    "quantity": "drop_column",
}

# (règle, fonction qui fabrique les données d'entrée, paramètres de la règle)
RULE_CASES = [
    pytest.param(set_column_types, _types_source, {}, id="set_column_types"),
    pytest.param(deduplicate_codes,
                 lambda: pick("nominal", "doublon_ancien", "doublon_retenu", "sans_code"), {},
                 id="deduplicate_codes"),
    # Sans les produits « catégorie vide gardée » : la règle les recompte comme
    # touchés à chaque passage, même sans rien modifier (limite connue du Report).
    pytest.param(handle_empty_categories, lambda: pick("nominal", "sans_categorie_ni_groupe", "categorie_vide_groupe_connu"), {},
                 id="handle_empty_categories"),
    pytest.param(missing_values_strategy, _missing_values_source, {"strategy": MISSING_VALUES_STRATEGY},
                 id="missing_values_strategy"),
    pytest.param(normalize_units, lambda: pick(*PRODUCTS), {}, id="normalize_units"),
    pytest.param(limit_nutriments, lambda: pick(*PRODUCTS), {}, id="limit_nutriments"),
    pytest.param(fix_energy, lambda: pick(*PRODUCTS), {}, id="fix_energy"),
]


@pytest.mark.parametrize("rule, make_source, kwargs", RULE_CASES)
def test_rule_is_pure(rule, make_source, kwargs):
    """La règle travaille sur une copie : l'entrée reste identique."""
    source = make_source()
    snapshot = source.copy(deep=True)

    rule(source, **kwargs)

    assert_frame_equal(source, snapshot)


@pytest.mark.parametrize("rule, make_source, kwargs", RULE_CASES)
def test_rule_is_idempotent(rule, make_source, kwargs):
    """Deuxième passage = même résultat, et aucune ligne touchée."""
    first_result, _ = rule(make_source(), **kwargs)
    second_result, second_report = rule(first_result, **kwargs)

    assert_frame_equal(first_result, second_result)
    assert second_report.affected_lines == 0
