import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine

# Environnement SQL
load_dotenv()

def get_engine() -> Engine:
    """
    Crée un engine sqlalchemy à partir des informations de la base postgresql à utiliser dans le '.env'
    :return: Engine de connexion à la base
    """
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.environ['POSTGRES_HOST']}:{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url, pool_pre_ping=True)