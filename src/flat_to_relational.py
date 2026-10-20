from _duckdb import DuckDBPyConnection

from src.config import PARQUET_CLEAN_DATASET, PARQUET_FR, Tag

class FlatToRelational:
    def __init__(self, conn: DuckDBPyConnection):
        self.conn = conn
        
    def create_products(self):
        """
        Crée une table temporaire propre des produits à partir du fichier parquet
        :param conn: Connexion à la base duckdb
        :return:
        """
        self.conn.sql(f"""
            CREATE OR REPLACE TEMP TABLE products AS
            SELECT row_number() over () as id, *
            FROM '{PARQUET_CLEAN_DATASET}'
        """)

    def create_product_relations(self, field: Tag):
        query = f"""
            CREATE OR REPLACE TEMP TABLE products_{field.plural} AS
            SELECT DISTINCT
                product_id,
                DENSE_RANK() OVER (ORDER BY name) AS {field}_id,
                name
            FROM (
                -- Les tags arrivent déjà nettoyés par cleaning.normalize_texts
                SELECT id AS product_id, UNNEST({field.plural}_tags) AS name
                FROM products
            )
            WHERE name IS NOT NULL AND name <> '';
        """
        self.conn.sql(query)
