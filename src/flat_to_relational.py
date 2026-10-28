from _duckdb import DuckDBPyConnection

from src.config import PARQUET_CLEAN_DATASET, Tag

class FlatToRelational:

    def __init__(self, conn: DuckDBPyConnection):
        self.conn = conn
        
    def create_products(self):
        """
        Crée une table temporaire propre des produits à partir du fichier parquet
        :return:
        """
        self.conn.sql(f"""
            CREATE OR REPLACE TEMP TABLE products AS
            SELECT row_number() over () as id, *
            FROM '{PARQUET_CLEAN_DATASET}'
        """)

    def create_product_relations(self, field: Tag):
        """
            Crée une table temporaire contenant les relations entre produits et un champ spécifique.

            :param field: L'objet Tag représentant le champ pour lequel créer la relation.
            :type field: Tag

            La méthode effectue les étapes suivantes :
            1. Crée une requête SQL qui sélectionne les ID des produits et les noms associés à un champ spécifique (par exemple, 'category').
            2. Utilise `DENSE_RANK()` pour attribuer un identifiant unique à chaque catégorie ordonnées par le nom.
            3. Filtre les résultats pour exclure les noms vides ou None.
            4. Exécute la requête SQL sur la connexion DuckDB.

            La table temporaire 'products_{field.plural}' est créée avec les colonnes suivantes :
            - product_id: L'ID du produit.
            - {field}_id: Un identifiant unique attribué à chaque catégorie ordonnées par le nom.
            - name: Le nom de la catégorie.

            Cette méthode permet d'avoir une relation claire entre les produits et leurs catégories, facilitant les requêtes futures sur ces relations.
        """
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
