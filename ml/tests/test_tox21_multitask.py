import torch

from hepatwin_ml.stretch.tox21_multitask import (
    N_TOX21_TASKS,
    GatnnDnnWithTox21,
    masked_bce_with_logits,
)


def test_masked_bce_ignores_nan_targets():
    logits = torch.tensor([[10.0, -10.0, 5.0]])
    targets_all_correct = torch.tensor([[1.0, 0.0, 1.0]])
    targets_with_nan_where_wrong = torch.tensor([[1.0, 0.0, float("nan")]])

    loss_all = masked_bce_with_logits(logits, targets_all_correct)
    loss_masked = masked_bce_with_logits(logits, targets_with_nan_where_wrong)

    # Karena elemen ke-3 (logit besar, akan salah bila target beda) di-mask NaN,
    # loss yang di-mask harus sama seperti dihitung hanya atas 2 elemen pertama.
    expected = masked_bce_with_logits(logits[:, :2], targets_all_correct[:, :2])
    assert torch.allclose(loss_masked, expected, atol=1e-5)
    assert loss_masked.item() < loss_all.item() + 1.0  # sanity: tidak meledak


def test_masked_bce_all_nan_returns_zero():
    logits = torch.tensor([[1.0, 2.0]])
    targets = torch.tensor([[float("nan"), float("nan")]])
    loss = masked_bce_with_logits(logits, targets)
    assert loss.item() == 0.0


def test_gatnn_dnn_with_tox21_forward_tox21_shape():
    from rdkit import Chem

    from hepatwin_ml.features.fingerprints import dnn_feature_vector
    from hepatwin_ml.features.graph import smiles_to_graph
    from torch_geometric.data import Batch

    torch.manual_seed(0)
    model = GatnnDnnWithTox21()
    model.eval()

    smiles = "CC(=O)Nc1ccc(O)cc1"
    g = smiles_to_graph(smiles)
    mol = Chem.MolFromSmiles(smiles)
    g.fingerprint = torch.tensor(dnn_feature_vector(mol), dtype=torch.float).unsqueeze(0)
    batch = Batch.from_data_list([g])

    dili_out = model(batch)
    tox21_out = model.forward_tox21(batch)

    assert dili_out.shape == (1,)
    assert tox21_out.shape == (1, N_TOX21_TASKS)
