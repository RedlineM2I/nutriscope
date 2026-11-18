"""Mise à plat du Parquet nettoyé en tables temporaires DuckDB (produits et tags).

Les tables temporaires n'existent que dans la connexion qui les crée : la même
connexion doit ensuite servir à `RelationalReader` et au chargement PostgreSQL.
"""
from _duckdb import DuckDBPyConnection

from pathlib import Path

from src.config import Tag

class FlatToRelational:
    """Découpe le Parquet nettoyé en tables temporaires relationnelles.

    Attributes:
        conn: connexion DuckDB qui porte les tables temporaires.
        source: Parquet nettoyé à découper.
    """

    def __init__(self, conn: DuckDBPyConnection, source: Path):
        """Initialise le découpage.

        Args:
            conn: connexion DuckDB, à partager avec le chargement en base.
            source: Parquet nettoyé à découper (le même que celui du Parquet
                partitionné).
        """
        self.conn = conn
        self.source = source
        
    def create_products(self):
        """Crée la table temporaire `products` à partir du fichier parquet.

        Chaque produit reçoit un identifiant `id` (numéro de ligne).
        """
        self.conn.sql(f"""
            CREATE OR REPLACE TEMP TABLE products AS
            SELECT row_number() over () as id, *
            FROM '{self.source}'
        """)

    def create_product_relations(self, field: Tag):
        """Crée une table temporaire des relations entre les produits et un champ de tags.

        La méthode effectue les étapes suivantes :
        1. Sélectionne les id des produits et les noms associés au champ (par
           exemple 'category'), un nom par ligne (`UNNEST`).
        2. Attribue avec `DENSE_RANK()` un identifiant unique à chaque nom, dans
           l'ordre alphabétique.
        3. Exclut les noms vides ou NULL.
        4. Exécute la requête sur la connexion DuckDB (table `products` requise,
           voir `create_products`).

        La table temporaire `products_{field.plural}` a les colonnes :
        - `product_id` : l'id du produit ;
        - `{field}_id` : l'identifiant unique du nom (ex. `category_id`) ;
        - `name` : le nom du tag.

        Cette table donne une relation claire entre les produits et leurs tags,
        et sert ensuite à construire le référentiel et la table de liaison.

        Args:
            field: champ de tags pour lequel créer la relation.
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
