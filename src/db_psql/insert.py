"""Écriture de DataFrames dans Postgres via COPY."""

import io
import logging

import pandas as pd
from sqlalchemy import Connection

from src.console import timer
from src.db_psql.connection import get_engine

logger = logging.getLogger(__name__)


def insert_one_item(table_name: str, table: pd.DataFrame, columns_int: list[str] = None):
    """
    Création d'une connexion puis insertion en base
    :param table_name: Table dans laquelle insérer le dataframe
    :param table: Dataframe à insérer dans la base
    :param columns_int: Noms des colonnes à convertir en Integer
    :return:
    """

    @timer(label=table_name)
    def tmp():
        with get_engine().begin() as conn:
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
