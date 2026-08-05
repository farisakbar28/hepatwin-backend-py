"""TU.8/TU.19 -- Baseline pembanding: RF, MLP, LightGBM, XGBoost, Logistic Regression.

UPSCALE.md SS4.4 (Tahap 1) + SS13.2/K7 (v3.0, Panduan_Training...md Ketua Tim):
baseline diperluas supaya perbandingan GATNN-DNN vs model konvensional adil
dan tidak "dilemahkan" (baseline default-tuning) -- kelimanya memakai sumber
fitur yang identik (ECFP4 utk RF/LightGBM/XGBoost/LogReg, MACCS+deskriptor
khusus MLP, dipertahankan dari Tahap 1).

[Catatan teknis, bukan gerbang Farmasi]: himpunan deskriptor RDKit untuk MLP
dipilih dari deskriptor 2D umum yang sering dipakai literatur DILI-QSAR
(MolWt, LogP, TPSA, H-bond donor/acceptor, rotatable bonds, ring count,
aromatic ring count) -- bukan daftar resmi dari paper manapun, pilihan
rekayasa fitur yang wajar untuk baseline pembanding, bukan model utama.
"""
import numpy as np
from lightgbm import LGBMClassifier
from rdkit import Chem
from rdkit.Chem import Descriptors, rdFingerprintGenerator
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier

from hepatwin_ml.features.fingerprints import MACCS_DIM
from rdkit.Chem import MACCSkeys

ECFP4_DIM = 1024
_morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=ECFP4_DIM)

_DESCRIPTOR_FNS = [
    Descriptors.MolWt,
    Descriptors.MolLogP,
    Descriptors.TPSA,
    Descriptors.NumHDonors,
    Descriptors.NumHAcceptors,
    Descriptors.NumRotatableBonds,
    Descriptors.RingCount,
    Descriptors.NumAromaticRings,
    Descriptors.FractionCSP3,
    Descriptors.HeavyAtomCount,
]
DESCRIPTOR_DIM = len(_DESCRIPTOR_FNS)
MLP_INPUT_DIM = MACCS_DIM + DESCRIPTOR_DIM


def ecfp4_features(smiles_list: list[str]) -> np.ndarray:
    out = np.zeros((len(smiles_list), ECFP4_DIM), dtype=np.float64)
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        bitvect = _morgan_gen.GetFingerprint(mol)
        out[i, list(bitvect.GetOnBits())] = 1.0
    return out


def maccs_descriptor_features(smiles_list: list[str]) -> np.ndarray:
    out = np.zeros((len(smiles_list), MLP_INPUT_DIM), dtype=np.float64)
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        maccs = np.array(MACCSkeys.GenMACCSKeys(mol), dtype=np.float64)
        descriptors = np.array([fn(mol) for fn in _DESCRIPTOR_FNS], dtype=np.float64)
        out[i] = np.concatenate([maccs, descriptors])
    return out


def make_random_forest(seed: int, n_estimators: int = 500, max_depth: "int | None" = None) -> RandomForestClassifier:
    """TU.19: class_weight='balanced' ditambahkan -- sebelumnya tidak diset
    (gap nyata di Tahap 1, ditemukan & diperbaiki mengikuti Panduan_Training...md)."""
    return RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth, random_state=seed, n_jobs=-1, class_weight="balanced"
    )


def make_mlp(seed: int) -> MLPClassifier:
    return MLPClassifier(
        hidden_layer_sizes=(256, 64),
        activation="relu",
        alpha=1e-4,
        max_iter=500,
        random_state=seed,
        early_stopping=True,
        n_iter_no_change=20,
    )


def make_lightgbm(
    seed: int, scale_pos_weight: float = 1.0, num_leaves: int = 31, learning_rate: float = 0.1
) -> LGBMClassifier:
    """TU.19. scale_pos_weight WAJIB dihitung dari train fold saja oleh
    pemanggil (n_negatif/n_positif) -- memakai keseluruhan data akan jadi
    leakage (UPSCALE.md SS13.2)."""
    return LGBMClassifier(
        num_leaves=num_leaves,
        learning_rate=learning_rate,
        scale_pos_weight=scale_pos_weight,
        random_state=seed,
        verbosity=-1,
    )


def make_xgboost(
    seed: int, scale_pos_weight: float = 1.0, max_depth: int = 5, learning_rate: float = 0.1
) -> XGBClassifier:
    """TU.19. scale_pos_weight WAJIB dari train fold saja (sama seperti LightGBM)."""
    return XGBClassifier(
        max_depth=max_depth,
        learning_rate=learning_rate,
        scale_pos_weight=scale_pos_weight,
        random_state=seed,
        eval_metric="logloss",
        n_jobs=-1,
    )


def make_logistic_regression(seed: int, C: float = 1.0, penalty: str = "l2") -> LogisticRegression:
    """TU.19. max_iter=1000 -- default sklearn (100) sering tidak konvergen
    pada fitur berdimensi tinggi seperti ECFP4 (UPSCALE.md SS13.2)."""
    solver = "liblinear" if penalty == "l1" else "lbfgs"
    return LogisticRegression(
        C=C, penalty=penalty, solver=solver, class_weight="balanced", max_iter=1000, random_state=seed
    )


def compute_scale_pos_weight(labels: np.ndarray) -> float:
    """n_negatif/n_positif dari train fold -- dipakai LightGBM & XGBoost."""
    labels = np.asarray(labels)
    n_pos = max(int((labels == 1).sum()), 1)
    n_neg = max(int((labels == 0).sum()), 1)
    return n_neg / n_pos
