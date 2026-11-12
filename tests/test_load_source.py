"""Tests de l'étape download : source choisie par NUTRISCOPE_SOURCE, brut figé, manifeste,
et contrôle « même nombre de produits que le nettoyé ».

Tout tourne dans des dossiers temporaires, sur un faux parquet source.
"""
import json

import duckdb
import pandas as pd
import pytest

from src.config import BASE_DIR, COLUMNS, SOURCE_ENV
from src.db_parquet.products import get_products_from
from src.outputs import check_same_count_as_clean, sha256_file, source_override, write_manifest


@pytest.fixture
def source(tmp_path):
    """Faux parquet au format Open Food Facts : 3 produits en France, 1 ailleurs, codes en entier."""
    path = tmp_path / "source.parquet"
    others = ", ".join(f"NULL AS \"{c}\"" for c in COLUMNS if c != "code")
    duckdb.connect().execute(f"""
        COPY (
            SELECT code::BIGINT AS code, {others}, countries_tags
            FROM (VALUES
                (300, ['en:france']),
                (100, ['en:france', 'en:belgium']),
                (400, ['en:germany']),
                (200, ['en:france'])
            ) t(code, countries_tags)
        ) TO '{path.as_posix()}' (FORMAT PARQUET)
    """)
    return path


# ---------- NUTRISCOPE_SOURCE ----------

def test_source_override_is_none_without_the_variable(monkeypatch):
    monkeypatch.delenv(SOURCE_ENV, raising=False)

    assert source_override() is None


def test_source_override_resolves_a_relative_path_from_the_repository_root(monkeypatch):
    monkeypatch.setenv(SOURCE_ENV, "requirements.txt")  # un fichier qui existe à la racine
    monkeypatch.chdir(BASE_DIR)                          # lancé depuis un autre dossier

    assert source_override() == BASE_DIR.parent / "requirements.txt"


def test_source_override_pointing_nowhere_fails_with_the_variable_name(monkeypatch, tmp_path):
    monkeypatch.setenv(SOURCE_ENV, str(tmp_path / "absent.parquet"))

    with pytest.raises(FileNotFoundError, match=SOURCE_ENV):
        source_override()


# ---------- Brut figé ----------

def test_raw_keeps_only_france_sorted_with_text_codes(source, tmp_path):
    raw = tmp_path / "raw" / "food_france_20261112.parquet"

    rows = get_products_from(source, raw, "en:france")

    df = pd.read_parquet(raw)
    assert rows == 3
    assert df["code"].tolist() == ["100", "200", "300"]
    assert duckdb.connect().execute(f"SELECT typeof(code) FROM '{raw.as_posix()}' LIMIT 1").fetchone()[0] == "VARCHAR"


def test_raw_is_written_with_the_same_bytes_twice(source, tmp_path):
    raw = tmp_path / "food_france_20261112.parquet"

    get_products_from(source, raw, "en:france")
    first = sha256_file(raw)
    get_products_from(source, raw, "en:france")

    assert sha256_file(raw) == first


def test_manifest_records_the_source_fingerprint(source, tmp_path):
    raw = tmp_path / "food_france_20261112.parquet"
    manifest = tmp_path / "manifest_20261112.json"
    rows = get_products_from(source, raw, "en:france")

    write_manifest(source, "test", raw, rows, "en:france", manifest)

    content = json.loads(manifest.read_text(encoding="utf-8"))
    assert content["source_sha256"] == sha256_file(source)
    assert content["raw_sha256"] == sha256_file(raw)
    assert content["rows"] == 3
    assert "Open Food Facts" in content["license"]


# ---------- Base et Parquet partent du même nettoyé ----------

def test_count_check_passes_when_counts_match(source):
    assert check_same_count_as_clean("extract_parquet", 4, source) == 4


def test_count_check_fails_when_counts_differ(source):
    with pytest.raises(ValueError, match="load_database : 3 produits écrits, mais 4"):
        check_same_count_as_clean("load_database", 3, source)
