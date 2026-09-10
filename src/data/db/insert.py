import io
import pandas as pd
import logging
from _duckdb import DuckDBPyConnection
from pandas.core.interchange.dataframe_protocol import DataFrame
from sqlalchemy import Connection, text

from src.config import timer
from src.data.db.connection import get_engine
from src.data.extract.nutriments import get_secondary_nutriments, get_nutriments
from src.data.extract.tags import build_link_table

#Tables où il faut créer une table de liaison
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_all_in_db(conn_duckdb : DuckDBPyConnection) :
    """
    Insertion de toutes les tables dans la base de donnée
    :param conn_duckdb: Connexion à la base duckdb
    :return:
    """
    engine = get_engine()
    try:
        with engine.begin() as conn:  # commit automatique si succès, rollback si erreur

            #Chargement
            insert_products(get_products(conn_duckdb=conn_duckdb), conn)
            insert_nutriments(get_nutriments(conn_duckdb), get_secondary_nutriments(conn_duckdb), conn)
            for source_col, table_name in TAG_TABLES.items():
                print(f"Insertion des {table_name}")
                id_tag_nm_table, link_table = build_link_table(conn_duckdb, source_col, "nom", table_name)
                insert_in_db_copy(id_tag_nm_table, table_name, conn)
                insert_in_db_copy(link_table, f"produits_{table_name}", conn)

    except Exception as e:
        logger.error(f"Échec de l'import : {e}")

@timer
def insert_in_db_copy(df: pd.DataFrame, table_name: str, conn : Connection, columns_int: list[str] = None) :
    """
    Insertion en base en créant un buffer CSV
    :param df: Dataframe à insérer dans la base
    :param table_name: Table dans laquelle on insère le dataframe
    :param conn: Connexion à la BDD
    :param columns_int: Noms des colonnes à convertir en Integer
    :return:
    """
    print(f"Insertion des données dans la table {table_name}")
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

def insert_products(df : pd.DataFrame, conn_psql : Connection):
    """
    Insertion des produits dans la base
    :param df: DataFrame des produits
    :param conn_psql: Connexion à la BDD
    :return:
    """
    print("Insertion des produits")
    insert_in_db_copy(df, "produits", conn_psql, columns_int=["nova_group", "nutriscore_score", "environmental_score_score"])

def insert_nutriments(df_nutriments : pd.DataFrame, df_secondary_nutriments : pd.DataFrame, conn_psql : Connection) :
    """
    Insertion des nutriments dans la base
    :param df_nutriments: Dataframe des nutriments principaux
    :param df_secondary_nutriments: Dataframe des nutriments secondaires
    :param conn_psql: Connexion à la BDD
    :return:
    """
    print("Insertion des nutriments")
    insert_in_db_copy(df_nutriments, "valeurs_nutritionnelles", conn_psql)
    #100 sec
    id_nm_unit = df_secondary_nutriments[["nom","unite"]].drop_duplicates(subset="nom").reset_index(drop=True).reset_index(names="id")

    link_table = df_secondary_nutriments.merge(id_nm_unit, on=["nom","unite"])[["produit_code", "id","valeur_100g"]]
    link_table = link_table.rename(columns={"id": "nutriment_id"}).drop_duplicates(subset=["produit_code", "nutriment_id"])
    insert_in_db_copy(id_nm_unit, "nutriments", conn_psql)
    insert_in_db_copy(link_table, "produits_nutriments_secondaires", conn_psql)

def get_products(conn_duckdb : DuckDBPyConnection) -> DataFrame:
    """
    Extrait les produits de la base DuckDB
    :param conn_duckdb: Connexion à la base DuckDB
    :return: Dataframe des produits
    """
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