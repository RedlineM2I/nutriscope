import duckdb
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import logging

#Fichier parquet à utiliser
FOOD_FR_PARQUET = "../../data/food_france.parquet"
SCRIPT_CREATION = "../../data/create_tables.sql"

# Environnement SQL
load_dotenv()

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_engine():
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.environ['POSTGRES_HOST']}:{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url, pool_pre_ping=True)

def extract_lang(df: pd.DataFrame, name: str) -> pd.DataFrame :
    new_df = pd.DataFrame()
    new_df[name] = df[name].str.replace(r"^([a-zA-Z]{2}):", "", regex=True).drop_duplicates()
    return new_df

def insert_in_db(df: pd.DataFrame, name: str) :
    engine = get_engine()
    try:
        with engine.begin() as conn:  # commit automatique si succès, rollback si erreur
            df.to_sql(name=name, con=conn, if_exists="append", index=False)
            logger.info(f"{len(df)} lignes importées avec succès")
    except Exception as e:
        logger.error(f"Échec de l'import ({len(df)} lignes) : {e}")

def insert_produits():
    pass

def insert_categories():
    pass

def insert_origines():
    pass

def insert_additifs():
    pass

def insert_images():
    pass

def insert_nutriments():
    pass

def insert_marques():
    pass

def insert_labels():
    pass

def insert_ingredients():
    pass

def create_tables() :
    with open(SCRIPT_CREATION, "r") as f:
        sql_script = f.read()

    with get_engine().begin() as conn:
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))

def main():
    create_tables()
    insert_produits()
    insert_categories()
    insert_labels()
    insert_images()
    insert_marques()
    insert_additifs()
    insert_origines()
    insert_nutriments()
    insert_ingredients()

if __name__=="__main__":
    main()