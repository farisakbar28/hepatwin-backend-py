import numpy as np
import torch

from hepatwin_ml.explain import (
    N_SMARTS,
    _exact_shapley,
    _occlusion_fallback,
    _predict_with_smarts_mask,
    _smarts_atom_indices,
    atom_masking_attribution,
    explain,
    explain_smarts_contribution,
)
from hepatwin_ml.features.fingerprints import dnn_feature_vector
from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.features.smarts import SMARTS_PATTERNS, SMARTS_SLICE
from hepatwin_ml.models.gatnn_dnn import GatnnDnn
from rdkit import Chem


def test_shapley_efficiency_property():
    """Properti efisiensi Shapley: jumlah phi_i harus sama dengan
    v(semua fitur ada) - v(semua fitur absen)."""
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    smiles = "CC(=O)Nc1ccc(O)cc1"
    mol = Chem.MolFromSmiles(smiles)
    graph_data = smiles_to_graph(smiles)
    base_fp = dnn_feature_vector(mol)

    phi = _exact_shapley(model, graph_data, base_fp)

    v_full = _predict_with_smarts_mask(model, graph_data, base_fp, np.ones(N_SMARTS))
    v_empty = _predict_with_smarts_mask(model, graph_data, base_fp, np.zeros(N_SMARTS))

    assert abs(phi.sum() - (v_full - v_empty)) < 1e-6


def test_occlusion_fallback_matches_sequential_reference():
    """P0: fallback occlusion ter-batch (`_batched_smarts_probs`) harus
    identik dengan loop serial lama (v_full - v_except_i) dan 0 untuk fitur
    SMARTS yang tidak match (kontribusi non-aktif == 0 EKSAK)."""
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    smiles = "CC(=O)Nc1ccc(O)cc1"
    mol = Chem.MolFromSmiles(smiles)
    graph_data = smiles_to_graph(smiles)
    base_fp = dnn_feature_vector(mol)

    phi = _occlusion_fallback(model, graph_data, base_fp)
    assert phi.shape == (N_SMARTS,)

    v_full = _predict_with_smarts_mask(model, graph_data, base_fp, np.ones(N_SMARTS))
    ref = np.zeros(N_SMARTS)
    for i in range(N_SMARTS):
        mask = np.ones(N_SMARTS)
        mask[i] = 0.0
        ref[i] = v_full - _predict_with_smarts_mask(model, graph_data, base_fp, mask)

    assert np.allclose(phi, ref, atol=1e-6)
    for i in np.flatnonzero(base_fp[SMARTS_SLICE] == 0):
        assert phi[i] == 0.0


def test_explain_smarts_contribution_returns_all_pattern_names(tmp_path):
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    cache_path = str(tmp_path / "shap_cache.json")
    result = explain_smarts_contribution(model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-1", cache_path=cache_path)

    assert set(result["contributions"].keys()) == {p.name for p in SMARTS_PATTERNS}
    assert result["method"] == "exact_shapley"


def test_explain_smarts_contribution_uses_cache_on_second_call(tmp_path):
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    cache_path = str(tmp_path / "shap_cache.json")
    r1 = explain_smarts_contribution(model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-2", cache_path=cache_path)
    r2 = explain_smarts_contribution(model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-2", cache_path=cache_path)
    assert r1 == r2


def test_atom_masking_attribution_returns_one_entry_per_atom():
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    smiles = "CC(=O)Nc1ccc(O)cc1"  # parasetamol, 11 atom berat
    mol = Chem.MolFromSmiles(smiles)
    atoms = atom_masking_attribution(model, smiles)

    assert len(atoms) == mol.GetNumAtoms() == 11
    assert {a["idx"] for a in atoms} == set(range(11))
    assert all(isinstance(a["value"], float) for a in atoms)


def test_atom_masking_attribution_handles_single_atom_molecule():
    """C8/C3 AC: molekul tanpa ikatan (ion tunggal) tidak boleh crash."""
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    atoms = atom_masking_attribution(model, "[Na+]")
    assert len(atoms) == 1
    assert atoms[0]["idx"] == 0


def test_smarts_atom_indices_empty_for_non_matching_pattern():
    mol = Chem.MolFromSmiles("CC")  # etana -- tidak match satu pun dari 9 pola
    result = _smarts_atom_indices(mol)
    assert all(indices == [] for indices in result.values())


def test_explain_method_field_is_honest_masking_not_shap(tmp_path):
    """Aturan kejujuran C8: field method wajib menyebut metode SEBENARNYA."""
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()
    cache_path = str(tmp_path / "explain_cache.json")
    result = explain(model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-EXPLAIN-1", cache_path=cache_path)
    assert result["method"] == "masking_attribution"


def test_explain_output_schema_matches_c8_contract(tmp_path):
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    cache_path = str(tmp_path / "explain_cache.json")
    result = explain(model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-EXPLAIN-2", cache_path=cache_path)

    assert set(result.keys()) == {"method", "groups", "atoms", "smiles_used"}
    assert result["smiles_used"] == "CC(=O)Nc1ccc(O)cc1"
    for group in result["groups"]:
        assert set(group.keys()) == {"name", "value", "atom_indices"}
        assert len(group["atom_indices"]) > 0  # grup tidak-match wajib dibuang
    for atom in result["atoms"]:
        assert set(atom.keys()) == {"idx", "value"}


def test_explain_no_smarts_match_returns_empty_groups_not_crash(tmp_path):
    """C8 AC: molekul tanpa satu pun match SMARTS -> groups=[], bukan crash."""
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()
    cache_path = str(tmp_path / "explain_cache.json")
    result = explain(model, "CC", "FAKE-INCHIKEY-ETHANE", cache_path=cache_path)
    assert result["groups"] == []
    assert len(result["atoms"]) == 2


def test_explain_uses_cache_on_second_call(tmp_path):
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()
    cache_path = str(tmp_path / "explain_cache.json")
    r1 = explain(model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-EXPLAIN-3", cache_path=cache_path)
    r2 = explain(model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-EXPLAIN-3", cache_path=cache_path)
    assert r1 == r2


def test_explain_atom_indices_consistent_with_smiles_used(tmp_path):
    """atom_indices harus valid untuk mol yang diparse dari smiles_used --
    tidak boleh melebihi jumlah atom di molekul tsb."""
    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()
    smiles = "CC(=O)Nc1ccc(O)cc1"
    cache_path = str(tmp_path / "explain_cache.json")
    result = explain(model, smiles, "FAKE-INCHIKEY-EXPLAIN-4", cache_path=cache_path)
    mol = Chem.MolFromSmiles(result["smiles_used"])
    n_atoms = mol.GetNumAtoms()
    for group in result["groups"]:
        assert all(0 <= idx < n_atoms for idx in group["atom_indices"])
    assert all(0 <= a["idx"] < n_atoms for a in result["atoms"])


def test_smarts_cache_skips_recompute_on_second_call(monkeypatch):
    """P2: cache in-memory LRU -- panggilan kedua dengan (model, inchikey) sama
    TIDAK boleh menghitung ulang. `r1 == r2` saja tidak cukup membuktikan hit
    (komputasi deterministik); di sini `_exact_shapley` di-patch agar raise
    bila dipanggil LEBIH dari sekali."""
    import hepatwin_ml.explain as explain_module

    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    original = explain_module._exact_shapley
    calls = {"n": 0}

    def guarded(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise AssertionError("_exact_shapley terpanggil lagi -- smarts cache tidak hit!")
        return original(*args, **kwargs)

    monkeypatch.setattr(explain_module, "_exact_shapley", guarded)
    explain_module.explain_smarts_contribution(
        model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-CACHEHIT-SMARTS"
    )
    explain_module.explain_smarts_contribution(
        model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-CACHEHIT-SMARTS"
    )
    assert calls["n"] == 1


def test_explain_cache_skips_recompute_on_second_call(monkeypatch):
    """P2: cache `explain()` (cache terpisah dari smarts) -- panggilan kedua
    dengan (model, inchikey) sama TIDAK memanggil tahap komputasi apa pun
    (gugus + atom di-patch agar raise bila dipanggil lagi)."""
    import hepatwin_ml.explain as explain_module

    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    orig_smarts = explain_module.explain_smarts_contribution
    orig_atoms = explain_module.atom_masking_attribution
    calls = {"n": 0}

    def guarded(fn):
        def inner(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] > 2:  # tepat 2 pemanggilan pada panggilan explain() pertama
                raise AssertionError("tahap hitung dipanggil lagi -- explain cache tidak hit!")
            return fn(*args, **kwargs)
        return inner

    monkeypatch.setattr(explain_module, "explain_smarts_contribution", guarded(orig_smarts))
    monkeypatch.setattr(explain_module, "atom_masking_attribution", guarded(orig_atoms))
    explain_module.explain(
        model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-CACHEHIT-EXPLAIN"
    )
    explain_module.explain(
        model, "CC(=O)Nc1ccc(O)cc1", "FAKE-INCHIKEY-CACHEHIT-EXPLAIN"
    )
    assert calls["n"] == 2


def test_cache_bounded_evicts_oldest_entry():
    """P2: cache in-memory bounded LRU -- saat penuh, entri terlama ter-evict;
    ukuran tidak pernah melebihi maxsize (diuji langsung via `_cache_set`,
    tanpa komputasi model, sehingga cepat walau maxsize besar)."""
    import hepatwin_ml.explain as explain_module
    from hepatwin_ml.explain import _cache_get, _cache_key, _cache_set

    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    maxsize = explain_module._EXPLAIN_CACHE_MAXSIZE
    assert maxsize > 0
    try:
        for i in range(maxsize + 1):
            _cache_set(
                explain_module._explain_cache,
                explain_module._explain_cache_lock,
                _cache_key(model, f"IK-BOUND-{i}"),
                {"i": i},
            )
        assert len(explain_module._explain_cache) == maxsize
        # entri terlama (IK-BOUND-0) ter-evict; entri terbaru tetap ada
        assert (
            _cache_get(
                explain_module._explain_cache,
                explain_module._explain_cache_lock,
                _cache_key(model, "IK-BOUND-0"),
            )
            is None
        )
        assert _cache_get(
            explain_module._explain_cache,
            explain_module._explain_cache_lock,
            _cache_key(model, f"IK-BOUND-{maxsize}"),
        ) == {"i": maxsize}
    finally:
        # bersihkan entri test ini agar tidak bocor ke test lain (cache global)
        with explain_module._explain_cache_lock:
            for i in range(maxsize + 1):
                explain_module._explain_cache.pop(_cache_key(model, f"IK-BOUND-{i}"), None)


def test_atom_masking_chunk_equals_full_batch(monkeypatch):
    """P3: ekivalensi per-chunk vs batch penuh -- konstruksi varian per-chunk
    (lazy) + forward terbatas (`_ATOM_MASK_CHUNK`) TIDAK boleh mengubah hasil
    matematis dibanding batch raksasa satu-pass. Di-pin sebagai test regresi
    agar refactor berikutnya tidak merusak invariant ini tanpa terdeteksi.
    """
    import hepatwin_ml.explain as explain_module

    torch.manual_seed(0)
    model = GatnnDnn()
    model.eval()

    smiles = "CC(=O)Nc1ccc(O)cc1"  # parasetamol, 11 atom -> 12 varian
    mol = Chem.MolFromSmiles(smiles)
    graph_data = smiles_to_graph(smiles)
    fp = dnn_feature_vector(mol)

    orig = explain_module._ATOM_MASK_CHUNK
    try:
        explain_module._ATOM_MASK_CHUNK = 2  # paksa multi-chunk (12 varian -> 6 chunk)
        chunked = explain_module.atom_masking_attribution(
            model, smiles, graph_data=graph_data, fingerprint=fp
        )
        explain_module._ATOM_MASK_CHUNK = 10**6  # batch penuh (perilaku lama)
        full = explain_module.atom_masking_attribution(
            model, smiles, graph_data=graph_data, fingerprint=fp
        )
    finally:
        explain_module._ATOM_MASK_CHUNK = orig

    assert chunked == full  # dict {idx, value} identik (value dibulatkan 6 desimal)
