import duckdb
import pandas as pd
from sqlalchemy import text

from src.config import timer
from src.data.db.connection import get_engine
from src.data.db.insert import insert_all_in_db
from src.data.extract.dedup import create_produits_code_clean

SCRIPT_CREATION = "./db/create_tables.sql"

@timer
def create_tables() :
    print("Création des tables")
    with open(SCRIPT_CREATION, "r") as f:
        sql_script = f.read()

    with get_engine().begin() as conn:
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))

def main():
    conn = duckdb.connect()
    create_tables()
    create_produits_code_clean(conn)
    insert_all_in_db(conn_duckdb=conn)

if __name__=="__main__":
    main()