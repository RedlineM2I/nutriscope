"""Écriture de DataFrames dans Postgres via COPY."""
import csv
import io
import logging
from typing import Iterator, Any

import pandas as pd
from sqlalchemy.engine.base import Connection

logging.basicConfig(
    filename="app.log",
    encoding="utf-8",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def psql_insert_copy(table: pd.DataFrame, conn: Connection, keys: list[str], data_iter: Iterator[Any]) -> None:
    """
    Insertion en base en créant un buffer CSV, utilise COPY au lieu d'INSERT (rapide pour gros volumes).

    :param table: DataFrame à insérer dans la base de données
    :param conn: Connexion à la BDD
    :param keys: Liste des colonnes à inclure dans l'insertion
    :param data_iter: Iterateur sur les lignes du DataFrame à insérer
    """

    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerows(data_iter)
        buffer.seek(0)
        columns = ", ".join(f'"{k}"' for k in keys)
        table_name = f'"{table.schema}"."{table.name}"' if table.schema else f'"{table.name}"'
        cur.copy_expert(
            f"COPY {table_name} ({columns}) FROM STDIN WITH CSV",
            buffer,
        )