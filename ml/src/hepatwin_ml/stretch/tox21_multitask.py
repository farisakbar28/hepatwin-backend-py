"""TU.16 (stretch, opsional) -- Tox21 multi-task auxiliary head.

Tox21 dipakai sebagai sinyal tambahan TANPA mencemari label DILI (UPSCALE.md
SS3.4): representasi graf 256-dim yang sama dipakai model utama (GatnnDnn)
dilekatkan cabang linear kedua yang memprediksi 12 label assay Tox21
(multi-label, BCEWithLogitsLoss per kolom, NaN diabaikan).

Tox21 (~7831 senyawa, mayoritas bahan kimia industri) TIDAK overlap dengan
dataset DILI -- manfaatnya lewat representasi graf bersama (multi-task
learning), bukan lewat baris tambahan berlabel DILI. Ini kenapa arsitektur di
sini secara sengaja HANYA memakai graph_branch (bukan dnn_branch/fingerprint)
untuk kepala Tox21: representasi yang mau diperkaya adalah representasi graf.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch_geometric.data import Batch, Data
from torch_geometric.loader import DataLoader

from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TOX21_TASK_COLUMNS = [
    "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD",
    "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53",
]
N_TOX21_TASKS = len(TOX21_TASK_COLUMNS)


def load_tox21_graphs(csv_path: str) -> list[Data]:
    """CSV Tox21 mentah -> list Data (x, edge_index, edge_attr, y=[12] dgn NaN
    untuk label hilang). Baris dengan SMILES gagal parse dibuang."""
    df = pd.read_csv(csv_path)
    graphs = []
    n_failed = 0
    for _, row in df.iterrows():
        g = smiles_to_graph(row["smiles"])
        if g is None:
            n_failed += 1
            continue
        labels = row[TOX21_TASK_COLUMNS].to_numpy(dtype=np.float64)
        g.y = torch.tensor(labels, dtype=torch.float).unsqueeze(0)  # NaN dipertahankan
        graphs.append(g)
    logger.info("Tox21 dimuat: %d graf valid, %d gagal parse SMILES", len(graphs), n_failed)
    return graphs


def masked_bce_with_logits(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """BCEWithLogitsLoss per elemen, mengabaikan target NaN (label Tox21 hilang)."""
    mask = ~torch.isnan(targets)
    if mask.sum() == 0:
        return torch.tensor(0.0, requires_grad=True)
    safe_targets = torch.where(mask, targets, torch.zeros_like(targets))
    loss_per_elem = nn.functional.binary_cross_entropy_with_logits(logits, safe_targets, reduction="none")
    return (loss_per_elem * mask.float()).sum() / mask.sum()


class GatnnDnnWithTox21(GatnnDnn):
    """GatnnDnn + kepala kedua utk 12 label Tox21, dari representasi graf
    256-dim yang sama (bukan dari cabang DNN/fingerprint)."""

    def __init__(self):
        super().__init__()
        self.tox21_head = nn.Linear(self.graph_branch.out_dim, N_TOX21_TASKS)

    def forward_tox21(self, batch: Batch) -> torch.Tensor:
        graph_repr = self.graph_branch(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        return self.tox21_head(graph_repr)


def train_gatnn_with_tox21_auxiliary(
    dili_train_graphs: list[Data],
    dili_val_graphs: list[Data],
    tox21_graphs: list[Data],
    seed: int,
    lambda_tox21: float = 0.1,
    max_epochs: int = 300,
    patience: int = 30,
    batch_size: int = 32,
    verbose: bool = False,
) -> tuple[GatnnDnnWithTox21, np.ndarray, np.ndarray]:
    """Sama seperti train.train_gatnn, tapi tiap langkah optimisasi juga
    menambah loss_tox21 * lambda_tox21 dari batch Tox21 terpisah (interleaved)."""
    from sklearn.metrics import roc_auc_score

    torch.manual_seed(seed)
    np.random.seed(seed)

    model = GatnnDnnWithTox21()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=10)

    train_labels = np.array([g.y.item() for g in dili_train_graphs])
    n_pos = max(int(train_labels.sum()), 1)
    n_neg = max(len(train_labels) - n_pos, 1)
    pos_weight = torch.tensor([n_neg / n_pos], dtype=torch.float)
    dili_loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    dili_loader = DataLoader(dili_train_graphs, batch_size=batch_size, shuffle=True)
    tox21_loader = DataLoader(tox21_graphs, batch_size=batch_size, shuffle=True)
    val_batch = Batch.from_data_list(dili_val_graphs)
    val_y = np.array([g.y.item() for g in dili_val_graphs])

    best_val_auc = -np.inf
    best_state = None
    epochs_no_improve = 0
    best_val_probs = None

    for epoch in range(max_epochs):
        model.train()
        tox21_iter = iter(tox21_loader)
        for dili_batch in dili_loader:
            try:
                tox21_batch = next(tox21_iter)
            except StopIteration:
                tox21_iter = iter(tox21_loader)
                tox21_batch = next(tox21_iter)

            optimizer.zero_grad()
            dili_logits = model(dili_batch)
            loss_dili = dili_loss_fn(dili_logits, dili_batch.y)

            tox21_logits = model.forward_tox21(tox21_batch)
            loss_tox21 = masked_bce_with_logits(tox21_logits, tox21_batch.y)

            total_loss = loss_dili + lambda_tox21 * loss_tox21
            total_loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(val_batch)
            val_probs = torch.sigmoid(val_logits).numpy()
        val_auc = roc_auc_score(val_y, val_probs) if len(set(val_y)) > 1 else 0.5
        scheduler.step(val_auc)

        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            best_val_probs = val_probs
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if verbose and epoch % 20 == 0:
            logger.info("epoch %d loss_dili=%.4f loss_tox21=%.4f val_auc=%.4f best=%.4f",
                        epoch, loss_dili.item(), loss_tox21.item(), val_auc, best_val_auc)

        if epochs_no_improve >= patience:
            if verbose:
                logger.info("Early stopping di epoch %d (best_val_auc=%.4f)", epoch, best_val_auc)
            break

    model.load_state_dict(best_state)
    return model, val_y, best_val_probs
