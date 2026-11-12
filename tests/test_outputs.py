"""Tests des sorties datées : résolution des entrées, journal des durées, conversion idempotente.

Tout tourne dans des dossiers temporaires.
"""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from src.config import KEY_NUTRIENTS, SUCCESS_MARKER
from src.models import StepReport
from src.outputs import latest_clean, latest_output, latest_partitioned, run_step
from src.storage.convert_parquet import convert_parquet


@pytest.fixture
def clean_parquet(tmp_path):
    """Petit Parquet nettoyé, avec les colonnes que lit convert_parquet."""
    rng = np.random.default_rng(0)
    n = 60
    df = pd.DataFrame({
        "code": [f"{i:013d}" for i in rng.permutation(n)],
        "product_name": [f"Produit {i}" for i in range(n)],
        "food_group": rng.choice(["beverages", "sugary-snacks", "unknown"], n),
        "main_category": "en:snacks",
        "brands_tags": [["marque-a"]] * n,
        "additives_tags": [["en:e330"]] * n,
        "nutriscore_score": rng.integers(-5, 30, n),
        "last_modified_t": rng.integers(1_600_000_000, 1_700_000_000, n),
        "nutriscore_grade": rng.choice(list("abcde"), n),
        "nova_group": rng.integers(1, 5, n),
        **{col: rng.uniform(0, 50, n) for col in KEY_NUTRIENTS},
    })
    path = tmp_path / "food_clean_20261110.parquet"
    df.to_parquet(path)
    return path


def _folder_hashes(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


# ---------- Résolution des entrées ----------

def test_latest_output_prefers_the_most_recent_date(tmp_path):
    for day in ["20261101", "20261112", "20261105"]:
        (tmp_path / f"food_clean_{day}.parquet").touch()

    assert latest_output(tmp_path, "food_clean_*.parquet", "clean").name == "food_clean_20261112.parquet"


def test_latest_output_without_any_output_names_the_step_to_run(tmp_path):
    with pytest.raises(FileNotFoundError, match="--clean"):
        latest_output(tmp_path, "food_clean_*.parquet", "clean")


def test_latest_partitioned_skips_folders_without_success(tmp_path, monkeypatch):
    monkeypatch.setattr("src.outputs.PARQUET_DIR", tmp_path)
    (tmp_path / "products_20261110").mkdir()
    (tmp_path / "products_20261110" / SUCCESS_MARKER).touch()
    (tmp_path / "products_20261112").mkdir()  # exécution interrompue : pas de marqueur

    assert latest_partitioned().name == "products_20261110"


def test_latest_clean_without_clean_output_names_the_clean_step(tmp_path, monkeypatch):
    monkeypatch.setattr("src.outputs.PARQUET_DIR", tmp_path)

    with pytest.raises(FileNotFoundError, match="--clean"):
        latest_clean()


def test_convert_reads_yesterdays_clean_output(clean_parquet, tmp_path, monkeypatch):
    monkeypatch.setattr("src.outputs.PARQUET_DIR", clean_parquet.parent)

    n = convert_parquet(latest_clean(), tmp_path / "products_20261112")

    assert n == 60
    assert (tmp_path / "products_20261112" / SUCCESS_MARKER).exists()


# ---------- Idempotence ----------

def test_convert_twice_writes_the_same_bytes(clean_parquet, tmp_path):
    dest = tmp_path / "products_20261112"

    convert_parquet(clean_parquet, dest)
    first = _folder_hashes(dest)
    convert_parquet(clean_parquet, dest)

    assert _folder_hashes(dest) == first
    assert any(name.endswith(".parquet") for name in first)


# ---------- Journal des durées ----------

def test_run_step_logs_a_successful_step(tmp_path):
    log = tmp_path / "pipeline.jsonl"

    run_step("clean", lambda force: StepReport("clean", 0.1, 42, ["data/parquet/food_clean_20261112.parquet"]),
             log_path=log)

    entry = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["step"] == "clean"
    assert entry["status"] == "ok"
    assert entry["rows"] == 42
    assert entry["files"] == ["food_clean_20261112.parquet"]
    assert {"timestamp", "duration_s"} <= entry.keys()


def test_run_step_logs_a_failed_step_then_raises(tmp_path):
    log = tmp_path / "pipeline.jsonl"

    def failing(force):
        raise FileNotFoundError("lancer d'abord --clean")

    with pytest.raises(FileNotFoundError):
        run_step("extract_parquet", failing, log_path=log)

    entry = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["status"] == "failed"
    assert entry["rows"] is None
    assert "--clean" in entry["error"]
