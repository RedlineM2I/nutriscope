"""Création des tables PostgreSQL à partir de `create_tables.sql`."""
from sqlalchemy import text
from src.config import SCRIPT_CREATION


def create_tables(conn) -> None:
    """Crée les tables à partir du script de création.

    Le script est découpé sur les `;` et chaque instruction est exécutée à part.

    Args:
        conn: connexion SQLAlchemy ouverte.
    """
    with open(SCRIPT_CREATION, "r") as f:
        sql_script = f.read()

    for statement in sql_script.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(text(statement))
