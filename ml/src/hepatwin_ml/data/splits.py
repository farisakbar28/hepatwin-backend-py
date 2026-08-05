"""TU.5 -- Modul split (random & scaffold wajib; temporal opsional).

Dasar: EXECUTION_PLAN_UPSCALE.md TU.5, UPSCALE.md SS4.1 (L1 = random 5-fold CV,
L2 = scaffold 5-fold CV, Bemis-Murcko).
"""
from typing import Iterator, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import StratifiedKFold


def random_kfold(df: pd.DataFrame, k: int = 5, seed: int = 42) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Stratified random k-fold pada label_binary. Wajib (UPSCALE.md SS4.1 L1)."""
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    yield from skf.split(df, df["label_binary"])


def _bemis_murcko_scaffold(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold) if scaffold is not None else ""


def scaffold_kfold(df: pd.DataFrame, k: int = 5, seed: int = 42) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Group k-fold berbasis scaffold Bemis-Murcko. Satu scaffold tidak boleh
    muncul di dua fold berbeda. Wajib (UPSCALE.md SS4.1 L2)."""
    scaffolds = df["canonical_smiles"].apply(_bemis_murcko_scaffold)
    unique_scaffolds = scaffolds.unique()

    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(unique_scaffolds)
    fold_of_scaffold: dict[str, int] = {s: i % k for i, s in enumerate(shuffled)}

    fold_assignment = scaffolds.map(fold_of_scaffold).to_numpy()
    indices = np.arange(len(df))
    for fold in range(k):
        test_idx = indices[fold_assignment == fold]
        train_idx = indices[fold_assignment != fold]
        yield train_idx, test_idx


def temporal_split(df: pd.DataFrame, year_col: str = "approval_year", cutoff: int = 2010) -> Optional[tuple[np.ndarray, np.ndarray]]:
    """Split berbasis tahun persetujuan. OPSIONAL -- tidak masuk Definition of
    Done (UPSCALE.md SS4.3). Mengembalikan None bila kolom tahun tidak tersedia,
    karena DILIrank/LiverTox tidak selalu menyertakan tahun persetujuan per baris."""
    if year_col not in df.columns:
        return None
    indices = np.arange(len(df))
    train_idx = indices[df[year_col] < cutoff]
    test_idx = indices[df[year_col] >= cutoff]
    return train_idx, test_idx
