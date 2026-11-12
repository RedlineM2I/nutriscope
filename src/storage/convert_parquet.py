"""Conversion du Parquet nettoyé en dataset partitionné par food_group (TP 12).

Le script relit le Parquet nettoyé avec DuckDB, applique les types définis
dans `SCHEMA_COLUMNS` (un CAST par colonne, nutriments en FLOAT), puis écrit
un Parquet compressé ZSTD partitionné par `food_group`. Un fichier JSON
décrivant le schéma (types et justifications) est généré à côté.

Données : © Open Food Facts contributors, ODbL.
"""
import json, shutil
import time
from pathlib import Path
import duckdb

from src.config import KEY_NUTRIENTS, PARQUET_CLEAN_DATASET, PARQUET_CLEAN_BY_FOOD_GROUP, SCHEMA_PRODUIT_JSON, SUCCESS_MARKER

# Colonne -> (type DuckDB, justification du choix), reprise telle quelle dans le schéma JSON
SCHEMA_COLUMNS = {
    "code": ("VARCHAR", "un code-barres n'est pas un nombre, on garde les zéros de tête"),
    "product_name": ("VARCHAR", "texte libre, tel que dans le nettoyé"),
    "food_group": ("VARCHAR", "slug de la catégorie, sert de clé de partition ('unknown' si vide)"),
    "main_category": ("VARCHAR", "catégorie principale, texte normalisé"),
    "additives_n": ("SMALLINT", "nombre d'additifs, petit entier positif"),
    "brand": ("VARCHAR","première marque de la liste brands_tags"),
    "nutriscore_score": ("SMALLINT", "intervalle réel d'environ -15 à 40, tient sur 2 octets"),
    "last_modified_t": ("TIMESTAMP", "epoch en secondes converti via to_timestamp"),
    "nutriscore_grade": ("VARCHAR", "grade a-e, unknown, not-applicable ou NULL"),
    "nova_group": ("TINYINT", "4 valeurs (1 à 4), 1 octet suffit"),
}


def _create_request() -> str:
    """
    Construit la requête COPY qui convertit le Parquet nettoyé en Parquet partitionné.

    Chaque colonne est castée vers le type le plus compact possible (voir `SCHEMA_COLUMNS`),
    la marque est réduite au premier élément de `brands_tags`, les additifs sont comptés
    et `last_modified_t` passe d'un epoch en secondes à un TIMESTAMP.

    :return: Requête SQL DuckDB prête à être exécutée
    """
    columns = [
        "CAST(code AS VARCHAR) AS code",
        "product_name",
        "food_group",
        "main_category",
        "brands_tags[1] as brand",
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
    """
    Écrit le schéma du dataset partitionné au format JSON.

    Le fichier contient la clé de partition, la compression, le nombre de lignes,
    la licence et, pour chaque colonne, son type et la raison de ce choix.

    :param n_rows: Nombre de lignes du dataset partitionné
    :param path: Chemin du fichier JSON à écrire (créé avec ses dossiers parents si besoin)
    """
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

def convert_parquet() -> int:
    """
    Convertit le Parquet nettoyé en dataset Parquet partitionné par food_group.

    Le dossier de sortie est supprimé avant l'écriture pour que la conversion soit
    rejouable sans laisser de partition orpheline. Le marqueur `_SUCCESS` est écrit
    en dernier : un dossier sans marqueur est le reste d'une exécution interrompue.

    :return: Nombre de lignes relues dans le dataset partitionné
    """
    if Path(PARQUET_CLEAN_BY_FOOD_GROUP).exists():
        shutil.rmtree(PARQUET_CLEAN_BY_FOOD_GROUP)  # rejouable, pas de partition orpheline
    Path(PARQUET_CLEAN_BY_FOOD_GROUP).parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    request = _create_request()
    con.execute(request)
    n = con.execute(
        f"SELECT count(*) FROM read_parquet('{PARQUET_CLEAN_BY_FOOD_GROUP}/**/*.parquet', hive_partitioning=true)"
    ).fetchone()[0]
    (Path(PARQUET_CLEAN_BY_FOOD_GROUP) / SUCCESS_MARKER).touch()  # en dernier, une fois tout écrit et relu
    return n


if __name__ == "__main__":
    start = time.perf_counter()
    n = convert_parquet()
    end = time.perf_counter()
    print("Temps d'exécution : ", end - start)
    write_schema(n)
