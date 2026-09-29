"""Chemins du projet et constantes métier."""

from enum import StrEnum
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # dossier contenant config.py (src/)

PARQUET_FILE = f"{BASE_DIR.parent}/data/food.parquet"
CLEAN_PARQUET_FILE = f"{BASE_DIR.parent}/data/food_clean.parquet"
PARQUET_FR = f"{BASE_DIR.parent}/data/food_france.parquet"

SCRIPT_CREATION = f"{BASE_DIR.parent}/src/db_psql/create_tables.sql"

ELEVATOR = BASE_DIR.parent / "data" / "elevator.mp3"

EXPORT_PARQUET_DIR = BASE_DIR.parent / "data" / "export"


class Tag(StrEnum):
    CATEGORIE = "categorie"
    ORIGIN = "origin"
    LABEL = "label"
    ADDITIVE = "additive"
    BRAND = "brand"
    INGREDIENT = "ingredient"


COLUMNS = [
    # Général
    "code",
    "product_name",
    "quantity",
    "nutrition_data_per",

    # Classification
    "brands_tags",
    "categories_tags",
    "labels_tags",
    "origins_tags",

    # Ingrédients
    "ingredients_tags",
    "additives_tags",

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
