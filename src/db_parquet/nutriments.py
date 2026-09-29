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
                  energie_100g,
                  sucres_100g,
                  glucides_100g,
                  matieres_grasses_100g,
                  acides_gras_satures_100g,
                  sel_100g,
                  proteines_100g,
                  fibres_100g,
                  fruits_nuts_100g,
                  fruits_legumes_100g
           FROM nutriments_extraits
           """).df()

def get_secondary_nutriments(conn_duckdb: DuckDBPyConnection) -> DataFrame :
    """
    Extrait les nutriments secondaires de la base DuckDB
    :param conn_duckdb: Connexion à la base DuckDB
    :return: Dataframe des nutriments secondaires
    """
    return conn_duckdb.sql("""
                           SELECT id               as product_id,
                                  nutriment.name   AS name,
                                  nutriment."100g" AS valeur_100g,
                                  nutriment.unit   AS unit
                           FROM (SELECT id, UNNEST(nutriments_secondaires) AS nutriment
                                 FROM nutriments_extraits)
                           """).df()


def get_secondary_nutriments_link_table(conn_duckdb: DuckDBPyConnection) -> tuple[DataFrame, DataFrame]:
    """
    Crée la table des nutriments secondaires et sa table de liaison
    :param conn_duckdb: Connexion à la base DuckDB
    :return: DataFrame des nutriments secondaire et DataFrame de la table de liaison
    """
    df_secondary_nutriments = get_secondary_nutriments(conn_duckdb)
    id_nm_unit = df_secondary_nutriments[["name", "unit"]].drop_duplicates(subset="name").reset_index(
        drop=True).reset_index(names="id")
    link_table = df_secondary_nutriments.merge(id_nm_unit, on=["name", "unit"])[["product_id", "id", "valeur_100g"]]
    link_table = link_table.rename(columns={"id": "nutriment_id"}).drop_duplicates(
        subset=["product_id", "nutriment_id"])
    return id_nm_unit, link_table
