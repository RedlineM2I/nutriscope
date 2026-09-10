from _duckdb import DuckDBPyConnection

from src.config import PARQUET_FR

def create_produits_code_clean(conn : DuckDBPyConnection) :
    """
    Crée une table temporaire propre des produits à partir du fichier parquet
    :param conn: Connexion à la base duckdb
    :return:
    """
    conn.sql(f"""
        CREATE OR REPLACE TEMP TABLE produits_dedup AS
        SELECT row_number() over () as id, *
        FROM '{PARQUET_FR}'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY code ORDER BY completeness DESC) = 1
    """)

def create_nutriments_extraits(conn : DuckDBPyConnection) :
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
            ) AS energie_100g,
        
            list_extract(list_filter(nutriments, x -> x.name = 'sugars'), 1)."100g" AS sucres_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'carbohydrates'), 1)."100g" AS glucides_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fat'), 1)."100g" AS matieres_grasses_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'saturated-fat'), 1)."100g" AS acides_gras_satures_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'salt'), 1)."100g" AS sel_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'proteins'), 1)."100g" AS proteines_100g,
            list_extract(list_filter(nutriments, x -> x.name = 'fiber'), 1)."100g" AS fibres_100g,
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