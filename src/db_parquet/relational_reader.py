import pandas as pd

from src.config import Tag


class RelationalReader:
    def __init__(self, conn):
        self.conn = conn


    def get_products(self) -> pd.DataFrame:
        query = """
            SELECT
                id,
                code,
                product_name,
                -- main_category,
                -- foodgroup_id,
                nutrition_data_per,
                nutriscore_grade,
                nutriscore_score,
                nova_group,
                completeness,
                environmental_score_grade,
                environmental_score_score,
                -- last_modified_t
            FROM products
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
