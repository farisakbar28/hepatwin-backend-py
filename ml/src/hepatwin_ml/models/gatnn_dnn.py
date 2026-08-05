"""TU.7 -- Arsitektur GATNN-DNN (Wibowo, Chong, & Tayara, 2025, Toxicology 514:154108).

K1 (EXECUTION_PLAN_UPSCALE.md, keputusan Ketua Tim): GCNConv versi master
diganti GATv2Conv di branch upscale. Edge feature 6-dim (features/graph.py)
dipakai lewat GATv2Conv(edge_dim=6) di kedua layer graf (UPSCALE.md SS5.1/SS5.3).

PENTING: model mengembalikan LOGIT, bukan probabilitas (UPSCALE.md SS5.1).
BCEWithLogitsLoss di training; sigmoid HANYA di lapisan inferensi setelah
kalibrasi (TU.10). Versi master menaruh nn.Sigmoid() di forward() -- TIDAK
diwarisi ke sini, itu justru bug yang diperbaiki K1.

TU.20 (v3.0): `hidden` dan `dropout` jadi parameter konstruktor -- UPSCALE.md
SS13.3 (Panduan_Training...md Ketua Tim) meminta keduanya masuk ruang pencarian
hyperparameter (hidden in {64,128}, dropout in {0.2,0.3,0.4}). Nilai default
(64, 0.2/0.3 berbeda per layer) TETAP jadi default parameter -- sama seperti
UPSCALE.md SS5.1 -- tapi sekarang bisa diubah pemanggil untuk nested CV.
`dropout` diterapkan seragam ke SEMUA layer dropout di model (GAT + DNN branch
+ head) -- interpretasi paling sederhana dari satu nilai "dropout" di ruang
pencarian, bukan per-layer terpisah.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Batch
from torch_geometric.nn import GATv2Conv, global_mean_pool

from hepatwin_ml.features.fingerprints import FINGERPRINT_DIM
from hepatwin_ml.features.graph import EDGE_FEATURE_DIM, NODE_FEATURE_DIM

GAT_HEADS = 4
DEFAULT_HIDDEN = 64
DEFAULT_DROPOUT = 0.3
DNN_BRANCH_OUT_DIM = 128


class GraphBranch(nn.Module):
    def __init__(
        self,
        node_dim: int = NODE_FEATURE_DIM,
        edge_dim: int = EDGE_FEATURE_DIM,
        hidden: int = DEFAULT_HIDDEN,
        dropout: float = DEFAULT_DROPOUT,
    ):
        super().__init__()
        self.out_dim = hidden * GAT_HEADS
        self.gat1 = GATv2Conv(node_dim, hidden, heads=GAT_HEADS, edge_dim=edge_dim, concat=True)
        self.dropout1 = nn.Dropout(dropout)
        self.gat2 = GATv2Conv(self.out_dim, hidden, heads=GAT_HEADS, edge_dim=edge_dim, concat=True)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        h = self.gat1(x, edge_index, edge_attr=edge_attr)
        h = F.elu(h)
        h = self.dropout1(h)
        h = self.gat2(h, edge_index, edge_attr=edge_attr)
        h = F.elu(h)
        return global_mean_pool(h, batch)  # [batch, hidden*GAT_HEADS]


class DnnBranch(nn.Module):
    def __init__(self, in_dim: int = FINGERPRINT_DIM, dropout: float = DEFAULT_DROPOUT):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(self, fingerprint: torch.Tensor) -> torch.Tensor:
        return self.net(fingerprint)  # [batch, 128]


class GatnnDnn(nn.Module):
    """Model hybrid dua-cabang. `forward` menerima Batch (torch_geometric) yang
    sudah punya atribut `fingerprint` [batch, 1200] tertempel per-graph (lihat
    train.py untuk cara menempelkannya saat membangun Data/Batch)."""

    def __init__(self, hidden: int = DEFAULT_HIDDEN, dropout: float = DEFAULT_DROPOUT):
        super().__init__()
        self.graph_branch = GraphBranch(hidden=hidden, dropout=dropout)
        self.dnn_branch = DnnBranch(dropout=dropout)
        concat_dim = self.graph_branch.out_dim + DNN_BRANCH_OUT_DIM
        self.head = nn.Sequential(
            nn.Linear(concat_dim, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 1),
        )

    def forward(self, batch: Batch) -> torch.Tensor:
        graph_repr = self.graph_branch(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        dnn_repr = self.dnn_branch(batch.fingerprint)
        combined = torch.cat([graph_repr, dnn_repr], dim=1)
        logit = self.head(combined)  # [batch, 1] -- LOGIT, bukan probabilitas
        return logit.squeeze(-1)
