"""Sorties datées du pipeline : résolution des entrées et journal des durées.

Chaque étape écrit une sortie datée (`<nom>_<AAAAMMJJ>`). Pour lire son entrée, une
étape prend la sortie du jour, sinon la plus récente ; si elle n'en trouve aucune,
elle échoue en disant quelle étape lancer avant.
"""
import json
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from src.config import PARQUET_DIR, PARQUET_FR, PIPELINE_LOG, SUCCESS_MARKER
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


def require_france() -> Path:
    """Parquet du périmètre France (sortie de l'étape download, non daté : c'est la source)."""
    path = Path(PARQUET_FR)
    if not path.exists():
        raise FileNotFoundError(f"{path.name} absent : lancer d'abord `python -m src.pipeline --download`.")
    return path


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
