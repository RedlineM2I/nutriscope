"""Export des features figées pour la phase 4 (TP 12, split train/test au TP 13).

Lit le Parquet partitionné par food_group, filtre les produits exploitables,
ajoute une colonne `split` stratifiée sur le Nutri-Score (graine fixe) et écrit
`data/exports/features_<AAAAMMJJ>.parquet` avec son `schema.json`.
L'export est figé : il refuse de s'écraser sans `force=True`.

Données : © Open Food Facts contributors, ODbL.
"""
import hashlib
import json
import subprocess
from datetime import date

import duckdb
import pandas as pd
from _duckdb import DuckDBPyConnection
from pathlib import Path
from src.config import (PARQUET_CLEAN_BY_FOOD_GROUP, BASE_DIR, TODAY, SUCCESS_MARKER,
                        EXPORTS_DIR, SPLIT_SEED, TEST_SIZE)

KEY_NUTRIENTS = [
    "energy-kcal_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g",
    "salt_100g",
]

USAGE_RULE = (
    "fit sur le train seulement ; le test n'est regardé qu'une fois, à la fin ; "
    "la validation croisée se fait à l'intérieur du train. "
    "Ne pas recalculer le split. Ne pas utiliser nutriscore_score pour prédire le grade, "
    "ni code, product_name ou brands comme features."
)

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
    "split": _info("-", "train / test, frozen: never recompute", "split", "none"),
}

def read_partitioned_parquet(con: DuckDBPyConnection, req: str) -> pd.DataFrame :
    return con.execute(req).df()

def build_select(path: str = PARQUET_CLEAN_BY_FOOD_GROUP, seed: int = SPLIT_SEED,
                 test_size: float = TEST_SIZE) -> str:
    """Return the SQL selecting the usable products for Nutri-Score prediction.

    Reads the hive-partitioned Parquet (food_group comes from the folder name).
    Adds the frozen `split` column, stratified on nutriscore_grade: within each grade,
    products are ranked by md5(code || seed) and the first `test_size` share goes to test.
    A product's split only depends on its code, its grade and the seed.
    """
    # Les noms avec un tiret doivent être entre guillemets doubles en SQL.
    q = {n: f'"{n}"' for n in KEY_NUTRIENTS}
    not_null = " AND ".join(f"{c} IS NOT NULL" for c in q.values())

    return f"""
        WITH features AS (
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
        )
        SELECT *,
            CASE WHEN row_number() OVER (PARTITION BY nutriscore_grade ORDER BY md5(code || '{seed}'))
                      <= round(count(*) OVER (PARTITION BY nutriscore_grade) * {test_size})
                 THEN 'test' ELSE 'train' END AS split
        FROM features
        ORDER BY code
    """

def check_success(folder: str = PARQUET_CLEAN_BY_FOOD_GROUP) -> None:
    """Refuse de lire un dossier partitionné sans marqueur `_SUCCESS` (écriture incomplète)."""
    if not (Path(folder) / SUCCESS_MARKER).exists():
        raise FileNotFoundError(
            f"Parquet partitionné incomplet ou absent ({folder}, pas de {SUCCESS_MARKER}) : "
            "lancer d'abord `python -m src.pipeline --extract_parquet`."
        )

def write_parquet(force: bool = False, source: str = PARQUET_CLEAN_BY_FOOD_GROUP,
                  export_dir: Path = EXPORTS_DIR) -> Path:
    """Écrit l'export features du jour, avec sa colonne `split`.

    :param force: réécrit l'export du jour s'il existe déjà (sinon FileExistsError)
    :return: chemin du fichier écrit
    """
    check_success(source)
    path = Path(export_dir) / f"features_{TODAY}.parquet"
    if path.exists() and not force:
        raise FileExistsError(
            f"Export figé déjà présent : {path.name}. Il sert de référence à la phase 4 ; "
            "changer de date ou relancer avec --force en l'assumant."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)

    con = duckdb.connect()
    con.execute("SET threads = 1")  # écriture déterministe : mêmes octets à chaque exécution
    con.execute(f"""
        COPY ({build_select(source)}) TO '{path.as_posix()}'
        (FORMAT PARQUET, COMPRESSION ZSTD)""")
    return path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file :
        for chunk in iter(lambda: file.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def _split_counts(con: DuckDBPyConnection, file: str) -> dict[str, dict]:
    """Effectifs train / test et part de test pour chaque grade, relus dans le fichier écrit."""
    rows = con.execute(f"""
        SELECT nutriscore_grade,
               count(*) FILTER (WHERE split = 'train') AS train,
               count(*) FILTER (WHERE split = 'test') AS test
        FROM read_parquet('{file}')
        GROUP BY nutriscore_grade ORDER BY nutriscore_grade
    """).fetchall()
    return {
        grade: {"train": train, "test": test, "test_share": round(test / (train + test), 4)}
        for grade, train, test in rows
    }

def build_schema(path: Path) -> int:
    """Écrit `schema.json` à côté de l'export. Retourne le nombre de lignes du fichier."""
    con = duckdb.connect()
    file = path.as_posix()
    names_and_types = con.execute(f"""
        DESCRIBE SELECT * FROM read_parquet('{file}')
    """).fetchall()
    count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{file}')").fetchone()[0]
    cols = [c[0] for c in names_and_types]
    missings = {}
    for c in cols :
        missings[c] = con.execute(f'SELECT avg(("{c}" IS NULL)::INT) * 100 AS "{c}" FROM read_parquet(\'{file}\')').fetchone()[0]
    target = "nutriscore_grade"
    target_rep = dict(con.execute(f"SELECT {target}, count(*) FROM read_parquet('{file}')"
                                  f" GROUP BY {target}"
                                  f" ORDER BY 1").fetchall())
    freeze = date.today().isoformat()
    try :
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                                cwd=BASE_DIR.parent).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "unknown"
    try:
        source = path.resolve().relative_to(BASE_DIR.parent).as_posix()
    except ValueError:  # export écrit hors du dépôt (tests)
        source = path.name
    sha = sha256_file(path)
    name = path.name
    schema = {
        "name": name,
        "freeze_date": freeze,
        "source": source,
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
        "target_distribution": target_rep,  # {"a": n, ...}
        "split": {
            "column": "split",
            "method": "stratified on nutriscore_grade: within each grade, products ranked by "
                      "md5(code || seed); the first round(n * test_size) go to test",
            "seed": SPLIT_SEED,
            "test_size": TEST_SIZE,
            "why_test_size": "20 % keeps enough grade a and b products in the test set; "
                             "80 % stays for training and cross-validation",
            "counts_by_grade": _split_counts(con, file),
        },
        "usage_rule": USAGE_RULE,
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
        "intended_use": "Entraînement et évaluation du modèle de prédiction du Nutri-Score (TP 14 à 16), "
                        "avec la colonne split telle quelle.",
    }

    Path(f"{path.parent}/schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    return count

if __name__ == '__main__':
    path = write_parquet()
    build_schema(path)
