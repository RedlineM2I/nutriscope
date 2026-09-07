import pandas as pd
from _duckdb import DuckDBPyConnection

def get_nom_table(conn, source_column:str, column_name: str) -> pd.DataFrame:
    return conn.sql(f"""
        SELECT code AS produit_code,
               lower(REGEXP_REPLACE(UNNEST({source_column}), '^[a-zA-Z]{{2}}:', '')) AS {column_name}
        FROM produits_dedup
    """).df()

def build_liaison_table(conn : DuckDBPyConnection, source_column : str, column_name : str, table_name : str) :
    """
    Construit une table de liaison entre la table table_name et la table produit
    :param conn: connexion à la base duckdb
    :param source_column: nom de la colonne source dans le fichier parquet
    :param column_name: nom de la future colonne dans la table (nom)
    :param table_name: nom de la table à créer
    :return: DataFrame de la nouvelle table ainsi que son DataFrame de liaison
    """
    liaison = get_nom_table(conn, source_column, column_name)
    nom_uniques = liaison[[column_name]].drop_duplicates().reset_index(drop=True).reset_index( names="id")

    table_liaison = liaison.merge(nom_uniques, on="nom")[["produit_code", "id"]]
    table_liaison = table_liaison.rename(columns={"id": f"{table_name[:len(table_name)-1]}_id"})
    return nom_uniques, table_liaison.drop_duplicates(subset=["produit_code", f"{table_name[:len(table_name)-1]}_id"])