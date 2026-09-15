import duckdb
from sqlalchemy import text

from src.config import timer, SCRIPT_CREATION
from src.data.db.connection import get_engine
from src.data.db.contraints import drop_constraints, restore_constraints
from src.data.db.insert import insert_all_in_db
from src.data.extract.dedup import create_produits_code_clean, create_nutriments_extraits

JUNCTION_TABLES = ["produits_categories", "produits_labels", "produits_marques", "produits_origines", "produits_nutriments_secondaires","produits_additifs","produits_ingredients", "valeurs_nutritionnelles"]
"""Tables de jonction dont on retire FK+PK pendant le COPY (cf. docs/contraintes)."""

@timer
def create_tables() -> None :
    """
    Crée les tables à partir du script de création
    :return:
    """
    print("Création des tables")
    with open(SCRIPT_CREATION, "r") as f:
        sql_script = f.read()

    with get_engine().begin() as conn:
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))

@timer
def main():
    print("Début du chargement des données")
    conn = duckdb.connect()
    create_tables()
    create_produits_code_clean(conn)
    create_nutriments_extraits(conn)
    temp = get_engine()
    with temp.begin() as index_conn :
        rows = drop_constraints(index_conn, JUNCTION_TABLES)

    insert_all_in_db(conn_duckdb=conn)

    restore_constraints(temp, rows)
    print("Fin du chargement des données")

if __name__=="__main__":
    main()