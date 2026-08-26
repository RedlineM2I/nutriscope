import time


PARQUET_FILE = '../data/food.parquet'
CLEAN_PARQUET_FILE = '../data/food_clean.parquet'
PARQUET_FR = "../data/food_france.parquet"


def timer(function):
    def f():
        start = time.perf_counter()
        res = function()
        duration = time.perf_counter() - start
        print(f"Temps de traitement : {duration:.3f} secondes")
        return res

    return f


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