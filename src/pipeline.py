"""
Étapes du projet, appelées par main.py et par les tâches du DAG Airflow.

Chaque étape lit et écrit des fichiers (parquet) ou la base PostgreSQL : elle peut
donc tourner seule, dans son propre processus. Seules flatten_to_relational et
load_database partagent une connexion DuckDB (tables temporaires en mémoire) :
elles doivent être appelées l'une après l'autre dans le même processus.
"""

import os
import subprocess
import argparse
import time

from pathlib import Path
from duckdb import DuckDBPyConnection, connect

from src import cleaning, fetch_data
from src.config import PARQUET_FILE, PARQUET_FR, EXPORT_PARQUET_DIR, PARQUET_CLEAN_DATASET, EXPORT_CLEANING_REPORT, ELEVATOR, Tag
from src.console import timer, title1, title2
from src.report import generate_report
from src.db_parquet.nutriments import get_nutriments, get_secondary_nutrients_link_table
from src.db_parquet.products import extract_products, get_products_from
from src.db_parquet.relational_reader import RelationalReader
from src.db_psql.connection import get_engine  # charge aussi le .env
from src.db_psql.constraints import drop_constraints, restore_constraints
from src.db_psql.insert import psql_insert_copy
from src.db_psql.schema import create_tables
from src.flat_to_relational import FlatToRelational
from src.models import StepReport
from src.music import background_music


JUNCTION_TABLES = [
    "products_categories", "products_labels", "products_brands", "products_origins",
    "products_secondary_nutrients", "products_additives", "products_ingredients", "nutritional_values"
]

def parse_args() -> argparse.Namespace:
    """Lit les options de la ligne de commande (une seule action à la fois)."""
    parser = argparse.ArgumentParser(description="Traite des fichiers Parquet.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--download", action="store_true", help="Download the parquet file from the huggingface repository")
    group.add_argument("--clean", action="store_true", help="Apply all the cleaning rules to the dataset")
    group.add_argument("--load_database", action="store_true", help="Convert parquet file to a relational dataframes and load them into the database")
    group.add_argument("--extract_parquet", action="store_true", help="Extract a parquet file partioned by categorie")
    group.add_argument("--build_datasets", action="store_true", help="Create a dataset to exploit it in the ML phase")
    group.add_argument("--all", action="store_true", help="Run all the pipeline from the beginning")
    return parser.parse_args()

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

def step_download() -> StepReport:
    """Télécharge le brut puis le restreint à la France ; lignes = produits du périmètre."""
    start = time.perf_counter()
    with background_music(ELEVATOR, play=False):
        download()
    filter_country(country="en:france")
    rows = connect().execute(f"SELECT count(*) FROM read_parquet('{PARQUET_FR}')").fetchone()[0]
    return StepReport("download", time.perf_counter() - start, rows, [PARQUET_FILE, PARQUET_FR])

def step_clean() -> StepReport:
    """Nettoie le périmètre France ; lignes = produits conservés après la dernière règle."""
    start = time.perf_counter()
    conn_duckdb = connect()
    products = extract_products(conn_duckdb)
    rows = clean(products)
    return StepReport("clean", time.perf_counter() - start, rows, [PARQUET_CLEAN_DATASET, str(EXPORT_CLEANING_REPORT)])

def step_load_database() -> StepReport:
    """Recrée et remplit la base ; lignes = total inséré, tables de liaison comprises."""
    start = time.perf_counter()
    reset_database()
    # Les tables temporaires DuckDB vivent dans cette connexion : même connexion pour les deux étapes
    conn_duckdb = connect()
    flatten_to_relational(conn_duckdb)
    rows = load_database(conn_duckdb)
    return StepReport("load_database", time.perf_counter() - start, rows)


# Ordre d'exécution de --all ; la clé est le nom de l'option de la ligne de commande
STEPS = {
    "download": step_download,
    "clean": step_clean,
    "load_database": step_load_database,
}


@timer
def main():
    args = parse_args()
    title1("Projet Nutriscope")

    reports = [step() for name, step in STEPS.items() if args.all or getattr(args, name)]
    if not reports:
        print("Aucune étape lancée (option absente ou pas encore implémentée).")
    else:
        title2("Récapitulatif")
        for r in reports:
            print(f"✔ {r.step:<14} {r.duration:8.1f} s {r.rows:>10} lignes  {', '.join(r.files)}")

    # export_to_parquet()


@timer(label="Téléchargement du fichier parquet")
def download() -> None:
    """Télécharge le parquet complet d'OpenFoodFacts."""
    title2("Téléchargement du fichier parquet OpenFactFood")
    fetch_data.download()


@timer(label="Filtre sur le périmètre")
def filter_country(country: str = "en:france") -> None:
    """Restreint le parquet aux colonnes utiles et aux produits vendus dans le pays."""
    title2("Filtre sur le périmètre du fichier parquet (colonnes sélectionnées et produits en France)")
    get_products_from(country=country)
    print("✔ food.parquet → food_france.parquet")


@timer(label="Nettoyage")
def clean(products) -> int:
    """Applique les règles de nettoyage et exporte le résultat en parquet. Retourne le nombre de lignes finales."""
    title2("Nettoyage des données")
    before = products.copy()
    reports = []
    for rule in CLEANING_RULES:
        products, report = rule(products)
        reports.append(report)
        print(f"✔ {rule.__name__}")

    Path(PARQUET_CLEAN_DATASET).parent.mkdir(parents=True, exist_ok=True)
    products.to_parquet(PARQUET_CLEAN_DATASET)
    print(f"✔ products: DataFrame → {PARQUET_CLEAN_DATASET}")
    generate_report(before, products, reports, EXPORT_CLEANING_REPORT)
    print(f"✔ Rapport Markdown → {EXPORT_CLEANING_REPORT}")
    return reports[-1].lines_after


@timer(label="Réinitialisation de la base")
def reset_database() -> None:
    """Supprime puis recrée toutes les tables PostgreSQL."""
    title2("Réinitialisation de la base PostgreSQL")
    with get_engine().begin() as conn_psql:
        create_tables(conn_psql)
    print("✔ base réinitialisée")


@timer(label="Conversion en tables relationnelles")
def flatten_to_relational(conn_duckdb: DuckDBPyConnection) -> None:
    """Découpe le parquet nettoyé en tables temporaires DuckDB, au format du schéma PostgreSQL."""
    title2("Conversion du fichier parquet en tables relationnelles")
    flat_to_rel = FlatToRelational(conn=conn_duckdb)

    flat_to_rel.create_products()
    print("✔ products")
    for tag in Tag:
        flat_to_rel.create_product_relations(tag)
        print(f"✔ products_{tag.plural}")


@timer(label="Chargement des tables")
def load_database(conn_duckdb: DuckDBPyConnection) -> int:
    """Charge dans PostgreSQL les tables temporaires créées par flatten_to_relational. Retourne le total de lignes insérées."""
    title2("Chargement des tables dans la base de données")
    rel_reader = RelationalReader(conn_duckdb)
    engine = get_engine()
    total = 0

    def insert(df, table):
        nonlocal total
        df.to_sql(table, con=conn_psql, if_exists="append", index=False, method=psql_insert_copy)
        total += len(df)

    # Sans PK/FK sur les tables de liaison, le COPY n'a ni index à maintenir ni FK à vérifier.
    with engine.begin() as conn_psql:
        constraints = drop_constraints(conn_psql, JUNCTION_TABLES)

    with engine.begin() as conn_psql:
        products = rel_reader.get_products()
        insert(products, "products")
        print("✔ products")

        nutritional_values = get_nutriments(conn_duckdb)
        insert(nutritional_values, "nutritional_values")
        print("✔ nutritional_values")

        # Référentiel des nutriments secondaires avant sa table de liaison, qui le référence
        secondary_nutrients, products_secondary_nutrients = get_secondary_nutrients_link_table(conn_duckdb)
        insert(secondary_nutrients, "secondary_nutrients")
        print("✔ secondary_nutrients")
        insert(products_secondary_nutrients, "products_secondary_nutrients")
        print("✔ products_secondary_nutrients")

        # Table du tag (id, name) avant sa table de liaison, qui la référence
        for tag in Tag:
            df_tags = rel_reader.get_tags(tag)
            insert(df_tags, tag.plural)
            print(f"✔ {tag.plural}")

            df_relations = rel_reader.get_product_relations(tag)
            insert(df_relations, f"products_{tag.plural}")
            print(f"✔ products_{tag.plural}")

    # Après le commit des insertions : restore_constraints ouvre ses propres connexions
    title2("Application des contraintes")
    restore_constraints(engine, constraints)
    print("✔ contraintes restaurées")
    return total


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
    
