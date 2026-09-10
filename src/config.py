from pathlib import Path

import time
import functools

BASE_DIR = Path(__file__).resolve().parent  # dossier contenant config.py (src/)

PARQUET_FILE = f"{BASE_DIR.parent}/data/food.parquet"
CLEAN_PARQUET_FILE = f"{BASE_DIR.parent}/data/food_clean.parquet"
PARQUET_FR = f"{BASE_DIR.parent}/data/food_france.parquet"

SCRIPT_CREATION = f"{BASE_DIR.parent}/src/data/db/create_tables.sql"

def timer(func=None, *, label=None, store=None):
    """
    Mesure le temps d'exécution.

    Utilisable de 4 façons :
        @timer
        @timer(label="chargement")
        @timer(store=timings)             # timings[nom] = durée (dict fourni)
        @timer(label="load", store=timings)

    Fonctionne sur n'importe quelle fonction OU méthode (grâce à *args/**kwargs
    et functools.wraps). Le temps est loggué même si la fonction lève.
    """
    def decorator(fn):
        name = label or fn.__qualname__          # __qualname__ => "Classe.methode"

        @functools.wraps(fn)                      # garde nom, docstring, signature
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                print(f"[{name}] {duration:.3f} s")
                if store is not None:
                    store[name] = duration
        return wrapper

    # @timer          -> func est la fonction        -> on décore tout de suite
    # @timer(...)      -> func est None              -> on renvoie le décorateur
    return decorator(func) if callable(func) else decorator


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