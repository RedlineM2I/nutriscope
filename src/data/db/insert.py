import io
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import logging
from _duckdb import DuckDBPyConnection
from sqlalchemy import Connection

from src.config import timer
from src.data.db.connection import get_engine
from src.data.extract.nutriments import get_secondary_nutriments, get_nutriments
from src.data.extract.tags import build_link_table

# Tables où il faut créer une table de liaison
TAG_TABLES = {
    "categories_tags": "categories",
    "origins_tags": "origines",
    "additives_tags": "additifs",
    "brands_tags": "marques",
    "labels_tags": "labels",
    "ingredients_tags": "ingredients",
}
"""
Noms de colonnes dans le fichier parquet où il faut créer une table de liaison associés des noms de table dans la BDD
"""

# Logger
logging.basicConfig(filename="app.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_all_in_db(conn_duckdb: DuckDBPyConnection):
    """
    Insertion de toutes les tables dans la base de donnée
    :param conn_duckdb: Connexion à la base duckdb
    :return:
    """
    try:
        all_tables = {}
        products = get_products(conn_duckdb=conn_duckdb)
        nutriments = get_nutriments(conn_duckdb)
        secondary_nutriments, products_secondary_nutriments = get_secondary_nutriments_link_table(
            get_secondary_nutriments(conn_duckdb))
        for source_col, table_name in TAG_TABLES.items():
            id_tag_nm_table, link_table = build_link_table(conn_duckdb, source_col, "nom", table_name)
            all_tables[table_name] = (id_tag_nm_table, link_table)

        with ProcessPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(insert_one_item, "produits", products,
                                   columns_int=["nova_group", "nutriscore_score", "environmental_score_score"]),
                       pool.submit(insert_one_item, "valeurs_nutritionnelles", nutriments),
                       pool.submit(insert_one_item, "nutriments_secondaires", secondary_nutriments),
                       pool.submit(insert_one_item, "produits_nutriments_secondaires", products_secondary_nutriments)]
            for table_name, tables in all_tables.items():
                futures.append(pool.submit(insert_one_item, table_name, tables[0]))
                futures.append(pool.submit(insert_one_item, f"produits_{table_name}", tables[1]))
            for future in futures:
                future.result()


    except Exception as e:
        # logger.error(f"Échec de l'import : {e}")
        raise e


def insert_one_item(table_name, table, columns_int: list[str] = None):
    @timer(label=table_name)
    def tmp():
        with get_engine().begin() as conn:
            print(f"Insertion des {table_name}")
            insert_in_db_copy(table, table_name, conn, columns_int=columns_int)

    tmp()


@timer
def insert_in_db_copy(df: pd.DataFrame, table_name: str, conn: Connection, columns_int: list[str] = None):
    """
    Insertion en base en créant un buffer CSV
    :param df: Dataframe à insérer dans la base
    :param table_name: Table dans laquelle on insère le dataframe
    :param conn: Connexion à la BDD
    :param columns_int: Noms des colonnes à convertir en Integer
    :return:
    """
    for col in columns_int or []:
        df[col] = df[col].astype("Int64")

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, na_rep="\\N")
    buffer.seek(0)

    columns_sql = f"({', '.join(df.columns)})"
    cur = conn.connection.cursor()
    cur.copy_expert(
        f"COPY {table_name} {columns_sql} FROM STDIN WITH (FORMAT csv, NULL '\\N')",
        buffer
    )
    logger.info(f"{len(df)} lignes importées avec succès")


def get_secondary_nutriments_link_table(df_secondary_nutriments: pd.DataFrame):
    id_nm_unit = df_secondary_nutriments[["nom", "unite"]].drop_duplicates(subset="nom").reset_index(
        drop=True).reset_index(names="id")
    link_table = df_secondary_nutriments.merge(id_nm_unit, on=["nom", "unite"])[["produit_id", "id", "valeur_100g"]]
    link_table = link_table.rename(columns={"id": "nutriment_id"}).drop_duplicates(
        subset=["produit_id", "nutriment_id"])
    return id_nm_unit, link_table


def get_products(conn_duckdb: DuckDBPyConnection) -> pd.DataFrame:
    """
    Extrait les produits de la base DuckDB
    :param conn_duckdb: Connexion à la base DuckDB
    :return: Dataframe des produits
    """
    query = f"""
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
    return conn_duckdb.sql(query).df()
