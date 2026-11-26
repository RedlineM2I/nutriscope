"""Tests de l'export features figé : split stratifié, reproductible, figé, schéma fidèle.

Les tests tournent sur un faux Parquet partitionné écrit dans un dossier temporaire.
"""
import json

import duckdb
import numpy as np
import pandas as pd
import pytest

from src.config import SUCCESS_MARKER, SPLIT_SEED, TEST_SIZE
from src.storage.export_features import build_schema, build_select, sha256_file, write_parquet

# Grades déséquilibrés, comme dans les vraies données (a et b minoritaires)
GRADE_COUNTS = {"a": 15, "b": 25, "c": 60, "d": 70, "e": 40}


@pytest.fixture
def partitioned(tmp_path):
    """Faux Parquet partitionné par food_group, terminé par son marqueur _SUCCESS."""
    rng = np.random.default_rng(0)
    grades = [g for g, n in GRADE_COUNTS.items() for _ in range(n)]
    n = len(grades)
    df = pd.DataFrame({
        "code": [f"{i:013d}" for i in rng.permutation(n)],
        "food_group": rng.choice(["beverages", "sugary-snacks", "unknown"], n),
        "energy-kcal_100g": rng.uniform(10, 500, n).astype("float32"),
        "fat_100g": rng.uniform(5, 30, n).astype("float32"),
        "saturated-fat_100g": rng.uniform(0, 5, n).astype("float32"),
        "carbohydrates_100g": rng.uniform(20, 60, n).astype("float32"),
        "sugars_100g": rng.uniform(0, 20, n).astype("float32"),
        "proteins_100g": rng.uniform(0, 20, n).astype("float32"),
        "salt_100g": rng.uniform(0, 2, n).astype("float32"),
        "additives_n": rng.integers(0, 5, n).astype("int16"),
        "nova_group": rng.integers(1, 5, n).astype("int8"),
        "nutriscore_score": rng.integers(-5, 30, n).astype("int16"),
        "nutriscore_grade": grades,
    })
    folder = tmp_path / "products"
    con = duckdb.connect()
    con.register("df", df)
    con.execute(f"COPY df TO '{folder.as_posix()}' (FORMAT PARQUET, PARTITION_BY (food_group))")
    (folder / SUCCESS_MARKER).touch()
    return folder


@pytest.fixture
def export(partitioned, tmp_path):
    """Export écrit une fois, avec son schéma."""
    path = write_parquet(source=str(partitioned), export_dir=tmp_path / "exports")
    build_schema(path)
    return path


def test_split_is_stratified_on_grade(export):
    df = pd.read_parquet(export)

    for grade, n in GRADE_COUNTS.items():
        n_test = (df.loc[df["nutriscore_grade"] == grade, "split"] == "test").sum()
        assert n_test == round(n * TEST_SIZE)


def test_split_is_reproducible_product_by_product(partitioned, tmp_path):
    first = write_parquet(source=str(partitioned), export_dir=tmp_path / "run1")
    second = write_parquet(source=str(partitioned), export_dir=tmp_path / "run2")

    a = pd.read_parquet(first).set_index("code")["split"]
    b = pd.read_parquet(second).set_index("code")["split"]
    pd.testing.assert_series_equal(a, b)


def test_split_does_not_depend_on_other_grades(partitioned, tmp_path):
    only_a = tmp_path / "only_a"
    con = duckdb.connect()
    con.execute(f"""
        COPY (SELECT * FROM read_parquet('{partitioned.as_posix()}/**/*.parquet', hive_partitioning = true)
              WHERE nutriscore_grade = 'a')
        TO '{only_a.as_posix()}' (FORMAT PARQUET, PARTITION_BY (food_group))""")

    together = con.execute(f"SELECT code, split FROM ({build_select(str(partitioned))}) WHERE nutriscore_grade = 'a'").df()
    alone = con.execute(f"SELECT code, split FROM ({build_select(str(only_a))})").df()

    pd.testing.assert_frame_equal(alone, together)


def test_changing_the_seed_changes_the_split(partitioned):
    con = duckdb.connect()

    seed_42 = con.execute(f"SELECT split FROM ({build_select(str(partitioned))})").df()
    seed_7 = con.execute(f"SELECT split FROM ({build_select(str(partitioned), seed=7)})").df()

    assert not seed_42.equals(seed_7)


def test_export_refuses_to_overwrite_without_force(partitioned, export):
    with pytest.raises(FileExistsError, match="--force"):
        write_parquet(source=str(partitioned), export_dir=export.parent)


def test_force_rewrites_the_same_bytes(partitioned, export):
    before = sha256_file(export)

    write_parquet(force=True, source=str(partitioned), export_dir=export.parent)

    assert sha256_file(export) == before


def test_export_refuses_incomplete_partitioned_input(partitioned, tmp_path):
    (partitioned / SUCCESS_MARKER).unlink()

    with pytest.raises(FileNotFoundError, match="--extract_parquet"):
        write_parquet(source=str(partitioned), export_dir=tmp_path / "exports")


def test_schema_describes_the_written_file(export):
    schema = json.loads((export.parent / "schema.json").read_text(encoding="utf-8"))
    df = pd.read_parquet(export)

    assert schema["row_count"] == len(df)
    assert schema["sha256"] == sha256_file(export)
    assert [c["name"] for c in schema["columns"]] == list(df.columns)
    assert schema["split"]["seed"] == SPLIT_SEED == 42
    assert schema["split"]["test_size"] == TEST_SIZE
    for grade, n in GRADE_COUNTS.items():
        counts = schema["split"]["counts_by_grade"][grade]
        assert counts["train"] + counts["test"] == n
        assert counts["test"] == round(n * TEST_SIZE)
    assert "fit sur le train seulement" in schema["usage_rule"]
