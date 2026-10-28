"""
Étapes du projet, appelées par main.py et par les tâches du DAG Airflow.

Chaque étape lit et écrit des fichiers (parquet) ou la base PostgreSQL : elle peut
donc tourner seule, dans son propre processus. Seules flatten_to_relational et
load_database partagent une connexion DuckDB (tables temporaires en mémoire) :
elles doivent être appelées l'une après l'autre dans le même processus.
"""

import os
import subprocess

from pathlib import Path
from duckdb import DuckDBPyConnection, connect

from src import cleaning, fetch_data
from src.config import EXPORT_PARQUET_DIR, PARQUET_CLEAN_DATASET, EXPORT_CLEANING_REPORT, Tag
from src.console import title2
from src.report import generate_report
from src.db_parquet.products import extract_products, get_products_from
from src.db_parquet.relational_reader import RelationalReader
from src.db_psql.connection import get_engine  # charge aussi le .env
from src.db_psql.constraints import drop_constraints, restore_constraints
from src.db_psql.insert import psql_insert_copy
from src.db_psql.schema import create_tables
from src.flat_to_relational import FlatToRelational
from src.config import ELEVATOR
from src.console import timer, title1
from src.music import background_music


JUNCTION_TABLES = [
    "products_categories", "products_labels", "products_brands", "products_origins",
    "products_secondary_nutrients", "products_additives", "products_ingredients", "nutritional_values"
]

# Ordre des règles : types, textes, doublons, unités, bornes, énergie, catégories, manquants.
# Les unités avant les bornes (un sel dérivé du sodium peut ensuite être borné) ;
# l'énergie après les bornes (le recalcul 4 / 4 / 9 s'appuie sur des macronutriments déjà plausibles).
CLEANING_RULES = [
    cleaning.set_column_types,
    cleaning.normalize_texts,
    cleaning.deduplicate_codes,
    cleaning.normalize_units,
    cleaning.limit_nutriments,
    cleaning.fix_energy,
    cleaning.handle_empty_categories,
    cleaning.missing_values_strategy,
]


@timer
def main():
    title1("Projet Nutriscope")

    with background_music(ELEVATOR, play=True):
        download()

    filter_country(country="en:france")

    clean(Path(EXPORT_CLEANING_REPORT))
    reset_database()

    # Les tables temporaires DuckDB vivent dans cette connexion : même connexion pour les deux étapes
    conn_duckdb = connect()
    flatten_to_relational(conn_duckdb)
    load_database(conn_duckdb)

    # export_to_parquet()


def download() -> None:
    """Télécharge le parquet complet d'OpenFoodFacts."""
    title2("Téléchargement du fichier parquet OpenFactFood")
    fetch_data.download()


def filter_country(country: str = "en:france") -> None:
    """Restreint le parquet aux colonnes utiles et aux produits vendus dans le pays."""
    title2("Filtre sur le périmètre du fichier parquet (colonnes sélectionnées et produits en France)")
    get_products_from(country=country)
    print("✔ food.parquet → food_france.parquet")


def clean(report_path : Path) -> None:
    """Applique les règles de nettoyage et exporte le résultat en parquet."""
    title2("Nettoyage des données")
    products = extract_products(conn=connect())
    before = products.copy()
    reports = []
    for rule in CLEANING_RULES:
        products, report = rule(products)
        reports.append(report)
        print(f"✔ {rule.__name__}")

    Path(PARQUET_CLEAN_DATASET).parent.mkdir(parents=True, exist_ok=True)
    products.to_parquet(PARQUET_CLEAN_DATASET)
    print(f"✔ products: DataFrame → {PARQUET_CLEAN_DATASET}")
    generate_report(before, products, reports, report_path)
    print(f"✔ Rapport Markdown → {str(report_path)}")


def reset_database() -> None:
    """Supprime puis recrée toutes les tables PostgreSQL."""
    title2("Réinitialisation de la base PostgreSQL")
    with get_engine().begin() as conn_psql:
        create_tables(conn_psql)
    print("✔ base réinitialisée")


def flatten_to_relational(conn_duckdb: DuckDBPyConnection) -> None:
    """Découpe le parquet nettoyé en tables temporaires DuckDB, au format du schéma PostgreSQL."""
    title2("Conversion du fichier parquet en tables relationnelles")
    flat_to_rel = FlatToRelational(conn=conn_duckdb)

    flat_to_rel.create_products()
    print("✔ products")
    for tag in Tag:
        flat_to_rel.create_product_relations(tag)
        print(f"✔ products_{tag.plural}")


def load_database(conn_duckdb: DuckDBPyConnection) -> None:
    """Charge dans PostgreSQL les tables temporaires créées par flatten_to_relational."""
    title2("Chargement des tables dans la base de données")
    rel_reader = RelationalReader(conn_duckdb)
    engine = get_engine()

    # Sans PK/FK sur les tables de liaison, le COPY n'a ni index à maintenir ni FK à vérifier.
    with engine.begin() as conn_psql:
        constraints = drop_constraints(conn_psql, JUNCTION_TABLES)

    with engine.begin() as conn_psql:
        products = rel_reader.get_products()
        products.to_sql("products", con=conn_psql, if_exists="append", index=False, method=psql_insert_copy)
        print("✔ products")

        # Table du tag (id, name) avant sa table de liaison, qui la référence
        for tag in Tag:
            df_tags = rel_reader.get_tags(tag)
            df_tags.to_sql(tag.plural, con=conn_psql, if_exists="append", index=False, method=psql_insert_copy)
            print(f"✔ {tag.plural}")

            df_relations = rel_reader.get_product_relations(tag)
            df_relations.to_sql(f"products_{tag.plural}", con=conn_psql, if_exists="append", index=False, method=psql_insert_copy)
            print(f"✔ products_{tag.plural}")

    # Après le commit des insertions : restore_constraints ouvre ses propres connexions
    title2("Application des contraintes")
    restore_constraints(engine, constraints)
    print("✔ contraintes restaurées")


def export_to_parquet(schema: str = "public") -> None:
    """Exporte chaque table PostgreSQL du schéma dans un fichier parquet."""
    title2("Exportation des tables vers des fichiers parquets")
    EXPORT_PARQUET_DIR.mkdir(parents=True, exist_ok=True)

    # Mêmes variables d'environnement que get_engine (POSTGRES_HOST diffère dans Docker)
    dsn = (
        f"host={os.environ['POSTGRES_HOST']} port={os.getenv('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ['POSTGRES_DB']} user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )

    conn = connect()
    conn.execute("INSTALL postgres; LOAD postgres;")
    conn.execute(f"ATTACH '{dsn}' AS src (TYPE postgres, READ_ONLY)")

    # Liste uniquement les tables du schéma (pas les tables système)
    tables = conn.execute(
        "SELECT table_name FROM duckdb_tables() "
        "WHERE database_name = 'src' AND schema_name = ?",
        [schema],
    ).fetchall()

    for (table,) in tables:
        path = (EXPORT_PARQUET_DIR / f"{table}.parquet").as_posix()
        conn.execute(
            f'COPY src."{schema}"."{table}" TO \'{path}\' (FORMAT parquet, COMPRESSION zstd)'
        )
        print(f"✔ {table} → {path}")

    conn.close()
    print(f"Export terminé : {len(tables)} tables")


if __name__ == "__main__":
    subprocess.call('cls', shell=True)
    main()
