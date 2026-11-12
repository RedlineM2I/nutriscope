"""Sorties datées du pipeline : résolution des entrées et journal des durées.

Chaque étape écrit une sortie datée (`<nom>_<AAAAMMJJ>`). Pour lire son entrée, une
étape prend la sortie du jour, sinon la plus récente ; si elle n'en trouve aucune,
elle échoue en disant quelle étape lancer avant.
"""
import hashlib
import json
import os
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import duckdb

from src.config import BASE_DIR, PARQUET_DIR, PIPELINE_LOG, RAW_DIR, SOURCE_ENV, SUCCESS_MARKER
from src.models import StepReport


def latest_output(folder: Path, pattern: str, producer: str, require_success: bool = False) -> Path:
    """
    Sortie la plus récente de `folder` qui correspond à `pattern` (ex. 'food_clean_*.parquet').

    La date AAAAMMJJ dans le nom suffit à trier : la sortie du jour, si elle existe, est la dernière.
    :param producer: option de l'étape qui produit cette sortie, citée dans le message d'erreur
    :param require_success: ignore les dossiers sans marqueur `_SUCCESS` (écriture interrompue)
    """
    candidates = sorted(
        p for p in Path(folder).glob(pattern)
        if not require_success or (p / SUCCESS_MARKER).exists()
    )
    if not candidates:
        raise FileNotFoundError(
            f"Aucune sortie '{pattern}' complète dans {folder} : "
            f"lancer d'abord `python -m src.pipeline --{producer}`."
        )
    return candidates[-1]


def latest_clean() -> Path:
    """Parquet nettoyé le plus récent (sortie de l'étape clean)."""
    return latest_output(PARQUET_DIR, "food_clean_*.parquet", "clean")


def latest_partitioned() -> Path:
    """Dossier partitionné complet le plus récent (sortie de l'étape extract_parquet)."""
    return latest_output(PARQUET_DIR, "products_*", "extract_parquet", require_success=True)


def latest_raw() -> Path:
    """Brut figé le plus récent du périmètre France (sortie de l'étape download)."""
    return latest_output(RAW_DIR, "food_france_*.parquet", "download")


def source_override() -> Path | None:
    """
    Parquet source désigné par la variable NUTRISCOPE_SOURCE, ou None si elle n'est pas définie.

    Un chemin relatif est pris depuis la racine du dépôt, pas depuis le dossier courant.
    """
    value = os.getenv(SOURCE_ENV)
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = BASE_DIR.parent / path
    if not path.exists():
        raise FileNotFoundError(f"{SOURCE_ENV}={value} : fichier introuvable ({path}).")
    return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file :
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(source: Path, origin: str, raw: Path, rows: int, country: str, path: Path) -> None:
    """Écrit le manifeste du brut figé : d'où il vient, ses empreintes, son filtre. L'horodatage vit ici, pas dans les données."""
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": source.name,
        "source_origin": origin,
        "source_sha256": sha256_file(source),
        "source_size_bytes": source.stat().st_size,
        "raw_file": raw.name,
        "raw_sha256": sha256_file(raw),
        "rows": rows,
        "filter": f"list_contains(countries_tags, '{country}')",
        "code_type": "VARCHAR (code-barres en texte, zéros de tête conservés)",
        "license": "ODbL - © Open Food Facts contributors",
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def check_same_count_as_clean(step: str, rows: int, clean: Path) -> int:
    """
    Vérifie qu'une étape a écrit autant de produits que le nettoyé dont elle part.

    La base (load_database) et le Parquet (extract_parquet) lisent le même nettoyé :
    s'ils ne comptent pas le même nombre de produits, c'est la chaîne qui est fausse.
    """
    expected = duckdb.connect().execute(f"SELECT count(*) FROM read_parquet('{clean}')").fetchone()[0]
    if rows != expected:
        raise ValueError(f"{step} : {rows} produits écrits, mais {expected} dans {clean.name}.")
    print(f"✔ {step} : {rows} produits, autant que dans {clean.name}")
    return rows


def log_step(entry: dict, path: Path = PIPELINE_LOG) -> None:
    """Ajoute une ligne au journal JSON Lines des étapes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_step(name: str, step: Callable[..., StepReport], force: bool = False,
             log_path: Path = PIPELINE_LOG) -> StepReport:
    """Lance une étape et la consigne dans le journal, qu'elle réussisse ou échoue (puis relance l'erreur)."""
    timestamp = datetime.now().isoformat(timespec="seconds")
    start = time.perf_counter()
    try:
        report = step(force=force)
    except Exception as e:
        log_step({"timestamp": timestamp, "step": name, "duration_s": round(time.perf_counter() - start, 2),
                  "status": "failed", "rows": None, "error": f"{type(e).__name__}: {e}"}, log_path)
        raise
    log_step({"timestamp": timestamp, "step": name, "duration_s": round(time.perf_counter() - start, 2),
              "status": "ok", "rows": report.rows, "files": [Path(f).name for f in report.files]}, log_path)
    return report
