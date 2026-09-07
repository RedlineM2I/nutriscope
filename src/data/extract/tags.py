import pandas as pd
from _duckdb import DuckDBPyConnection

from src.config import timer

def get_code_tag_nm_table(conn, source_column:str, column_name: str) -> pd.DataFrame:
    return conn.sql(f"""
        SELECT code AS produit_code,
               lower(REGEXP_REPLACE(UNNEST({source_column}), '^[a-zA-Z]{{2}}:', '')) AS {column_name}
        FROM produits_dedup
    """).df()

@timer
def build_link_table(conn : DuckDBPyConnection, source_column : str, column_name : str, table_name : str) :
    """
    Construit une table de liaison entre la table table_name et la table produit
    :param conn: connexion à la base duckdb
    :param source_column: nom de la colonne source dans le fichier parquet
    :param column_name: nom de la future colonne dans la table (nom)
    :param table_name: nom de la table à créer
    :return: DataFrame de la nouvelle table ainsi que son DataFrame de liaison
    """
    print(f"Récupération des données pour la table {table_name}")
    link = get_code_tag_nm_table(conn, source_column, column_name)
    id_tag_nm_table = link[[column_name]].drop_duplicates().reset_index(drop=True).reset_index( names="id")

    link_table = link.merge(id_tag_nm_table, on="nom")[["produit_code", "id"]]
    link_table = link_table.rename(columns={"id": f"{table_name[:len(table_name)-1]}_id"})
    return id_tag_nm_table, link_table.drop_duplicates(subset=["produit_code", f"{table_name[:len(table_name)-1]}_id"])