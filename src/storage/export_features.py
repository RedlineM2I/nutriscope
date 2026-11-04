import hashlib
import json
import subprocess

import duckdb
import pandas as pd
from _duckdb import DuckDBPyConnection
from pathlib import Path
from src.config import PARQUET_CLEAN_BY_FOOD_GROUP, BASE_DIR, TODAY

KEY_NUTRIENTS = [
    "energy-kcal_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g",
    "salt_100g",
]

def _info(unit: str, description: str, role: str, missing_policy: str) -> dict[str, str]:
    return {
        "unit": unit,
        "description": description,
        "role": role,
        "missing_policy": missing_policy,
    }

_NUTRIENT_POLICY = "none expected (filtered NOT NULL at export)"

COLUMN_INFO: dict[str, dict[str, str]] = {
    "code": _info("-", "Barcode (text, leading zeros kept)", "identifier", "none expected"),
    "food_group": _info("-", "Product category (partition key)", "feature", "'unknown' if empty"),
    "energy-kcal_100g": _info("kcal/100g", "Energy", "feature", _NUTRIENT_POLICY),
    "fat_100g": _info("g/100g", "Total fat", "feature", _NUTRIENT_POLICY),
    "saturated-fat_100g": _info("g/100g", "Saturated fat", "feature", _NUTRIENT_POLICY),
    "carbohydrates_100g": _info("g/100g", "Carbohydrates", "feature", _NUTRIENT_POLICY),
    "sugars_100g": _info("g/100g", "Sugars", "feature", _NUTRIENT_POLICY),
    "proteins_100g": _info("g/100g", "Proteins", "feature", _NUTRIENT_POLICY),
    "salt_100g": _info("g/100g", "Salt", "feature", _NUTRIENT_POLICY),
    "additives_n": _info("count", "Number of additives", "feature", "check; impute 0 if NULL"),
    "nova_group": _info("1-4", "Degree of processing (NOVA)", "feature",
                        "not filtered at export: impute (mode) + missing flag"),
    "sugars_to_carbs_ratio": _info("ratio", "sugars / carbohydrates", "feature",
                                   "NULL if carbohydrates = 0: impute 0 + flag"),
    "sat_fat_to_fat_ratio": _info("ratio", "saturated fat / fat", "feature",
                                  "NULL if fat = 0: impute 0 + flag"),
    "fat_energy_share": _info("ratio", "fat * 9 / energy-kcal", "feature",
                              "none expected (energy > 0 filtered)"),
    "nutriscore_score": _info("points", "Numeric Nutri-Score", "leakage_do_not_use_as_feature",
                              "none expected"),
    "nutriscore_grade": _info("a-e", "Nutri-Score grade", "target", "none (filtered a-e)"),
}

def read_partitioned_parquet(con: DuckDBPyConnection, req: str) -> pd.DataFrame :
    return con.execute(req).df()

def build_select(path: str = PARQUET_CLEAN_BY_FOOD_GROUP) -> str:
    """Return the SQL selecting the usable products for Nutri-Score prediction.

    Reads the hive-partitioned Parquet (food_group comes from the folder name).
    """
    # Les noms avec un tiret doivent être entre guillemets doubles en SQL.
    q = {n: f'"{n}"' for n in KEY_NUTRIENTS}
    not_null = " AND ".join(f"{c} IS NOT NULL" for c in q.values())

    return f"""
        SELECT
            code,
            food_group,
            {", ".join(q.values())},
            additives_n,
            nova_group,
            (sugars_100g / NULLIF(carbohydrates_100g, 0))::FLOAT AS sugars_to_carbs_ratio,
            ("saturated-fat_100g" / NULLIF(fat_100g, 0))::FLOAT AS sat_fat_to_fat_ratio,
            (fat_100g * 9 / NULLIF("energy-kcal_100g", 0))::FLOAT AS fat_energy_share,
            nutriscore_score,
            nutriscore_grade
        FROM read_parquet('{Path(f"{path}/**/*.parquet").as_posix()}', hive_partitioning = true)
        WHERE nutriscore_grade IN ('a', 'b', 'c', 'd', 'e')
          AND {not_null}
          AND sugars_100g <= carbohydrates_100g
          AND "saturated-fat_100g" <= fat_100g
          AND "energy-kcal_100g" > 0
        ORDER BY code
    """

def write_parquet(force : bool = False) -> Path:
    path = Path(f"{BASE_DIR.parent}/data/exports/features_nutriscope_{TODAY}.parquet")
    if path.exists() and not force:
        raise FileExistsError()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)

    con = duckdb.connect()
    con.execute(f"""
        COPY ({build_select()}) TO '{path.as_posix()}'
        (FORMAT PARQUET, COMPRESSION ZSTD)""")
    return path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file :
        for chunk in iter(lambda: file.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def build_schema(path: Path) -> pd.DataFrame:
    con = duckdb.connect()
    names_and_types = con.execute(f"""
        DESCRIBE SELECT * FROM read_parquet('{path.as_posix()}')
    """).fetchall()
    count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{path.as_posix()}')").fetchone()[0]
    cols = [c[0] for c in names_and_types]
    missings = {}
    for c in cols :
        missings[c] = con.execute(f'SELECT avg(("{c}" IS NULL)::INT) * 100 AS "{c}" FROM read_parquet(\'{path.as_posix()}\')').fetchone()
    target = "nutriscore_grade"
    target_rep = con.execute(f"SELECT {target}, count(*) FROM read_parquet('{path.as_posix()}')"
                         f"GROUP BY {target}"
                         f" ORDER BY 1").fetchall()
    freeze = date.today().isoformat()
    try :
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "unknown"
    sha = sha256_file(path)
    name = path.name
    schema = {
        "name": name,
        "freeze_date": freeze,
        "source": path.as_posix(),
        "git_commit": commit,
        "row_count": count,
        "sha256": sha,
        "target": target,  # "nutriscore_grade"
        "identifier": "code",
        "filters_applied": [
            "nutriscore_grade IN ('a','b','c','d','e')",
            "7 key nutrients IS NOT NULL",
            "sugars_100g <= carbohydrates_100g",
            "saturated-fat_100g <= fat_100g",
            "energy-kcal_100g > 0",
        ],
        "target_distribution": target_rep,  # dict {"a": n, ...}
        "columns": [
            {
                "name": c[0],
                "type": c[1],
                "missing_pct": missings[c[0]],
                **COLUMN_INFO[c[0]],  # unit, description, role, missing_policy
            }
            for c in names_and_types  # liste (nom, type, ...) issue de DESCRIBE, dans l'ordre du fichier
        ],
        "license": "ODbL - © Open Food Facts contributors",
        "intended_use": "Entraînement du modèle de prédiction du Nutri-Score (TP 14). "
                        "Split train/test non fait ici (TP 13).",
    }

    Path(f"{path.parent}/schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == '__main__':
    path = write_parquet(force=True)
    build_schema(path)


