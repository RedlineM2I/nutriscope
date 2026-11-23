"""Connexion à PostgreSQL à partir des variables `POSTGRES_*` du `.env`."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine

# Environnement SQL
load_dotenv()


def get_engine() -> Engine:
    """Crée un engine SQLAlchemy à partir des informations de la base PostgreSQL du `.env`.

    `POSTGRES_PORT` vaut 5432 par défaut ; les autres variables sont obligatoires.

    Returns:
        Engine de connexion à la base.

    Raises:
        KeyError: une variable `POSTGRES_*` obligatoire est absente.
    """
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.environ['POSTGRES_HOST']}:{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url, pool_pre_ping=True)
