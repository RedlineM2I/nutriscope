import io
import pandas as pd
import logging
from _duckdb import DuckDBPyConnection
from sqlalchemy import Connection

from src.data.db.connection import get_engine
from src.data.extract.tags import build_liaison_table

#Tables où il faut créer une table de liaison
TAG_TABLES = {
    "categories_tags": "categories",
    "origins_tags": "origines",
    "additives_tags": "additifs",
    "brands_tags": "marques",
    "labels_tags": "labels",
    "ingredients_tags": "ingredients",
}

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_all_in_db(conn_duckdb : DuckDBPyConnection) :
    engine = get_engine()
    try:
        with engine.begin() as conn:  # commit automatique si succès, rollback si erreur
            insert_produits(get_produits(conn_duckdb=conn_duckdb), conn)
            for source_col, table_name in TAG_TABLES.items():
                print(f"Insertion des {table_name}")
                table, table_liaison = build_liaison_table(conn_duckdb, source_col, "nom", table_name)
                insert_in_db_copy(table, table_name, conn)
                insert_in_db_copy(table_liaison, f"produits_{table_name}", conn)
            #insert_nutriments(con, conn)
    except Exception as e:
        logger.error(f"Échec de l'import : {e}")

def insert_in_db_copy(df: pd.DataFrame, table_name: str, conn : Connection, colonnes_int: list[str] = None) :
    df = df.copy()
    for col in colonnes_int or []:
        df[col] = df[col].astype("Int64")

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, na_rep="\\N")
    buffer.seek(0)

    colonnes_sql = f"({', '.join(df.columns)})"
    cur = conn.connection.cursor()
    cur.copy_expert(
        f"COPY {table_name} {colonnes_sql} FROM STDIN WITH (FORMAT csv, NULL '\\N')",
        buffer
    )
    logger.info(f"{len(df)} lignes importées avec succès")

def insert_produits(df : pd.DataFrame, conn_psql : Connection):
    print("Insertion des produits")
    insert_in_db_copy(df, "produits", conn_psql, colonnes_int=["nova_group", "nutriscore_score", "environmental_score_score"])

def get_produits(conn_duckdb : DuckDBPyConnection) :
    query = f"""
            SELECT
                code,
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
                environmental_score_score
            FROM produits_dedup
            """
    return conn_duckdb.sql(query).df()