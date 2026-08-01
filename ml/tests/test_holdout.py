import pandas as pd

from hepatwin_ml.data.holdout import HOLDOUT_FRACTION_MAX, HOLDOUT_FRACTION_MIN, build_holdout_split
from hepatwin_ml.data.splits import _bemis_murcko_scaffold

_SMILES = [
    "c1ccccc1O", "c1ccccc1N", "c1ccccc1C", "c1ccccc1Cl", "c1ccccc1Br",
    "CC(=O)Nc1ccc(O)cc1", "CC(=O)Oc1ccccc1C(=O)O",
    "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "c1ccc2[nH]ccc2c1", "c1ccc2ncccc2c1", "c1ccc2scnc2c1",
    "C1CCCCC1", "C1CCCC1", "C1CCC1",
]


def _make_df(n_repeat: int = 15) -> pd.DataFrame:
    smiles = (_SMILES * ((2 * n_repeat // len(_SMILES)) + 1))[: 2 * n_repeat]
    labels = [1] * n_repeat + [0] * n_repeat
    return pd.DataFrame(
        {
            "canonical_smiles": smiles,
            "label_binary": labels,
            "inchikey": [f"FAKE{i:06d}INCHIKEY" for i in range(len(smiles))],
        }
    )


def test_holdout_is_scaffold_disjoint_from_dev_pool():
    df = _make_df(n_repeat=50)
    holdout_df, dev_pool_df = build_holdout_split(df, seed=42)

    holdout_scaffolds = set(holdout_df["canonical_smiles"].apply(_bemis_murcko_scaffold))
    dev_scaffolds = set(dev_pool_df["canonical_smiles"].apply(_bemis_murcko_scaffold))

    assert not (holdout_scaffolds & dev_scaffolds), "Ada scaffold yang bocor lintas holdout/dev_pool"


def test_holdout_size_within_target_range():
    df = _make_df(n_repeat=100)
    holdout_df, dev_pool_df = build_holdout_split(df, seed=42)

    fraction = len(holdout_df) / len(df)
    assert HOLDOUT_FRACTION_MIN <= fraction <= HOLDOUT_FRACTION_MAX + 0.05, (
        f"Fraksi holdout {fraction:.3f} di luar target {HOLDOUT_FRACTION_MIN}-{HOLDOUT_FRACTION_MAX}"
    )
    assert len(holdout_df) + len(dev_pool_df) == len(df)


def test_holdout_and_dev_pool_no_row_overlap():
    df = _make_df(n_repeat=50)
    holdout_df, dev_pool_df = build_holdout_split(df, seed=42)

    holdout_keys = set(holdout_df["inchikey"])
    dev_keys = set(dev_pool_df["inchikey"])
    assert not (holdout_keys & dev_keys)
