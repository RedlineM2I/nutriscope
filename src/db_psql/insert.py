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
    """Insère des lignes en base via un buffer CSV, avec COPY au lieu d'INSERT (rapide pour gros volumes).

    S'utilise comme `method=` de `DataFrame.to_sql`, qui fournit les quatre
    arguments.

    Args:
        table: table cible fournie par pandas (`SQLTable`, avec `name` et
            `schema`), pour le DataFrame à insérer dans la base de données.
        conn: connexion à la BDD.
        keys: liste des colonnes à inclure dans l'insertion.
        data_iter: itérateur sur les lignes du DataFrame à insérer.
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