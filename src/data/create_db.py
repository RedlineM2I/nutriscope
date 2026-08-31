import duckdb
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

FOOD_FR_PARQUET = "../data/food_france.parquet"

load_dotenv()

def get_engine():
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@"
        f"{os.environ['POSTGRES_HOST']}:{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url, pool_pre_ping=True)

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


def main():
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