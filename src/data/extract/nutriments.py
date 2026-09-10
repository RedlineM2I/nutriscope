from pandas.core.interchange.dataframe_protocol import DataFrame


def get_nutriments(conn_duckdb) -> DataFrame:
    """
    Extrait les nutriments de la base DuckDB
    :param conn_duckdb: Connexion à la base DuckDB
    :return: Dataframe des nutriments principaux
    """
    return conn_duckdb.sql("""
           SELECT code as produit_code,
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

def get_secondary_nutriments(conn_duckdb) -> DataFrame :
    """
    Extrait les nutriments secondaires de la base DuckDB
    :param conn_duckdb: Connexion à la base DuckDB
    :return: Dataframe des nutriments secondaires
    """
    return conn_duckdb.sql("""
        SELECT
            code as produit_code,
            nutriment.name AS nom,
            nutriment."100g" AS valeur_100g,
            nutriment.unit AS unite
        FROM (
            SELECT code, UNNEST(nutriments_secondaires) AS nutriment
            FROM nutriments_extraits
        )
    """).df()