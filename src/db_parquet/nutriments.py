from duckdb import DuckDBPyConnection
from pandas.core.interchange.dataframe_protocol import DataFrame


def get_nutriments(conn_duckdb: DuckDBPyConnection) -> DataFrame:
    """
    Extrait les nutriments de la base DuckDB
    :param conn_duckdb: Connexion à la base DuckDB
    :return: Dataframe des nutriments principaux
    """
    return conn_duckdb.sql("""
           SELECT id as product_id,
                  energy_100g,
                  sugars_100g,
                  carbohydrates_100g,
                  fat_100g,
                  saturated_fat_100g,
                  salt_100g,
                  proteins_100g,
                  fiber_100g,
                  fruits_nuts_100g,
                  fruits_legumes_100g
           FROM nutriments_extraits
           """).df()

def get_secondary_nutrients(conn_duckdb: DuckDBPyConnection) -> DataFrame :
    """
    Extrait les nutriments secondaires de la base DuckDB
    :param conn_duckdb: Connexion à la base DuckDB
    :return: Dataframe des nutriments secondaires
    """
    return conn_duckdb.sql("""
                           SELECT id               as product_id,
                                  nutriment.name   AS name,
                                  nutriment."100g" AS value_100g,
                                  nutriment.unit   AS unit
                           FROM (SELECT id, UNNEST(nutriments_secondaires) AS nutriment
                                 FROM nutriments_extraits)
                           """).df()


def get_secondary_nutrients_link_table(conn_duckdb: DuckDBPyConnection) -> tuple[DataFrame, DataFrame]:
    """
    Crée la table des nutriments secondaires et sa table de liaison
    :param conn_duckdb: Connexion à la base DuckDB
    :return: DataFrame des nutriments secondaire et DataFrame de la table de liaison
    """
    df_secondary_nutrients = get_secondary_nutrients(conn_duckdb)
    id_nm_unit = df_secondary_nutrients[["name", "unit"]].drop_duplicates(subset="name").reset_index(
        drop=True).reset_index(names="id")
    link_table = df_secondary_nutrients.merge(id_nm_unit, on=["name", "unit"])[["product_id", "id", "value_100g"]]
    link_table = link_table.rename(columns={"id": "nutrient_id"}).drop_duplicates(
        subset=["product_id", "nutrient_id"])
    return id_nm_unit, link_table
