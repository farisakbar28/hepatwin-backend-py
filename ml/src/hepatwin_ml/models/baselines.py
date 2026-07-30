"""TU.8 -- Baseline pembanding: Random Forest (ECFP4) & MLP (MACCS + deskriptor).

UPSCALE.md SS4.4: "Random Forest (ECFP4) dan MLP (MACCS + deskriptor), dilatih
pada split yang sama, dilaporkan di tabel yang sama."

[Catatan teknis, bukan gerbang Farmasi]: himpunan deskriptor RDKit untuk MLP
dipilih dari deskriptor 2D umum yang sering dipakai literatur DILI-QSAR
(MolWt, LogP, TPSA, H-bond donor/acceptor, rotatable bonds, ring count,
aromatic ring count) -- bukan daftar resmi dari paper manapun, pilihan
rekayasa fitur yang wajar untuk baseline pembanding, bukan model utama.
"""
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdFingerprintGenerator
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

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


def make_random_forest(seed: int) -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=500, max_depth=None, random_state=seed, n_jobs=-1)


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
