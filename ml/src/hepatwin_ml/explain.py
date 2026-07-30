"""TU.11 -- Explainability: kontribusi 9 pola SMARTS terhadap prediksi.

[KEPUTUSAN AI -- PENDING REVIEW FARMASI, EXECUTION_PLAN_UPSCALE.md SS14.1
gerbang B5]: nama pola (features/smarts.py) belum divalidasi Farmasi, jangan
ditampilkan ke pengguna akhir sebelum ACC tertulis diterima.

Metode: nilai Shapley EKSAK atas 9 fitur biner SMARTS_SLICE (2^9=512 koalisi),
bukan KernelExplainer approksimasi -- untuk 9 fitur biner, eksak jauh lebih
murah (ratusan forward pass kecil) dan tidak punya noise sampling. Fitur di
luar SMARTS_SLICE (graf + MACCS + ECFP4) DITAHAN TETAP pada nilai molekul asli
selama perhitungan -- yang dijelaskan murni kontribusi marjinal blok SMARTS.

Cache per InChIKey (molekul sama -> hasil sama, tidak dihitung ulang).
Fallback: occlusion 1-fitur (bukan Shapley eksak) bila komputasi > 3 detik
(UPSCALE.md SS7) -- dalam praktiknya 512 forward pass kecil di CPU jauh di
bawah ambang ini, fallback ada untuk jaga-jaga di mesin lambat/molekul besar.
"""
import itertools
import json
import time
from pathlib import Path

import numpy as np
import torch
from rdkit import Chem
from torch_geometric.data import Batch

from hepatwin_ml.features.fingerprints import dnn_feature_vector
from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.features.smarts import SMARTS_PATTERNS, SMARTS_SLICE
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

N_SMARTS = len(SMARTS_PATTERNS)
_SHAPLEY_TIMEOUT_S = 3.0


def _predict_with_smarts_mask(model: GatnnDnn, graph_data, base_fingerprint: np.ndarray, mask: np.ndarray) -> float:
    """base_fingerprint dgn blok SMARTS diganti (mask * nilai_asli) -- fitur di
    luar SMARTS_SLICE tidak disentuh."""
    fp = base_fingerprint.copy()
    fp[SMARTS_SLICE] = base_fingerprint[SMARTS_SLICE] * mask
    batch = Batch.from_data_list([graph_data])
    batch.fingerprint = torch.tensor(fp, dtype=torch.float).unsqueeze(0)
    with torch.no_grad():
        logit = model(batch)
    return torch.sigmoid(logit).item()


def _exact_shapley(model: GatnnDnn, graph_data, base_fingerprint: np.ndarray) -> np.ndarray:
    """Nilai Shapley eksak untuk 9 fitur SMARTS biner (2^9 = 512 koalisi)."""
    from math import comb

    phi = np.zeros(N_SMARTS)
    features = list(range(N_SMARTS))
    value_cache: dict[tuple, float] = {}

    def v(subset: frozenset) -> float:
        if subset in value_cache:
            return value_cache[subset]
        mask = np.zeros(N_SMARTS)
        for idx in subset:
            mask[idx] = 1.0
        val = _predict_with_smarts_mask(model, graph_data, base_fingerprint, mask)
        value_cache[subset] = val
        return val

    n = N_SMARTS
    for i in features:
        others = [f for f in features if f != i]
        for r in range(len(others) + 1):
            weight = 1.0 / (n * comb(n - 1, r))
            for combo in itertools.combinations(others, r):
                s_without = frozenset(combo)
                s_with = frozenset(combo) | {i}
                phi[i] += weight * (v(s_with) - v(s_without))
    return phi


def _occlusion_fallback(model: GatnnDnn, graph_data, base_fingerprint: np.ndarray) -> np.ndarray:
    """Fallback cepat O(n): kontribusi = v(semua fitur) - v(semua kecuali fitur i)."""
    full_mask = np.ones(N_SMARTS)
    v_full = _predict_with_smarts_mask(model, graph_data, base_fingerprint, full_mask)
    phi = np.zeros(N_SMARTS)
    for i in range(N_SMARTS):
        mask = full_mask.copy()
        mask[i] = 0.0
        phi[i] = v_full - _predict_with_smarts_mask(model, graph_data, base_fingerprint, mask)
    return phi


def explain_smarts_contribution(
    model: GatnnDnn,
    smiles: str,
    inchikey: str,
    cache_path: str = "ml/data/interim/shap_cache.json",
) -> dict:
    """SMILES (sudah distandardisasi) -> {nama_pola: nilai_kontribusi}.

    Kontribusi POSITIF berarti keberadaan pola tsb MENDORONG NAIK skor risiko
    DILI, NEGATIF berarti menekan turun. Skala: perubahan probabilitas model
    (bukan logit), jadi bisa dibandingkan lintas molekul.
    """
    cache_file = Path(cache_path)
    cache: dict = {}
    if cache_file.exists():
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    if inchikey in cache:
        return cache[inchikey]

    mol = Chem.MolFromSmiles(smiles)
    graph_data = smiles_to_graph(smiles)
    base_fingerprint = dnn_feature_vector(mol)

    t0 = time.time()
    phi = _exact_shapley(model, graph_data, base_fingerprint)
    elapsed = time.time() - t0
    method = "exact_shapley"
    if elapsed > _SHAPLEY_TIMEOUT_S:
        phi = _occlusion_fallback(model, graph_data, base_fingerprint)
        method = "occlusion_fallback"

    result = {
        "method": method,
        "elapsed_s": round(elapsed, 3),
        "contributions": {SMARTS_PATTERNS[i].name: round(float(phi[i]), 6) for i in range(N_SMARTS)},
    }
    cache[inchikey] = result
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(cache, indent=0), encoding="utf-8")
    return result
