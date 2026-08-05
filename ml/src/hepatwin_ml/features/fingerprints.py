"""TU.6 -- Cabang fingerprint/DNN: MACCS (167) + ECFP4 folded (1024) + SMARTS (9).

UPSCALE.md SS5.4: total (167+1024+9=1200 dim). Blok SMARTS ada di INDEKS
TERAKHIR (SMARTS_SLICE, features/smarts.py) supaya TU.11 (SHAP) bisa
menunjuk balik ke pola asal tanpa ambigu.
"""
import numpy as np
from rdkit import Chem
from rdkit.Chem import MACCSkeys, rdFingerprintGenerator

from hepatwin_ml.features.smarts import SMARTS_PATTERNS, smarts_flags

MACCS_DIM = 167
ECFP4_DIM = 1024
SMARTS_DIM = len(SMARTS_PATTERNS)
FINGERPRINT_DIM = MACCS_DIM + ECFP4_DIM + SMARTS_DIM

_morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=ECFP4_DIM)


def dnn_feature_vector(mol: Chem.Mol) -> np.ndarray:
    """Mol RDKit (sudah distandardisasi) -> vektor float64 panjang 1200.

    Urutan tetap: [MACCS(167), ECFP4(1024), SMARTS(9)] -- jangan diubah tanpa
    memperbarui SMARTS_SLICE di features/smarts.py.
    """
    maccs = np.array(MACCSkeys.GenMACCSKeys(mol), dtype=np.float64)  # 167 bit (indeks 0 selalu 0, tetap disertakan agar dim konsisten dgn RDKit)
    ecfp4 = np.zeros((ECFP4_DIM,), dtype=np.float64)
    bitvect = _morgan_gen.GetFingerprint(mol)
    on_bits = list(bitvect.GetOnBits())
    ecfp4[on_bits] = 1.0
    smarts = np.array(smarts_flags(mol), dtype=np.float64)

    return np.concatenate([maccs, ecfp4, smarts])
