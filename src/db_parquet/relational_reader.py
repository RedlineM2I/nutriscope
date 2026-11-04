import pandas as pd

from src.config import Tag

# 'unknown' n'est qu'une clé de partition : ces produits auront foodgroup_id NULL
FOODGROUPS_QUERY = """
    SELECT DENSE_RANK() OVER (ORDER BY food_group) AS id, food_group AS name
    FROM (SELECT DISTINCT food_group FROM products WHERE food_group <> 'unknown')
"""

class RelationalReader:
    def __init__(self, conn):
        self.conn = conn


    def get_foodgroups(self) -> pd.DataFrame:
        return self.conn.sql(f"{FOODGROUPS_QUERY} ORDER BY id").df()


    def get_products(self) -> pd.DataFrame:
        # Les slugs main_category et food_group sont remplacés par les ids de leurs référentiels
        query = f"""
            WITH categories AS (
                SELECT DISTINCT name, {Tag.CATEGORY}_id AS id FROM products_{Tag.CATEGORY.plural}
            ),
            foodgroups AS ({FOODGROUPS_QUERY})
            SELECT
                p.id,
                p.code,
                p.product_name,
                c.id AS main_category,
                f.id AS foodgroup_id,
                p.nutrition_data_per,
                p.nutriscore_grade,
                p.nutriscore_score,
                p.nova_group,
                p.completeness,
                p.environmental_score_grade,
                p.environmental_score_score,
                -- epoch en secondes → TIMESTAMP, comme dans storage/convert_parquet.py
                to_timestamp(p.last_modified_t)::TIMESTAMP AS last_modified_t
            FROM products p
            LEFT JOIN categories c ON c.name = p.main_category
            LEFT JOIN foodgroups f ON f.name = p.food_group
            ORDER BY p.id
        """

        return self.conn.sql(query).df()


    def get_tags(self, field: Tag):
        query = f"""
            SELECT DISTINCT {field}_id AS id, name
            FROM products_{field.plural}
            ORDER BY id;
        """

        return self.conn.sql(query).df()


    def get_product_relations(self, field: Tag):
        query = f"""
            SELECT DISTINCT product_id, {field}_id
            FROM products_{field.plural};
        """

        return self.conn.sql(query).df()
