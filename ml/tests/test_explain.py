import numpy as np
import torch

from hepatwin_ml.explain import (
    N_SMARTS,
    _exact_shapley,
    _predict_with_smarts_mask,
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
