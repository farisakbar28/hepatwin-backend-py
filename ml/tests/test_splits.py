import numpy as np
import pandas as pd
import pytest

from hepatwin_ml.data.splits import random_kfold, scaffold_kfold, temporal_split

# Beberapa SMILES nyata dengan scaffold berulang (benzena tersubstitusi) supaya
# scaffold_kfold punya kasus "scaffold sama, molekul beda" untuk diuji.
_SMILES = [
    "c1ccccc1O",       # phenol
    "c1ccccc1N",       # aniline
    "c1ccccc1C",       # toluene
    "c1ccccc1Cl",      # chlorobenzene
    "CCO",             # ethanol
    "CCN",             # ethylamine
    "CCCl",            # chloroethane
    "CC(=O)O",         # acetic acid
    "CC(=O)N",         # acetamide
    "c1ccc2[nH]ccc2c1",  # indole-like
]


def _make_df(n_per_class: int = 5) -> pd.DataFrame:
    smiles = (_SMILES * ((2 * n_per_class // len(_SMILES)) + 1))[: 2 * n_per_class]
    labels = [1] * n_per_class + [0] * n_per_class
    return pd.DataFrame({"canonical_smiles": smiles, "label_binary": labels})


def test_random_kfold_covers_all_rows_exactly_once_as_test():
    df = _make_df(n_per_class=10)
    seen = np.zeros(len(df), dtype=bool)
    n_folds = 0
    for train_idx, test_idx in random_kfold(df, k=5, seed=42):
        assert not set(train_idx) & set(test_idx)
        seen[test_idx] = True
        n_folds += 1
    assert n_folds == 5
    assert seen.all()


def test_scaffold_kfold_no_scaffold_leaks_across_folds():
    df = _make_df(n_per_class=10)
    from hepatwin_ml.data.splits import _bemis_murcko_scaffold

    scaffolds = df["canonical_smiles"].apply(_bemis_murcko_scaffold)

    for train_idx, test_idx in scaffold_kfold(df, k=5, seed=42):
        assert not set(train_idx) & set(test_idx)
        train_scaffolds = set(scaffolds.iloc[train_idx])
        test_scaffolds = set(scaffolds.iloc[test_idx])
        assert not (train_scaffolds & test_scaffolds), "scaffold bocor lintas fold"


def test_temporal_split_returns_none_without_year_column():
    df = _make_df(n_per_class=5)
    assert temporal_split(df) is None


def test_temporal_split_splits_by_cutoff_when_year_present():
    df = _make_df(n_per_class=5)
    df["approval_year"] = list(range(2000, 2000 + len(df)))
    result = temporal_split(df, cutoff=2005)
    assert result is not None
    train_idx, test_idx = result
    assert (df.iloc[train_idx]["approval_year"] < 2005).all()
    assert (df.iloc[test_idx]["approval_year"] >= 2005).all()
