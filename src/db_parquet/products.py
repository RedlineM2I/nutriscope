from duckdb import DuckDBPyConnection

from src.config import COLUMNS, PARQUET_FILE, PARQUET_FR, TAG_COLUMNS

import pandas as pd
import duckdb


def extract_products(conn: DuckDBPyConnection) -> pd.DataFrame:
    """
    Extrait les produits du parquet brut, nutriments aplatis
    :param conn: Connexion à la base DuckDB
    :return: Dataframe des produits
    """
    query = f"""
        SELECT
            code,
            last_modified_t,
            REPLACE(COALESCE(
                list_extract(list_filter(product_name, x -> x.lang = 'fr'),   1)."text",
                list_extract(list_filter(product_name, x -> x.lang = 'main'), 1)."text",
                list_extract(list_filter(product_name, x -> x.lang = 'en'),   1)."text"), chr(0), '')
            AS product_name,
            quantity,
            nutrition_data_per,
            nutriscore_grade,
            nutriscore_score,
            nova_group,
            completeness,
            environmental_score_grade,
            environmental_score_score,

            {",".join(TAG_COLUMNS)},
        
            
            list_extract(list_filter(nutriments, x -> x.name = 'energy-kj'), 1)."100g" AS energy_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'energy-kcal'), 1)."100g" AS 'energy-kcal_100g',
            list_extract(list_filter(nutriments, x -> x.name = 'sugars'), 1)."100g" AS sugars_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'carbohydrates'), 1)."100g" AS carbohydrates_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fat'), 1)."100g" AS fat_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'saturated-fat'), 1)."100g" AS 'saturated-fat_100g',
            list_extract(list_filter(nutriments, x -> x.name = 'salt'), 1)."100g" AS salt_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'sodium'), 1)."100g" AS sodium_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'proteins'), 1)."100g" AS proteins_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fiber'), 1)."100g" AS fiber_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fruits-vegetables-nuts'), 1)."100g" AS fruits_nuts_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fruits-vegetables-legumes'), 1)."100g" AS 'fruits-vegetables-legumes_100g',

            -- Tout le reste : la liste privée des noms déjà extraits ci-dessus
            list_filter(
                nutriments,
                x -> x.name NOT IN (
                    'energy-kj', 'energy-kcal', 'sugars', 'carbohydrates', 'fat', 'saturated-fat',
                    'salt', 'proteins', 'fiber', 'fruits-vegetables-nuts', 'fruits-vegetables-legumes'
                )
            ) AS nutriments_secondaires
        FROM '{PARQUET_FR}'
    """

    return conn.sql(query).df()


def get_products_from(country: str):
    duckdb.sql(f"""
        COPY (
            SELECT {",".join(COLUMNS)}
            FROM '{PARQUET_FILE}'
            WHERE list_contains(countries_tags, '{country}')
        ) TO '{PARQUET_FR}' (FORMAT PARQUET)
    """)