import torch
from rdkit import Chem
from torch_geometric.data import Batch

from hepatwin_ml.features.fingerprints import dnn_feature_vector
from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

_SMILES = ["c1ccccc1O", "CC(=O)Nc1ccc(O)cc1", "CCO"]


def _make_batch() -> Batch:
    graphs = []
    for smi in _SMILES:
        g = smiles_to_graph(smi)
        mol = Chem.MolFromSmiles(smi)
        g.fingerprint = torch.tensor(dnn_feature_vector(mol), dtype=torch.float).unsqueeze(0)
        graphs.append(g)
    return Batch.from_data_list(graphs)


def test_forward_pass_returns_one_logit_per_graph():
    model = GatnnDnn()
    batch = _make_batch()
    out = model(batch)
    assert out.shape == (len(_SMILES),)


def test_output_is_raw_logit_not_probability():
    """UPSCALE.md SS5.1: model TIDAK boleh menaruh sigmoid di forward()."""
    model = GatnnDnn()
    batch = _make_batch()
    out = model(batch)
    # Logit mentah dari layer Linear tanpa sigmoid secara umum bisa < 0 atau > 1;
    # yang penting dipastikan adalah TIDAK ada sigmoid di graf komputasi forward().
    assert not any(isinstance(m, torch.nn.Sigmoid) for m in model.modules())


def test_gradients_flow_through_both_branches():
    model = GatnnDnn()
    batch = _make_batch()
    out = model(batch)
    loss = out.sum()
    loss.backward()

    graph_grad = model.graph_branch.gat1.lin_l.weight.grad
    dnn_grad = model.dnn_branch.net[0].weight.grad
    assert graph_grad is not None and graph_grad.abs().sum() > 0
    assert dnn_grad is not None and dnn_grad.abs().sum() > 0
