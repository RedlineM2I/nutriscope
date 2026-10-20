import json, shutil
from pathlib import Path
import duckdb

from config import KEY_NUTRIENTS
from src.config import PARQUET_CLEAN_DATASET, PARQUET_CLEAN_BY_FOOD_GROUP, SCHEMA_PRODUIT_JSON

SCHEMA_COLUMNS = {
    "code": ("VARCHAR", "un code-barres n'est pas un nombre, on garde les zéros de tête"),
    "product_name": ("VARCHAR", "texte libre, tel que dans le nettoyé"),
    "food_group": ("VARCHAR", "slug de la catégorie, sert de clé de partition ('unknown' si vide)"),
    "main_category": ("VARCHAR", "catégorie principale, texte normalisé"),
    "additives_n": ("SMALLINT", "nombre d'additifs, petit entier positif"),
    "nutriscore_score": ("SMALLINT", "intervalle réel d'environ -15 à 40, tient sur 2 octets"),
    "last_modified_t": ("TIMESTAMP", "epoch en secondes converti via to_timestamp"),
    "nutriscore_grade": ("VARCHAR", "grade a-e, unknown, not-applicable ou NULL"),
    "nova_group": ("TINYINT", "4 valeurs (1 à 4), 1 octet suffit"),
}


def _create_request() -> str:
    columns = [
        "CAST(code AS VARCHAR) AS code",
        "product_name",
        "food_group",
        "main_category",
        "CAST(len(additives_tags) AS SMALLINT) AS additives_n",
        "CAST(nutriscore_score AS SMALLINT) AS nutriscore_score",
        "to_timestamp(CAST(last_modified_t AS BIGINT))::TIMESTAMP AS last_modified_t",
        "nutriscore_grade",
        "CAST(nova_group AS TINYINT) AS nova_group",
        *(f'CAST("{n}" AS FLOAT) AS "{n}"' for n in KEY_NUTRIENTS),
    ]
    select_clause = ",\n            ".join(columns)
    return f"""
        COPY (
            SELECT
            {select_clause}
            FROM read_parquet('{PARQUET_CLEAN_DATASET}')
        ) TO '{PARQUET_CLEAN_BY_FOOD_GROUP}' (FORMAT PARQUET, PARTITION_BY (food_group),
            COMPRESSION ZSTD, OVERWRITE_OR_IGNORE)
    """

def write_schema(n_rows: int, path=SCHEMA_PRODUIT_JSON):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)   # ← évite le plantage
    schema = {
        "partition": "food_group",
        "compression": "ZSTD",
        "rows": n_rows,
        "licence": "© Open Food Facts contributors, ODbL",
        "columns": {k: {"type": t, "why": w} for k, (t, w) in SCHEMA_COLUMNS.items()},
    }
    p.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")

def convert_parquet():
    if Path(PARQUET_CLEAN_BY_FOOD_GROUP).exists():
        shutil.rmtree(PARQUET_CLEAN_BY_FOOD_GROUP)  # rejouable, pas de partition orpheline
    Path(PARQUET_CLEAN_BY_FOOD_GROUP).parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    request = _create_request()
    con.execute(request)
    n = con.execute(
        f"SELECT count(*) FROM read_parquet('{PARQUET_CLEAN_BY_FOOD_GROUP}/**/*.parquet', hive_partitioning=true)"
    ).fetchone()[0]
    return n


if __name__ == "__main__":
    n = convert_parquet()
    write_schema(n)
