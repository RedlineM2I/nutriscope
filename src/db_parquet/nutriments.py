"""Extraction des nutriments (principaux et secondaires) depuis la table DuckDB `products`."""
from duckdb import DuckDBPyConnection
from pandas import DataFrame


def get_nutriments(conn_duckdb: DuckDBPyConnection) -> DataFrame:
    """Extrait les nutriments principaux de la table DuckDB `products`.

    Les noms de colonnes avec tiret sont renommés avec des tirets bas, pour
    PostgreSQL (ex. `energy-kcal_100g` -> `energy_kcal_100g`).

    Args:
        conn_duckdb: connexion à la base DuckDB.

    Returns:
        DataFrame des nutriments principaux, une ligne par produit.
    """
    return conn_duckdb.sql("""
           SELECT id as product_id,
                  "energy-kcal_100g" AS energy_kcal_100g,
                  sugars_100g,
                  carbohydrates_100g,
                  fat_100g,
                  "saturated-fat_100g" AS saturated_fat_100g,
                  salt_100g,
                  sodium_100g,
                  proteins_100g,
                  fiber_100g,
                  fruits_nuts_100g,
                  "fruits-vegetables-legumes_100g" AS fruits_legumes_100g
           FROM products
           """).df()

def get_secondary_nutrients(conn_duckdb: DuckDBPyConnection) -> DataFrame :
    """Extrait les nutriments secondaires de la table DuckDB `products`.

    La liste `nutriments_secondaires` est dépliée (une ligne par produit et
    nutriment) ; les nutriments sans valeur pour 100 g sont écartés.

    Args:
        conn_duckdb: connexion à la base DuckDB.

    Returns:
        DataFrame des nutriments secondaires (`product_id`, `name`,
        `value_100g`, `unit`).
    """
    return conn_duckdb.sql("""
        SELECT id               as product_id,
                nutriment.name   AS name,
                nutriment."100g" AS value_100g,
                nutriment.unit   AS unit
        FROM (SELECT id, UNNEST(nutriments_secondaires) AS nutriment
                FROM products)
        WHERE nutriment."100g" IS NOT NULL
    """).df()


def get_secondary_nutrients_link_table(conn_duckdb: DuckDBPyConnection) -> tuple[DataFrame, DataFrame]:
    """Crée la table des nutriments secondaires et sa table de liaison.

    Args:
        conn_duckdb: connexion à la base DuckDB.

    Returns:
        Le DataFrame des nutriments secondaires (`id`, `name`, `unit`) et le
        DataFrame de la table de liaison (`product_id`, `nutrient_id`,
        `value_100g`).
    """
    df_secondary_nutrients = get_secondary_nutrients(conn_duckdb)
    id_nm_unit = df_secondary_nutrients[["name", "unit"]].drop_duplicates(subset="name").reset_index(
        drop=True).reset_index(names="id")
    # Jointure sur le nom seul : le référentiel garde une seule unité par nutriment
    link_table = df_secondary_nutrients.merge(id_nm_unit[["id", "name"]], on="name")[["product_id", "id", "value_100g"]]
    link_table = link_table.rename(columns={"id": "nutrient_id"}).drop_duplicates(
        subset=["product_id", "nutrient_id"])
    return id_nm_unit, link_table
