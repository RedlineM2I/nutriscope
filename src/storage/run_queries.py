"""Contrôles de qualité SQL (DuckDB) sur le Parquet partitionné.

Le script lit les requêtes de `controles.sql` (une par marqueur `-- @nom: xxx`),
les exécute sur une vue `produits` qui pointe vers le Parquet partitionné le plus
récent, et écrit leurs résultats dans un rapport Markdown.
Les chemins `SQL_FILE` et `REPORT` sont relatifs au dossier courant (`src/storage`).

Données : © Open Food Facts contributors, ODbL.
"""
import re
from pathlib import Path
import duckdb

from src.outputs import latest_partitioned

SQL_FILE = Path("../sql/controles.sql")
PARQUET_GLOB = Path(f"{latest_partitioned()}/**/*.parquet")  # sortie la plus récente du pipeline
REPORT = Path("../../docs/data/controle.md")
MARKER = re.compile(r"^--\s*@nom:\s*(\w+)\s*$", re.MULTILINE)


def load_queries(sql_text: str) -> dict[str, str]:
    """Découpe le fichier SQL sur les marqueurs `-- @nom: xxx`.

    Args:
        sql_text: contenu du fichier SQL.

    Returns:
        Requêtes indexées par leur nom (le `xxx` du marqueur).
    """
    parts = MARKER.split(sql_text)  # [avant, nom1, sql1, nom2, sql2, ...]
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def to_markdown(title: str, columns: list[str], rows: list[tuple]) -> str:
    """Met en forme le résultat d'une requête en section Markdown (titre + tableau).

    Args:
        title: titre de la section (nom de la requête).
        columns: noms des colonnes du résultat.
        rows: lignes du résultat.

    Returns:
        Section Markdown, terminée par un saut de ligne.
    """
    def cell(v: object) -> str:
        """Convertit une valeur en texte, avec `|` échappé pour ne pas casser le tableau."""
        return str(v).replace("|", "\\|")

    lines = [f"## {title}", "", "| " + " | ".join(columns) + " |",
             "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def run(con: duckdb.DuckDBPyConnection, queries: dict[str, str]) -> str:
    """Exécute chaque requête et assemble le rapport Markdown complet.

    Args:
        con: connexion DuckDB où la vue `produits` est déjà créée.
        queries: requêtes indexées par leur nom.

    Returns:
        Contenu du rapport Markdown.
    """
    out = ["# Contrôles de qualité (DuckDB sur Parquet)", "",
           "Données : © Open Food Facts contributors, ODbL", ""]
    for name, sql in queries.items():
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        out.append(to_markdown(name, cols, cur.fetchall()))
    return "\n".join(out)


def main() -> None:
    """Crée la vue `produits`, exécute les contrôles et écrit le rapport dans `REPORT`."""
    con = duckdb.connect()
    con.execute(
        f"CREATE VIEW produits AS "
        f"SELECT * FROM read_parquet('{PARQUET_GLOB}', hive_partitioning=true)"
    )
    queries = load_queries(SQL_FILE.read_text(encoding="utf-8"))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(run(con, queries), encoding="utf-8")
    print(f"{len(queries)} requêtes exécutées → {REPORT}")


if __name__ == "__main__":
    main()