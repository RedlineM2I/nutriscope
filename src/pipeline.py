"""Orchestration du chargement : lit le parquet via DuckDB, écrit dans Postgres."""

from dataclasses import dataclass
import logging
from concurrent.futures import ProcessPoolExecutor

from _duckdb import DuckDBPyConnection

from src.db_parquet.nutriments import get_nutriments, get_secondary_nutrients_link_table
from src.db_parquet.products import get_products
from src.db_parquet.tags import build_link_table
from src.db_psql.insert import insert_one_item
from src.models import DataModel

# Tables où il faut créer une table de liaison
TAG_TABLES = {
    "categories_tags": "categories",
    "origins_tags": "origins",
    "additives_tags": "additives",
    "brands_tags": "brands",
    "labels_tags": "labels",
    "ingredients_tags": "ingredients",
}
"""
Noms de colonnes dans le fichier parquet où il faut créer une table de liaison associés des noms de table dans la BDD
"""

# Logger
logging.basicConfig(filename="app.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_all_in_db(conn_duckdb: DuckDBPyConnection, data: DataModel):
    """
    Insertion de toutes les tables dans la base de donnée
    :param conn_duckdb: Connexion à la base duckdb
    :return:
    """
    try:
        all_tables = {}
        products = get_products(conn=conn_duckdb)
        nutriments = get_nutriments(conn_duckdb)
        secondary_nutrients, products_secondary_nutrients = get_secondary_nutrients_link_table(conn_duckdb)
        for source_col, table_name in TAG_TABLES.items():
            id_tag_nm_table, link_table = build_link_table(conn_duckdb, source_col, "name", table_name)
            all_tables[table_name] = (id_tag_nm_table, link_table)

        with ProcessPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(insert_one_item, "products", products,
                                   columns_int=["nova_group", "nutriscore_score", "environmental_score_score"]),
                       pool.submit(insert_one_item, "nutritional_values", nutriments),
                       pool.submit(insert_one_item, "secondary_nutrients", secondary_nutrients),
                       pool.submit(insert_one_item, "products_secondary_nutrients", products_secondary_nutrients)]
            for table_name, tables in all_tables.items():
                futures.append(pool.submit(insert_one_item, table_name, tables[0]))
                futures.append(pool.submit(insert_one_item, f"products_{table_name}", tables[1]))
            for future in futures:
                future.result()


    except Exception as e:
        # logger.error(f"Échec de l'import : {e}")
        raise e
