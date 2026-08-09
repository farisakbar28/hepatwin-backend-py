"""C8 -- Explainability: kontribusi tingkat GUGUS (SMARTS, upscale, apa adanya)
DAN tingkat ATOM (baru, PROJECT_FIX_MODEL.md SS4.4 / EXECUTION_PLAN_FIX_MODEL.md C8).

## Tingkat gugus (grup, warisan upscale TU.11)

Nilai Shapley EKSAK atas 9 fitur biner SMARTS_SLICE, bukan KernelExplainer
approksimasi (P0): enumerasi koalisi dibatasi ke fitur yang MATCH saja (2^k,
k = jumlah fitur dengan base flag 1; fitur non-aktif -> phi 0 EKSAK) dan
seluruh koalisi dihitung dalam SATU forward ter-batch (graph_branch sekali,
lihat `_batched_smarts_probs`) -- hasil matematis IDENTIK dengan enumerasi
2^9=512, tanpa noise sampling. Fitur di luar SMARTS_SLICE (graf + MACCS +
ECFP4) DITAHAN TETAP pada nilai molekul asli selama perhitungan -- yang
dijelaskan murni kontribusi marjinal blok SMARTS.

## Tingkat atom (BARU, C8)

🔴 Metode: **occlusion/masking per-atom** -- untuk tiap atom, fitur node-nya
dinolkan (bukan dihapus dari graf, edge topologi tetap), diukur delta
probabilitas prediksi vs molekul utuh. Ini SENGAJA dilabeli jujur sebagai
`"masking_attribution"`, BUKAN "SHAP" -- ini bukan nilai Shapley sebenarnya
(tidak menghitung rata-rata atas semua koalisi kemungkinan subset atom,
yang untuk molekul besar computationally infeasible). Aturan kejujuran
EXECUTION_PLAN_FIX_MODEL.md C8: menyebut hasil masking sebagai "SHAP" adalah
klaim yang salah.

Seluruh varian (molekul utuh + N atom di-mask) diproses dalam forward
ter-batch PER CHUNK (P3: `_ATOM_MASK_CHUNK` = 32 varian/forward, bukan satu
batch raksasa) -- anggaran latensi C8 (<2 detik p95, 50 molekul) sekaligus
membatasi puncak memori utk molekul besar (Rifampin 60 varian, Aprotinin
455 varian): batch raksasa menaikkan RSS puluhan MB dan mengetuk ambang OOM
Hobby tier 512 MB. Hasil matematis IDENTIK -- tiap varian tetap dihitung
sendiri, hanya ukuran batch yang dibatasi.

Cache IN-MEMORY bounded LRU per (model, inchikey) (P2) -- pengganti file JSON
`shap_cache.json`/`explain_cache.json` yang dibaca/ditulis penuh tiap request
dan tumbuh tanpa batas. Bounded 10000 entri per cache, thread-safe; hilang
saat proses restart (scale-to-zero) -- konsekuensi diterima mengingat
komputasi kini cepat (P0) dan deterministik.

Footprint terukur (P2, deep sizeof): entri `smarts` ~1.4 KB KONSTAN (9
kontribusi + method + elapsed); entri `explain` ~1.7 KB overhead + ~240
B/atom (parasetamol 11 atom = 4.3 KB; 60 atom = 15.4 KB; 100 atom = 25.2 KB).
Pada maxsize 2048 (P3, DITURUNKAN dari 10000 pasca-temuan OOM Hobby 512 MB --
baseline app ~415 MB + puncak compute ~493 MB mengetuk ambang): ~3 MB
(smarts) + ~10-51 MB (explain, worst-case semua molekul >=100 atom) --
margin aman utk 512 MB.

Kunci cache memegang referensi kuat ke objek model (identitas objek). Dalam
produksi hanya ada SATU shared model (singleton orchestrator) sehingga aman;
di proses yang membuat banyak model (test), entri model lama baru dibuang
setelah LRU penuh (10000) -- bounded, diterima.
"""
import itertools
import threading
import time

from cachetools import LRUCache

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
# P3: varian atom-masking diproses per chunk maksimal `_ATOM_MASK_CHUNK`
# forward -- membatasi puncak memori utk molekul besar (lihat docstring C8).
_ATOM_MASK_CHUNK = 32
_COMPILED_SMARTS = [Chem.MolFromSmarts(p.pattern) for p in SMARTS_PATTERNS]


# ---------------------------------------------------------------------------
# Cache in-memory bounded LRU (P2) -- pengganti file shap_cache/explain_cache
# ---------------------------------------------------------------------------

_EXPLAIN_CACHE_MAXSIZE = 2048
_explain_cache: LRUCache = LRUCache(maxsize=_EXPLAIN_CACHE_MAXSIZE)
_explain_cache_lock = threading.Lock()
_smarts_cache: LRUCache = LRUCache(maxsize=_EXPLAIN_CACHE_MAXSIZE)
_smarts_cache_lock = threading.Lock()


def _cache_key(model, inchikey: str) -> tuple:
    """Kunci cache: identitas objek model + InChIKey -- model berbeda (mis.
    antar-test dengan bobot acak) TIDAK boleh berbagi entri cache."""
    return (model, inchikey)


def _cache_get(cache: LRUCache, lock: threading.Lock, key) -> dict | None:
    """Baca cache thread-safe; cachetools memperbarui recency saat get (LRU)."""
    with lock:
        try:
            return cache[key]
        except KeyError:
            return None


def _cache_set(cache: LRUCache, lock: threading.Lock, key, value: dict) -> None:
    """Tulis cache thread-safe; LRU meng-evict entri terlama bila penuh."""
    with lock:
        cache[key] = value


# ---------------------------------------------------------------------------
# Tingkat gugus (SMARTS) -- warisan upscale TU.11, tidak diubah
# ---------------------------------------------------------------------------


def _predict_with_smarts_mask(model: GatnnDnn, graph_data, base_fingerprint: np.ndarray, mask: np.ndarray) -> float:
    """base_fingerprint dgn blok SMARTS diganti (mask * nilai_asli) -- fitur di
    luar SMARTS_SLICE tidak disentuh.

    DIPERTAHANKAN walau jalur produksi kini memakai `_batched_smarts_probs`
    (P0) -- fungsi ini masih diimpor langsung oleh `ml/tests/test_explain.py`
    sebagai referensi serial utk verifikasi properti Shapley. JANGAN dihapus.
    """
    fp = base_fingerprint.copy()
    fp[SMARTS_SLICE] = base_fingerprint[SMARTS_SLICE] * mask
    batch = Batch.from_data_list([graph_data])
    batch.fingerprint = torch.tensor(fp, dtype=torch.float).unsqueeze(0)
    with torch.no_grad():
        logit = model(batch)
    return torch.sigmoid(logit).item()


def _batched_smarts_probs(model: GatnnDnn, graph_data, fingerprints: np.ndarray) -> np.ndarray:
    """P0: probabilitas model utk N varian fingerprint dlm SATU forward ter-batch.

    Eksak (bukan approksimasi): di `GatnnDnn.forward`, cabang graf
    (`graph_branch`) TIDAK bergantung pada fingerprint -- hanya pada
    x/edge_index/edge_attr. Jadi graph_repr dihitung SEKALI, lalu seluruh
    varian cukup melewati `dnn_branch` + `head` (matmul batch kecil).
    Sebelumnya tiap varian = SATU forward penuh model (exact Shapley 2^9=512
    forward serial -> sumber tail ~9.5 detik, F9).
    """
    with torch.no_grad():
        batch = torch.zeros(graph_data.x.shape[0], dtype=torch.long)
        graph_repr = model.graph_branch(
            graph_data.x, graph_data.edge_index, graph_data.edge_attr, batch
        )
        fp = torch.tensor(fingerprints, dtype=torch.float)
        dnn_repr = model.dnn_branch(fp)
        logits = model.head(
            torch.cat([graph_repr.expand(len(fingerprints), -1), dnn_repr], dim=1)
        )
        return torch.sigmoid(logits.squeeze(-1)).numpy()


def _exact_shapley(model: GatnnDnn, graph_data, base_fingerprint: np.ndarray) -> np.ndarray:
    """Nilai Shapley eksak untuk 9 fitur SMARTS biner (P0: matched-only + batched).

    - HANYA fitur yang MATCH (base flag == 1) ikut enumerasi koalisi (2^k,
      bukan 2^9). Phi utk fitur non-aktif == 0 EKSAK: base_i == 0 membuat
      fp_i tak pernah berubah oleh mask apapun -> v(S∪{i}) == v(S), persis
      properti null-player Shapley -- hasil IDENTIK dengan enumerasi 2^9.
    - SEMUA 2^k koalisi dihitung dalam SATU forward ter-batch
      (`_batched_smarts_probs`): graph_branch sekali, DNN/head untuk batch.
    """
    from math import comb

    phi = np.zeros(N_SMARTS)
    active = [int(i) for i in np.flatnonzero(base_fingerprint[SMARTS_SLICE] > 0)]
    k = len(active)
    if k == 0:
        return phi

    # Enumerasi seluruh 2^k subset fitur aktif: urutan ∅, {a}, {b}, {ab}, ...
    subset_list = list(itertools.chain.from_iterable(
        itertools.combinations(active, r) for r in range(k + 1)
    ))

    # Matriks fingerprint [2^k, FINGERPRINT_DIM]: blok SMARTS = indikator
    # keanggotaan subset; fitur non-SMARTS & non-aktif tetap pada nilai base.
    fps = np.tile(base_fingerprint, (len(subset_list), 1))
    for idx, sub in enumerate(subset_list):
        mask = np.zeros(N_SMARTS)
        mask[list(sub)] = 1.0
        fps[idx, SMARTS_SLICE] = base_fingerprint[SMARTS_SLICE] * mask

    probs = _batched_smarts_probs(model, graph_data, fps)
    v = {frozenset(sub): float(probs[idx]) for idx, sub in enumerate(subset_list)}

    for feat in active:
        others = [f for f in active if f != feat]
        for r in range(len(others) + 1):
            weight = 1.0 / (k * comb(k - 1, r))
            for combo in itertools.combinations(others, r):
                s_without = frozenset(combo)
                s_with = frozenset(combo) | {feat}
                phi[feat] += weight * (v[s_with] - v[s_without])
    return phi


def _occlusion_fallback(model: GatnnDnn, graph_data, base_fingerprint: np.ndarray) -> np.ndarray:
    """Fallback cepat O(k): kontribusi = v(semua fitur) - v(semua kecuali fitur i).

    Hanya fitur yang MATCH diproses (fitur non-aktif -> 0 EKSAK, lihat
    `_exact_shapley`). Ter-batch satu forward via `_batched_smarts_probs`.
    """
    phi = np.zeros(N_SMARTS)
    active = [int(i) for i in np.flatnonzero(base_fingerprint[SMARTS_SLICE] > 0)]
    if not active:
        return phi

    fps = np.tile(base_fingerprint, (len(active) + 1, 1))
    for i, feat in enumerate(active):
        mask = np.ones(N_SMARTS)
        mask[feat] = 0.0
        fps[i + 1, SMARTS_SLICE] = base_fingerprint[SMARTS_SLICE] * mask

    probs = _batched_smarts_probs(model, graph_data, fps)
    phi[active] = probs[0] - probs[1:]
    return phi


def explain_smarts_contribution(
    model: GatnnDnn,
    smiles: str,
    inchikey: str,
    cache_path: str | None = None,
    mol: Chem.Mol | None = None,
    graph_data: Data | None = None,
    base_fingerprint: np.ndarray | None = None,
) -> dict:
    """SMILES (sudah distandardisasi) -> {nama_pola: nilai_kontribusi}.

    Kontribusi POSITIF berarti keberadaan pola tsb MENDORONG NAIK skor risiko
    DILI, NEGATIF berarti menekan turun. Skala: perubahan probabilitas model
    (bukan logit), jadi bisa dibandingkan lintas molekul.

    Cache: in-memory bounded LRU per (model, inchikey) (P2) -- hasil identik
    tidak dihitung ulang. `cache_path` DIPERTAHANKAN hanya utk kompatibilitas
    pemanggil lama; TIDAK lagi melakukan I/O file (deprecated, abaikan).
    """
    key = _cache_key(model, inchikey)
    cached = _cache_get(_smarts_cache, _smarts_cache_lock, key)
    if cached is not None:
        return cached

    # P0: terima featurization precomputed dari pemanggil (ai_engine._featurize)
    # agar tidak dihitung ulang; hitung sendiri hanya bila tidak diberikan.
    if mol is None:
        mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"explain_smarts_contribution(): gagal parse smiles={smiles!r}")
    if graph_data is None:
        graph_data = smiles_to_graph(smiles)
    if base_fingerprint is None:
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
    _cache_set(_smarts_cache, _smarts_cache_lock, key, result)
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


def atom_masking_attribution(
    model: GatnnDnn,
    smiles: str,
    graph_data: Data | None = None,
    fingerprint: np.ndarray | None = None,
) -> list[dict]:
    """SMILES (sudah distandardisasi) -> [{"idx": i, "value": delta}, ...].

    `value` = P(molekul utuh) - P(atom i dinolkan) -- POSITIF berarti atom
    itu MENDORONG NAIK skor risiko (menghapusnya menurunkan skor), NEGATIF
    berarti atom itu justru menekan skor turun.

    Molekul tanpa ikatan (mis. ion tunggal, 1 atom) tetap valid -- ditangani
    otomatis oleh smiles_to_graph() (C3), tidak butuh percabangan khusus di sini.
    """
    # P0: terima featurization precomputed (ai_engine._featurize) bila tersedia.
    if graph_data is None or fingerprint is None:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"atom_masking_attribution(): gagal parse smiles={smiles!r}")
        graph_data = smiles_to_graph(smiles)
        fingerprint = dnn_feature_vector(mol)
    fp_tensor = torch.tensor(fingerprint, dtype=torch.float)
    n_atoms = graph_data.x.shape[0]

    # Varian 0 = molekul utuh (baseline); varian i+1 = atom i dinolkan.
    variants = [Data(x=graph_data.x, edge_index=graph_data.edge_index, edge_attr=graph_data.edge_attr)]
    for i in range(n_atoms):
        x_masked = graph_data.x.clone()
        x_masked[i, :] = 0.0
        variants.append(Data(x=x_masked, edge_index=graph_data.edge_index, edge_attr=graph_data.edge_attr))

    # P3: forward per CHUNK (bukan satu batch raksasa) -- membatasi puncak
    # memori utk molekul besar (Rifampin 60 varian, Aprotinin 455 varian):
    # batch 455 graf + fingerprint duplikat menaikkan RSS puluhan MB dan
    # mengetuk ambang OOM Hobby 512 MB (502 + restart). Hasil matematis
    # IDENTIK -- tiap varian tetap dihitung sendiri, hanya ukuran batch yang
    # dibatasi.
    n_variants = n_atoms + 1
    probs = np.empty(n_variants, dtype=np.float64)
    for start in range(0, n_variants, _ATOM_MASK_CHUNK):
        chunk_variants = variants[start:start + _ATOM_MASK_CHUNK]
        batch = Batch.from_data_list(chunk_variants)
        batch.fingerprint = fp_tensor.unsqueeze(0).repeat(len(chunk_variants), 1)
        with torch.no_grad():
            probs[start:start + len(chunk_variants)] = torch.sigmoid(model(batch)).numpy().ravel()

    baseline_prob = float(probs[0])
    return [{"idx": i, "value": round(baseline_prob - float(probs[i + 1]), 6)} for i in range(n_atoms)]


# ---------------------------------------------------------------------------
# Orkestrator gabungan -- format keluaran EXECUTION_PLAN_FIX_MODEL.md C8 langkah 3
# ---------------------------------------------------------------------------


def explain(
    model: GatnnDnn,
    smiles_standardized: str,
    inchikey: str,
    cache_path: str | None = None,
    mol: Chem.Mol | None = None,
    graph_data: Data | None = None,
    base_fingerprint: np.ndarray | None = None,
) -> dict:
    """Titik masuk tunggal C8/C10: SMILES terstandardisasi -> atribusi gugus +
    atom dalam satu struktur, di-cache in-memory per (model, inchikey).

    `atom_indices` (di dalam `groups`) merujuk ke indeks atom pada MOL yang
    diparse dari `smiles_standardized` -- sama dengan `smiles_used` yang
    disertakan di keluaran, supaya frontend menggambar dari string yang
    identik dengan yang dipakai menghitung atribusi (PROJECT_FIX_MODEL.md SS4.4).

    Cache: in-memory bounded LRU (P2) -- `cache_path` DIPERTAHANKAN hanya utk
    kompatibilitas pemanggil lama; TIDAK lagi melakukan I/O file (deprecated).
    """
    key = _cache_key(model, inchikey)
    cached = _cache_get(_explain_cache, _explain_cache_lock, key)
    if cached is not None:
        return cached

    # P0: terima featurization precomputed (ai_engine._featurize) bila tersedia;
    # seluruh tahap (gugus + atom) memakai hasil yang SAMA (satu sumber).
    if mol is None:
        mol = Chem.MolFromSmiles(smiles_standardized)
    if mol is None:
        raise ValueError(f"explain(): gagal parse smiles_standardized={smiles_standardized!r}")
    if graph_data is None:
        graph_data = smiles_to_graph(smiles_standardized)
    if base_fingerprint is None:
        base_fingerprint = dnn_feature_vector(mol)

    smarts_result = explain_smarts_contribution(
        model, smiles_standardized, inchikey,
        mol=mol, graph_data=graph_data, base_fingerprint=base_fingerprint,
    )
    atom_indices_by_group = _smarts_atom_indices(mol)
    atoms = atom_masking_attribution(
        model, smiles_standardized, graph_data=graph_data, fingerprint=base_fingerprint,
    )

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

    _cache_set(_explain_cache, _explain_cache_lock, key, result)
    return result
