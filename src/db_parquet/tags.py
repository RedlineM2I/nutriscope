"""Construction des tables de tags et de leurs tables de liaison depuis DuckDB."""
import pandas as pd
from _duckdb import DuckDBPyConnection

from src.console import timer


def get_id_tag_nm_table(conn_duckdb: DuckDBPyConnection, source_column: str, column_name: str) -> pd.DataFrame:
    """Extrait les id des produits avec leurs tags associés.

    Le préfixe de langue (ex. `en:`) est retiré et les tags sont mis en minuscules.

    Args:
        conn_duckdb: connexion à la base DuckDB.
        source_column: nom de la colonne source dans le fichier parquet.
        column_name: nom de la future colonne dans la table (nom).

    Returns:
        DataFrame des produits avec leurs tags associés, un tag par ligne.
    """
    return conn_duckdb.sql(f"""
        SELECT id AS product_id,
               lower(REGEXP_REPLACE(UNNEST({source_column}), '^[a-zA-Z]{{2}}:', '')) AS {column_name}
        FROM produits_dedup
    """).df()


@timer
def build_link_table(conn_duckdb: DuckDBPyConnection, source_column: str, column_name: str, table_name: str):
    """Construit une table de liaison entre la table `table_name` et la table produit.

    La clé étrangère est nommée d'après le singulier de `table_name`
    (ex. `categories` -> `category_id`).

    Args:
        conn_duckdb: connexion à la base DuckDB.
        source_column: nom de la colonne source dans le fichier parquet.
        column_name: nom de la future colonne dans la table (nom).
        table_name: nom de la table à créer.

    Returns:
        Le DataFrame de la nouvelle table et son DataFrame de liaison.
    """
    link = get_id_tag_nm_table(conn_duckdb, source_column, column_name)
    id_tag_nm_table = link[[column_name]].drop_duplicates().reset_index(drop=True).reset_index(names="id")

    singular = f"{table_name[:-3]}y" if table_name.endswith("ies") else table_name[:-1]
    fk_column = f"{singular}_id"

    link_table = link.merge(id_tag_nm_table, on=column_name)[["product_id", "id"]]
    link_table = link_table.rename(columns={"id": fk_column})
    return id_tag_nm_table, link_table.drop_duplicates(subset=["product_id", fk_column])
