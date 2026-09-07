FOOD_FR_PARQUET = "../../data/food_france.parquet"

def create_produits_code_clean(conn) :
    conn.sql(f"""
        CREATE OR REPLACE TEMP TABLE produits_dedup AS
        SELECT *
        FROM '{FOOD_FR_PARQUET}'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY code ORDER BY completeness DESC) = 1
    """)