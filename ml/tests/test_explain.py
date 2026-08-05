import numpy as np
import torch

from hepatwin_ml.explain import (
    N_SMARTS,
    _exact_shapley,
    _predict_with_smarts_mask,
    _smarts_atom_indices,
    atom_masking_attribution,
    explain,
    explain_smarts_contribution,
)
from hepatwin_ml.features.fingerprints import dnn_feature_vector
from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.features.smarts import SMARTS_PATTERNS
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
