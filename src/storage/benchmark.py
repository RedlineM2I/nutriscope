"""Benchmark de trois moteurs (pandas/Parquet, DuckDB/Parquet, PostgreSQL).

Lancé sans argument, le script mesure chaque couple (moteur, requête) dans un
sous-processus neuf et écrit le rapport Markdown. Avec `--single`, il exécute
une seule mesure (c'est ce que font les sous-processus).

Données : © Open Food Facts contributors, ODbL.
"""
import argparse
import json
import statistics
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from config import BASE_DIR
from src.config import PARQUET_CLEAN_BY_FOOD_GROUP, PARQUET_CLEAN_DATASET

PARTITIONED_GLOB = Path(PARQUET_CLEAN_BY_FOOD_GROUP + "/**/*.parquet")
REPORT_PATH = Path(f"{BASE_DIR.parent}/docs/data/benchmark.md")
FOOD_GROUP = "sugary-snacks"  # à remplacer par un food_group réel du jeu
TOP_N = 20
REPETITIONS = 3

Rows = list[Sequence]


def peak_memory_mb() -> float:
    """Retourne le pic de mémoire (RSS) du processus courant, en Mo.

    L'unité de `ru_maxrss` dépend de l'OS (octets sous macOS, Ko sous Linux) ;
    sous Windows, on passe par psutil car `resource` n'existe pas.
    """
    if sys.platform == "win32":
        import psutil
        return psutil.Process().memory_info().peak_wset / 1e6
    import resource
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / 1e6 if sys.platform == "darwin" else value / 1e3


def run_postgres(sql: str) -> Rows:
    """Exécute une requête SQL sur PostgreSQL et retourne les lignes en tuples.

    Les imports sont locaux pour ne pas gonfler la mémoire mesurée des autres moteurs.
    """
    from sqlalchemy import text
    from src.db_psql.connection import get_engine

    with get_engine().connect() as conn:
        return [tuple(row) for row in conn.execute(text(sql)).fetchall()]


# ---------- Requête 1 : agrégat par rayon ----------
def pandas_aggregate() -> Rows:
    """Moyenne des sucres et du sel par rayon, avec pandas sur le Parquet complet."""
    import pandas as pd

    df = pd.read_parquet(
        PARQUET_CLEAN_DATASET,
        columns=["code", "food_group", "sugars_100g", "salt_100g"],
    )
    result = (
        df.groupby("food_group")
        .agg(n=("code", "size"), sugars=("sugars_100g", "mean"), salt=("salt_100g", "mean"))
        .reset_index()
        .sort_values(["n", "food_group"], ascending=[False, True])
    )
    return result.values.tolist()


def duckdb_aggregate() -> Rows:
    """Même agrégat avec DuckDB sur le Parquet partitionné."""
    import duckdb

    return duckdb.sql(f"""
        SELECT food_group, count(*) n, avg(sugars_100g), avg(salt_100g)
        FROM read_parquet('{PARTITIONED_GLOB}', hive_partitioning=true)
        GROUP BY food_group ORDER BY n DESC, food_group""").fetchall()


def postgres_aggregate() -> Rows:
    """Même agrégat sur la base PostgreSQL (jointures produits/rayons/nutriments)."""
    return run_postgres("""
        SELECT f.name, count(*) n, avg(nv.sugars_100g), avg(nv.salt_100g)
        FROM products p
        JOIN foodgroups f ON f.id = p.foodgroup_id
        JOIN nutritional_values nv ON nv.product_id = p.id
        GROUP BY f.name ORDER BY n DESC, f.name""")


# ---------- Requête 2 : filtre et tri ----------
def pandas_filter() -> Rows:
    """Les TOP_N produits les plus sucrés du rayon FOOD_GROUP, avec pandas."""
    import pandas as pd

    df = pd.read_parquet(
        PARQUET_CLEAN_DATASET,
        columns=["code", "product_name", "food_group", "sugars_100g"],
    )
    top = (
        df[df.food_group == FOOD_GROUP]
        .sort_values(["sugars_100g", "code"], ascending=[False, True])
        .head(TOP_N)
    )
    return top[["code", "sugars_100g"]].values.tolist()


def duckdb_filter() -> Rows:
    """Les TOP_N produits les plus sucrés du rayon FOOD_GROUP, avec DuckDB."""
    import duckdb

    return duckdb.sql(f"""
        SELECT code, sugars_100g
        FROM read_parquet('{PARTITIONED_GLOB}', hive_partitioning=true)
        WHERE food_group = '{FOOD_GROUP}' AND sugars_100g IS NOT NULL
        ORDER BY sugars_100g DESC, code LIMIT {TOP_N}""").fetchall()


def postgres_filter() -> Rows:
    """Les TOP_N produits les plus sucrés du rayon FOOD_GROUP, avec PostgreSQL."""
    return run_postgres(f"""
        SELECT p.code, nv.sugars_100g
        FROM products p
        JOIN foodgroups f ON f.id = p.foodgroup_id
        JOIN nutritional_values nv ON nv.product_id = p.id
        WHERE f.name = '{FOOD_GROUP}' AND nv.sugars_100g IS NOT NULL
        ORDER BY nv.sugars_100g DESC, p.code LIMIT {TOP_N}""")

GRADES_SQL = "('a', 'b', 'c', 'd', 'e')"

# ---------- Requête 3 : agrégat à forte cardinalité ----------
def pandas_brand_completeness() -> Rows:
    """Top TOP_N des marques par nombre de produits, avec % de Nutri-Score a-e (pandas)."""
    import pandas as pd

    df = pd.read_parquet(PARQUET_CLEAN_DATASET, columns=["brands_tags", "nutriscore_grade"])
    # Même règle que la conversion Parquet : première marque de la liste
    df["brand"] = df["brands_tags"].map(lambda t: t[0] if t is not None and len(t) else None)
    df = df.dropna(subset=["brand"])
    df["has_grade"] = df["nutriscore_grade"].isin(["a", "b", "c", "d", "e"])
    result = (
        df.groupby("brand")
        .agg(n=("brand", "size"), grade_pct=("has_grade", "mean"))
        .reset_index()
        .sort_values(["n", "brand"], ascending=[False, True])
        .head(TOP_N)
    )
    result["grade_pct"] = (result["grade_pct"] * 100).round(2)
    return result.values.tolist()


def duckdb_brand_completeness() -> Rows:
    """Même agrégat avec DuckDB sur le Parquet partitionné (colonne `brand`)."""
    import duckdb

    return duckdb.sql(f"""
        SELECT brand, count(*) n,
               round(100.0 * count(*) FILTER (WHERE nutriscore_grade IN {GRADES_SQL}) / count(*), 2)
        FROM read_parquet('{PARTITIONED_GLOB}', hive_partitioning=true)
        WHERE brand IS NOT NULL
        GROUP BY brand ORDER BY n DESC, brand LIMIT {TOP_N}""").fetchall()


def postgres_brand_completeness() -> Rows:
    """Même agrégat sur PostgreSQL (jointure produits/marques)."""
    return run_postgres(f"""
        SELECT b.name, count(*) n,
               round(100.0 * count(*) FILTER (WHERE p.nutriscore_grade IN {GRADES_SQL}) / count(*), 2)
        FROM products p
        JOIN products_brands pb ON pb.product_id = p.id
        JOIN brands b ON b.id = pb.brand_id
        GROUP BY b.name ORDER BY n DESC, b.name LIMIT {TOP_N}""")

def baseline() -> Rows:
    """Mesure de référence : poids de l'interpréteur et des imports seuls."""
    import duckdb, pandas, psycopg2  # noqa: F401
    return []


RUNNERS: dict[tuple[str, str], Callable[[], Rows]] = {
    ("pandas_parquet", "aggregate"): pandas_aggregate,
    ("duckdb_parquet", "aggregate"): duckdb_aggregate,
    ("postgres", "aggregate"): postgres_aggregate,
    ("pandas_parquet", "filter"): pandas_filter,
    ("duckdb_parquet", "filter"): duckdb_filter,
    ("postgres", "filter"): postgres_filter,
    ("pandas_parquet", "brand_completeness"): pandas_brand_completeness,
    ("duckdb_parquet", "brand_completeness"): duckdb_brand_completeness,
    ("postgres", "brand_completeness"): postgres_brand_completeness,
    ("-", "baseline"): baseline,
}


def run_single(engine: str, query: str) -> None:
    """Exécute une mesure et affiche le résultat en JSON sur la sortie standard."""
    start = time.perf_counter()
    rows = RUNNERS[(engine, query)]()
    elapsed = time.perf_counter() - start
    print(json.dumps({
        "seconds": elapsed,
        "rss_mb": peak_memory_mb(),
        "n_rows": len(rows),
        "head": [list(row) for row in rows[:3]],
    }, default=str))


def measure(engine: str, query: str, repetitions: int = REPETITIONS) -> dict:
    """Lance `repetitions` sous-processus neufs ; retourne la médiane des temps et le pic mémoire max."""
    results = []
    for _ in range(repetitions):
        proc = subprocess.run(
            [sys.executable, __file__, "--single", engine, query],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"{engine}/{query} a échoué :\n{proc.stderr}")
        results.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    return {
        "seconds": statistics.median(r["seconds"] for r in results),
        "rss_mb": max(r["rss_mb"] for r in results),
        "n_rows": results[0]["n_rows"],
        "head": results[0]["head"],
    }


def write_report(measures: dict[str, dict]) -> None:
    """Écrit le tableau des mesures au format Markdown dans REPORT_PATH."""
    lines = [
        "# Benchmark", "",
        "Données : © Open Food Facts contributors, ODbL", "",
        "| Moteur / requête | Temps médian (s) | Pic mémoire (Mo) | Lignes |",
        "|---|---|---|---|",
    ]
    for name, m in measures.items():
        lines.append(f"| {name} | {m['seconds']:.2f} | {m['rss_mb']:.0f} | {m['n_rows']} |")
    # REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    """Point d'entrée : mesure unique (`--single`) ou benchmark complet avec rapport."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--single", nargs=2, metavar=("ENGINE", "QUERY"))
    args = parser.parse_args()
    if args.single:
        run_single(*args.single)
    else:
        write_report({f"{e}/{q}": measure(e, q) for e, q in RUNNERS})


if __name__ == "__main__":
    main()