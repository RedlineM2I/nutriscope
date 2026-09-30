from _duckdb import DuckDBPyConnection

from src.config import PARQUET_FR

def create_temp_products(conn: DuckDBPyConnection):
    """
    Crée une table temporaire propre des produits à partir du fichier parquet
    :param conn: Connexion à la base duckdb
    :return:
    """
    conn.sql(f"""
        CREATE OR REPLACE TEMP TABLE produits_dedup AS
        SELECT row_number() over () as id, *
        FROM '{PARQUET_FR}'
    """)


def create_nutriments_extraits(conn: DuckDBPyConnection):
    """
    Crée une table temporaire propre des nutriments à partir du fichier parquet
    :param conn: Connexion à la base duckdb
    :return:
    """
    conn.sql("""
        CREATE OR REPLACE TEMP TABLE nutriments_extraits AS
        SELECT
            id,

            -- Énergie : kJ natif, sinon conversion depuis kcal (1 kcal = 4.184 kJ)
            COALESCE(
                list_extract(list_filter(nutriments, x -> x.name = 'energy-kj'), 1)."100g",
                list_extract(list_filter(nutriments, x -> x.name = 'energy-kcal'), 1)."100g" * 4.184
            ) AS energy_100g,

            list_extract(list_filter(nutriments, x -> x.name = 'sugars'), 1)."100g" AS sugars_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'carbohydrates'), 1)."100g" AS carbohydrates_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fat'), 1)."100g" AS fat_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'saturated-fat'), 1)."100g" AS saturated_fat_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'salt'), 1)."100g" AS salt_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'proteins'), 1)."100g" AS proteins_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fiber'), 1)."100g" AS fiber_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fruits-vegetables-nuts'), 1)."100g" AS fruits_nuts_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fruits-vegetables-legumes'), 1)."100g" AS fruits_legumes_100g,

            -- Tout le reste : la liste privée des noms déjà extraits ci-dessus
            list_filter(
                nutriments,
                x -> x.name NOT IN (
                    'energy-kj', 'energy-kcal', 'sugars', 'carbohydrates', 'fat', 'saturated-fat',
                    'salt', 'proteins', 'fiber', 'fruits-vegetables-nuts', 'fruits-vegetables-legumes'
                )
            ) AS nutriments_secondaires
        FROM produits_dedup;
    """)
