"""C8 -- Explainability: kontribusi tingkat GUGUS (SMARTS, upscale, apa adanya)
DAN tingkat ATOM (baru, PROJECT_FIX_MODEL.md SS4.4 / EXECUTION_PLAN_FIX_MODEL.md C8).

## Tingkat gugus (grup, warisan upscale TU.11)

Nilai Shapley EKSAK atas 9 fitur biner SMARTS_SLICE (2^9=512 koalisi), bukan
KernelExplainer approksimasi -- untuk 9 fitur biner, eksak jauh lebih murah
(ratusan forward pass kecil) dan tidak punya noise sampling. Fitur di luar
SMARTS_SLICE (graf + MACCS + ECFP4) DITAHAN TETAP pada nilai molekul asli
selama perhitungan -- yang dijelaskan murni kontribusi marjinal blok SMARTS.

## Tingkat atom (BARU, C8)

🔴 Metode: **occlusion/masking per-atom** -- untuk tiap atom, fitur node-nya
dinolkan (bukan dihapus dari graf, edge topologi tetap), diukur delta
probabilitas prediksi vs molekul utuh. Ini SENGAJA dilabeli jujur sebagai
`"masking_attribution"`, BUKAN "SHAP" -- ini bukan nilai Shapley sebenarnya
(tidak menghitung rata-rata atas semua koalisi kemungkinan subset atom,
yang untuk molekul besar computationally infeasible). Aturan kejujuran
EXECUTION_PLAN_FIX_MODEL.md C8: menyebut hasil masking sebagai "SHAP" adalah
klaim yang salah.

Seluruh varian (molekul utuh + N atom di-mask) di-batch dalam SATU forward
pass (`Batch.from_data_list`) -- anggaran latensi C8 (<2 detik p95, 50
molekul), bukan loop serial per atom seperti versi `master` lama di
`app/services/ai_engine.py` (diperbaiki C10).

Cache per InChIKey (molekul sama -> hasil sama, tidak dihitung ulang).
"""
import itertools
import json
import time
from pathlib import Path

import numpy as np
import torch
from rdkit import Chem
from torch_geometric.data import Batch, Data

from hepatwin_ml.features.fingerprints import dnn_feature_vector
from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.features.smarts import SMARTS_PATTERNS, SMARTS_SLICE
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

N_SMARTS = len(SMARTS_PATTERNS)
_SHAPLEY_TIMEOUT_S = 3.0
_COMPILED_SMARTS = [Chem.MolFromSmarts(p.pattern) for p in SMARTS_PATTERNS]


# ---------------------------------------------------------------------------
# Tingkat gugus (SMARTS) -- warisan upscale TU.11, tidak diubah
# ---------------------------------------------------------------------------


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


def _smarts_atom_indices(mol: Chem.Mol) -> dict[str, list[int]]:
    """Nama pola SMARTS -> indeks atom (union semua match RDKit). Pola yang
    TIDAK match menghasilkan list kosong -- dipakai `explain()` untuk
    membuang grup yang tidak match dari keluaran (C8 AC: "molekul tanpa
    satu pun match SMARTS -> list kosong, bukan crash")."""
    out: dict[str, list[int]] = {}
    for pattern, compiled in zip(SMARTS_PATTERNS, _COMPILED_SMARTS):
        matches = mol.GetSubstructMatches(compiled)
        out[pattern.name] = sorted({idx for match in matches for idx in match})
    return out


# ---------------------------------------------------------------------------
# Tingkat atom -- BARU (C8), occlusion per-atom, di-batch satu forward pass
# ---------------------------------------------------------------------------


def atom_masking_attribution(model: GatnnDnn, smiles: str) -> list[dict]:
    """SMILES (sudah distandardisasi) -> [{"idx": i, "value": delta}, ...].

    `value` = P(molekul utuh) - P(atom i dinolkan) -- POSITIF berarti atom
    itu MENDORONG NAIK skor risiko (menghapusnya menurunkan skor), NEGATIF
    berarti atom itu justru menekan skor turun.

    Molekul tanpa ikatan (mis. ion tunggal, 1 atom) tetap valid -- ditangani
    otomatis oleh smiles_to_graph() (C3), tidak butuh percabangan khusus di sini.
    """
    mol = Chem.MolFromSmiles(smiles)
    graph_data = smiles_to_graph(smiles)
    fingerprint = torch.tensor(dnn_feature_vector(mol), dtype=torch.float)
    n_atoms = graph_data.x.shape[0]

    # Varian 0 = molekul utuh (baseline); varian i+1 = atom i dinolkan.
    variants = [Data(x=graph_data.x, edge_index=graph_data.edge_index, edge_attr=graph_data.edge_attr)]
    for i in range(n_atoms):
        x_masked = graph_data.x.clone()
        x_masked[i, :] = 0.0
        variants.append(Data(x=x_masked, edge_index=graph_data.edge_index, edge_attr=graph_data.edge_attr))

    batch = Batch.from_data_list(variants)
    batch.fingerprint = fingerprint.unsqueeze(0).repeat(len(variants), 1)

    with torch.no_grad():
        probs = torch.sigmoid(model(batch)).numpy()

    baseline_prob = float(probs[0])
    return [{"idx": i, "value": round(baseline_prob - float(probs[i + 1]), 6)} for i in range(n_atoms)]


# ---------------------------------------------------------------------------
# Orkestrator gabungan -- format keluaran EXECUTION_PLAN_FIX_MODEL.md C8 langkah 3
# ---------------------------------------------------------------------------


def explain(
    model: GatnnDnn,
    smiles_standardized: str,
    inchikey: str,
    cache_path: str = "ml/data/interim/explain_cache.json",
) -> dict:
    """Titik masuk tunggal C8/C10: SMILES terstandardisasi -> atribusi gugus +
    atom dalam satu struktur, di-cache per InChIKey.

    `atom_indices` (di dalam `groups`) merujuk ke indeks atom pada MOL yang
    diparse dari `smiles_standardized` -- sama dengan `smiles_used` yang
    disertakan di keluaran, supaya frontend menggambar dari string yang
    identik dengan yang dipakai menghitung atribusi (PROJECT_FIX_MODEL.md SS4.4).
    """
    cache_file = Path(cache_path)
    cache: dict = {}
    if cache_file.exists():
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    if inchikey in cache:
        return cache[inchikey]

    mol = Chem.MolFromSmiles(smiles_standardized)
    if mol is None:
        raise ValueError(f"explain(): gagal parse smiles_standardized={smiles_standardized!r}")

    smarts_result = explain_smarts_contribution(model, smiles_standardized, inchikey)
    atom_indices_by_group = _smarts_atom_indices(mol)
    atoms = atom_masking_attribution(model, smiles_standardized)

    groups = [
        {
            "name": name,
            "value": value,
            "atom_indices": atom_indices_by_group[name],
        }
        for name, value in smarts_result["contributions"].items()
        if atom_indices_by_group[name]  # buang grup yang tidak match (C8 AC)
    ]
    groups.sort(key=lambda g: abs(g["value"]), reverse=True)

    result = {
        "method": "masking_attribution",
        "groups": groups,
        "atoms": atoms,
        "smiles_used": smiles_standardized,
    }

    cache[inchikey] = result
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(cache, indent=0), encoding="utf-8")
    return result
