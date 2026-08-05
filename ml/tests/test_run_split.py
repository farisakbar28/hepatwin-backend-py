"""C5 -- test korpus training + verifikasi split (butuh ml/data/processed/features_all.parquet
dari C2, di-skip otomatis bila belum pernah dijalankan)."""
import json
from pathlib import Path

import pandas as pd
import pytest

from hepatwin_ml.data.harmonize_labels import harmonize_vdili_concern
from hepatwin_ml.data.splits import _bemis_murcko_scaffold

_REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "features_all.parquet"
TRAIN_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "train.parquet"
VAL_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "val.parquet"
TEST_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "test.parquet"
MANIFEST_PATH = _REPO_ROOT / "ml" / "data" / "interim" / "split_manifest.json"

pytestmark = pytest.mark.skipif(
    not (TRAIN_PATH.exists() and VAL_PATH.exists() and TEST_PATH.exists() and MANIFEST_PATH.exists()),
    reason="Jalankan ml/scripts/run_split.py dulu (butuh features_all.parquet dari C2)",
)


@pytest.fixture(scope="module")
def splits():
    return {
        "train": pd.read_parquet(TRAIN_PATH),
        "val": pd.read_parquet(VAL_PATH),
        "test": pd.read_parquet(TEST_PATH),
    }


def test_no_ambiguous_label_in_any_split(splits):
    for name, df in splits.items():
        assert df["label_binary"].isin([0, 1]).all(), f"{name} punya label_binary di luar {{0,1}}"


def test_no_inchikey_overlap_across_splits(splits):
    ik = {name: set(df["inchikey"]) for name, df in splits.items()}
    assert ik["train"] & ik["val"] == set()
    assert ik["train"] & ik["test"] == set()
    assert ik["val"] & ik["test"] == set()


def test_no_scaffold_overlap_across_splits(splits):
    scaf = {
        name: set(df["canonical_smiles"].apply(_bemis_murcko_scaffold))
        for name, df in splits.items()
    }
    assert scaf["train"] & scaf["val"] == set()
    assert scaf["train"] & scaf["test"] == set()
    assert scaf["val"] & scaf["test"] == set()


def test_split_sizes_sum_to_manifest_corpus_size(splits):
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    total = sum(len(df) for df in splits.values())
    assert total == manifest["n_training_corpus_G1"]


def test_g1_scope_vs_corpus_numbers_are_distinct(splits):
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["n_simulatable_scope_G1"] == 1231
    assert manifest["n_training_corpus_G1"] < manifest["n_simulatable_scope_G1"]


def test_test_set_is_scaffold_disjoint_15_to_20_percent(splits):
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    n_corpus = manifest["n_training_corpus_G1"]
    n_test = len(splits["test"])
    assert 0.15 * n_corpus <= n_test <= 0.20 * n_corpus + 1
