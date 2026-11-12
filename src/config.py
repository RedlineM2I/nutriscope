"""Chemins du projet et constantes métier."""

from enum import StrEnum
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent  # dossier contenant config.py (src/)

TODAY = date.today().strftime("%Y%m%d")

# Source brute : le parquet Open Food Facts téléchargé, sauf si la variable
# d'environnement NUTRISCOPE_SOURCE désigne un autre parquet (échantillon, extrait)
PARQUET_FILE = f"{BASE_DIR.parent}/data/food.parquet"
SOURCE_ENV = "NUTRISCOPE_SOURCE"
CLEAN_PARQUET_FILE = f"{BASE_DIR.parent}/data/food_clean.parquet"

# Brut figé du jour (périmètre France) et son manifeste (empreinte de la source)
RAW_DIR = BASE_DIR.parent / "data" / "raw"
PARQUET_FR = f"{RAW_DIR}/food_france_{TODAY}.parquet"
RAW_MANIFEST = f"{RAW_DIR}/manifest_{TODAY}.json"

# Sorties datées du jour (écriture). Pour lire, passer par src.outputs, qui retombe
# sur la sortie la plus récente quand celle du jour n'existe pas.
PARQUET_DIR = BASE_DIR.parent / "data" / "parquet"
PARQUET_CLEAN_DATASET = f"{PARQUET_DIR}/food_clean_{TODAY}.parquet"
PARQUET_CLEAN_BY_FOOD_GROUP = f"{PARQUET_DIR}/products_{TODAY}"
# Marqueur écrit en dernier dans un dossier partitionné : son absence = écriture incomplète
SUCCESS_MARKER = "_SUCCESS"

SCHEMA_PRODUIT_JSON = f"{PARQUET_DIR}/schema_products_{TODAY}.json"

# Journal des durées : une ligne JSON par étape terminée, échecs compris
PIPELINE_LOG = BASE_DIR.parent / "data" / "logs" / "pipeline.jsonl"

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
