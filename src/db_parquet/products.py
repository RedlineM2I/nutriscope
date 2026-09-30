from duckdb import DuckDBPyConnection

import pandas as pd


def get_products(conn: DuckDBPyConnection) -> pd.DataFrame:
    """
    Extrait les produits de la base DuckDB
    :param conn_duckdb: Connexion à la base DuckDB
    :return: Dataframe des produits
    """
    query = """
            SELECT
                id,
                code,
                REPLACE(COALESCE(
                list_extract(list_filter(product_name, x -> x.lang = 'fr'),   1)."text",
                list_extract(list_filter(product_name, x -> x.lang = 'main'), 1)."text",
                list_extract(list_filter(product_name, x -> x.lang = 'en'),   1)."text"), chr(0), '')
                AS product_name,
                quantity,
                nutrition_data_per,
                case
                    when nutriscore_grade = 'unknown' or nutriscore_grade = 'not-applicable'
                    then null
                    else nutriscore_grade
                end as nutriscore_grade,
                nutriscore_score,
                nova_group,
                completeness,
                environmental_score_grade,
                environmental_score_score
            FROM produits_dedup
            """
    return conn.sql(query).df()
