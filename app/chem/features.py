"""Featurizer tabular — SATU-SATUNYA sumber featurization (AGENTS.md §4).

Dasar: Arsitektur §D.3 · EXECUTION_PLAN.md T1.8.

Komposisi vektor: ECFP4 2048 bit + 10 deskriptor + n flag SMARTS.
Script training di `ml/` WAJIB mengimpor dari sini, tidak menyalin. Featurizer
berbeda antara training dan inference adalah bug ML paling sulit dilacak.

Prefiks `smarts::` pada nama fitur bukan kosmetik — itu yang dipakai lapisan
explainability untuk menyaring kontribusi SHAP hanya dari fitur bernama
farmakologis (PRD §8.5).
"""
from typing import Callable

import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, rdFingerprintGenerator

from app.chem.smarts_library import SMARTS_COMPILED

_FP_SIZE = 2048
_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=_FP_SIZE)

# Sepuluh deskriptor fisikokimia (Arsitektur §D.3).
_DESCRIPTORS: list[tuple[str, Callable]] = [
    ("mw", Descriptors.MolWt),
    ("logp", Crippen.MolLogP),
    ("tpsa", Descriptors.TPSA),
    ("hbd", Descriptors.NumHDonors),
    ("hba", Descriptors.NumHAcceptors),
    ("rotb", Descriptors.NumRotatableBonds),
    ("arom", Descriptors.NumAromaticRings),
    ("heavy", Descriptors.HeavyAtomCount),
    ("fsp3", Descriptors.FractionCSP3),
    ("rings", Descriptors.RingCount),
]


def feature_names() -> list[str]:
    """Nama tiap kolom fitur, urutan sama persis dengan `featurize()`."""
    return (
        [f"ecfp_{i}" for i in range(_FP_SIZE)]
        + [name for name, _ in _DESCRIPTORS]
        + [f"smarts::{key}" for key in SMARTS_COMPILED]
    )


def featurize(mol: "Chem.Mol") -> np.ndarray:
    """Vektor fitur satu molekul (float32). Panjang == len(feature_names())."""
    fp = np.asarray(_gen.GetFingerprintAsNumPy(mol), dtype=np.float32)
    desc = np.asarray([fn(mol) for _, fn in _DESCRIPTORS], dtype=np.float32)
    smarts = np.asarray(
        [float(mol.HasSubstructMatch(pat)) for pat in SMARTS_COMPILED.values()],
        dtype=np.float32,
    )
    return np.concatenate([fp, desc, smarts])


def featurize_batch(mols: list["Chem.Mol"]) -> np.ndarray:
    """Matriks fitur (n_mol, n_feature) untuk training."""
    if not mols:
        return np.empty((0, len(feature_names())), dtype=np.float32)
    return np.vstack([featurize(m) for m in mols])
