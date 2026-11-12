import re
from pathlib import Path
import duckdb

from src.outputs import latest_partitioned

SQL_FILE = Path("../sql/controles.sql")
PARQUET_GLOB = Path(f"{latest_partitioned()}/**/*.parquet")  # sortie la plus récente du pipeline
REPORT = Path("../../docs/data/controle.md")
MARKER = re.compile(r"^--\s*@nom:\s*(\w+)\s*$", re.MULTILINE)


def load_queries(sql_text: str) -> dict[str, str]:
    """Découpe le fichier SQL sur les marqueurs `-- @nom: xxx`."""
    parts = MARKER.split(sql_text)  # [avant, nom1, sql1, nom2, sql2, ...]
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def to_markdown(title: str, columns: list[str], rows: list[tuple]) -> str:
    def cell(v: object) -> str:
        return str(v).replace("|", "\\|")

    lines = [f"## {title}", "", "| " + " | ".join(columns) + " |",
             "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def run(con: duckdb.DuckDBPyConnection, queries: dict[str, str]) -> str:
    out = ["# Contrôles de qualité (DuckDB sur Parquet)", "",
           "Données : © Open Food Facts contributors, ODbL", ""]
    for name, sql in queries.items():
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        out.append(to_markdown(name, cols, cur.fetchall()))
    return "\n".join(out)


def main() -> None:
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