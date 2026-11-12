"""Chemins du projet et constantes métier."""

from enum import StrEnum
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent  # dossier contenant config.py (src/)

PARQUET_FILE = f"{BASE_DIR.parent}/data/food.parquet"
CLEAN_PARQUET_FILE = f"{BASE_DIR.parent}/data/food_clean.parquet"
PARQUET_FR = f"{BASE_DIR.parent}/data/food_france.parquet"
# PARQUET_CLEAN_DATASET = f"{BASE_DIR.parent}/data/parquet/food_clean.parquet"
TODAY = date.today().strftime("%Y%m%d")

PARQUET_CLEAN_DATASET = f"{BASE_DIR.parent}/data/parquet/food_clean_{TODAY}.parquet"
PARQUET_CLEAN_BY_FOOD_GROUP = f"{BASE_DIR.parent}/data/parquet/products"
# Marqueur écrit en dernier dans un dossier partitionné : son absence = écriture incomplète
SUCCESS_MARKER = "_SUCCESS"

SCHEMA_PRODUIT_JSON = f"{BASE_DIR.parent}/data/parquet/schema_products.json"

SCRIPT_CREATION = f"{BASE_DIR.parent}/src/db_psql/create_tables.sql"

ELEVATOR = BASE_DIR.parent / "data" / "elevator.mp3"

EXPORT_PARQUET_DIR = BASE_DIR.parent / "data" / "export"

# Export figé pour la phase 4 (TP 14+) : la graine et la part de test ne changent plus
EXPORTS_DIR = BASE_DIR.parent / "data" / "exports"
SPLIT_SEED = 42
TEST_SIZE = 0.2

EXPORT_CLEANING_REPORT = BASE_DIR.parent / "docs" / "data" / "rapport_nettoyage.md"



class Tag(StrEnum):
    CATEGORY = "category"
    ORIGIN = "origin"
    LABEL = "label"
    ADDITIVE = "additive"
    BRAND = "brand"
    INGREDIENT = "ingredient"
    # FOODGROUP = "foodgroup"

    @property
    def plural(self) -> str:
        """Nom des tables et des colonnes de tags : categories, origins..."""

        if self is Tag.CATEGORY:
            return "categories"

        # elif self is Tag.FOODGROUP:
        #     return "food"
        
        return f"{self}s"

    # def get_origin_tag(self):
    #     return "food_groups_tags" if self is Tag.FOODGROUP else f"{self}s"


# TAG_COLUMNS = [
#     "brands_tags",
#     "categories_tags",
#     "food_groups_tags"
#     "labels_tags",
#     "origins_tags",
#     "ingredients_tags",
#     "additives_tags",
# ]

TAG_COLUMNS = [f"{tag.plural}_tags" for tag in Tag] + [
    "food_groups_tags"
]

ENERGY_COL = "energy-kcal_100g"

KEY_NUTRIENTS = [
    ENERGY_COL,
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

COLUMNS = TAG_COLUMNS + [
    # Général
    "code",
    "product_name",
    "quantity",
    "nutrition_data_per",
    "last_modified_t",

    "nutriments",
    "nutriscore_grade",
    "nutriscore_score",
    "nutrient_levels_tags",

    "nova_group",

    # Qualité des données
    "completeness",

    # Environnement
    "environmental_score_grade",
    "environmental_score_score",

    # Images
    "images",
]

CATEGORIES = [
    "en:snacks",
    "en:beverages",
    "en:meats",
    "en:fruits-and-vegetables-based-foods",
    "en:cheeses",
    "en:fishes",
    "en:desserts"
]
