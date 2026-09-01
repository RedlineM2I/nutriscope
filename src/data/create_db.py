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
    query = f"""
        SELECT
            code,
            REPLACE(COALESCE(
            list_extract(list_filter(product_name, x -> x.lang = 'fr'),   1)."text",
            list_extract(list_filter(product_name, x -> x.lang = 'main'), 1)."text",
            list_extract(list_filter(product_name, x -> x.lang = 'en'),   1)."text"), chr(0), '')
            AS product_name,
            quantity,
            nutrition_data_per,
            nutriscore_grade,
            nutriscore_score,
            nova_group,
            completeness,
            environmental_score_grade,
            environmental_score_score
        FROM '{FOOD_FR_PARQUET}'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY code ORDER BY completeness DESC) = 1 --Regroupe par code bar identique et choisi celui qui a un meilleur taux de complétude
    """
    df = duckdb.sql(query).df()
    insert_in_db(df, "produits")

def insert_categories():
    df = duckdb.sql(f"SELECT DISTINCT UNNEST(categories_tags) AS nom FROM '{FOOD_FR_PARQUET}'").df()
    df = extract_lang(df, "nom")
    insert_in_db(df, "categories")

def insert_origines():
    df = duckdb.sql(f"SELECT DISTINCT UNNEST(origins_tags) AS nom FROM '{FOOD_FR_PARQUET}'").df()
    df = extract_lang(df, "nom")
    insert_in_db(df, "origines")

def insert_additifs():
    df = duckdb.sql(f"SELECT DISTINCT UNNEST(additives_tags) AS nom FROM '{FOOD_FR_PARQUET}'").df()
    df = extract_lang(df,"nom")
    insert_in_db(df,"additifs")

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