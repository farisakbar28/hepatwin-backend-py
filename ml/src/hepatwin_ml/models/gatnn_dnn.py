"""TU.7 -- Arsitektur GATNN-DNN (Wibowo, Chong, & Tayara, 2025, Toxicology 514:154108).

K1 (EXECUTION_PLAN_UPSCALE.md, keputusan Ketua Tim): GCNConv versi master
diganti GATv2Conv di branch upscale. Edge feature 6-dim (features/graph.py)
dipakai lewat GATv2Conv(edge_dim=6) di kedua layer graf (UPSCALE.md SS5.1/SS5.3).

PENTING: model mengembalikan LOGIT, bukan probabilitas (UPSCALE.md SS5.1).
BCEWithLogitsLoss di training; sigmoid HANYA di lapisan inferensi setelah
kalibrasi (TU.10). Versi master menaruh nn.Sigmoid() di forward() -- TIDAK
diwarisi ke sini, itu justru bug yang diperbaiki K1.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Batch
from torch_geometric.nn import GATv2Conv, global_mean_pool

from hepatwin_ml.features.fingerprints import FINGERPRINT_DIM
from hepatwin_ml.features.graph import EDGE_FEATURE_DIM, NODE_FEATURE_DIM

GRAPH_BRANCH_OUT_DIM = 256
DNN_BRANCH_OUT_DIM = 128
CONCAT_DIM = GRAPH_BRANCH_OUT_DIM + DNN_BRANCH_OUT_DIM  # 384


class GraphBranch(nn.Module):
    def __init__(self, node_dim: int = NODE_FEATURE_DIM, edge_dim: int = EDGE_FEATURE_DIM):
        super().__init__()
        self.gat1 = GATv2Conv(node_dim, 64, heads=4, edge_dim=edge_dim, concat=True)
        self.dropout1 = nn.Dropout(0.2)
        self.gat2 = GATv2Conv(256, 64, heads=4, edge_dim=edge_dim, concat=True)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor, batch: torch.Tensor) -> torch.Tensor:
        h = self.gat1(x, edge_index, edge_attr=edge_attr)
        h = F.elu(h)
        h = self.dropout1(h)
        h = self.gat2(h, edge_index, edge_attr=edge_attr)
        h = F.elu(h)
        return global_mean_pool(h, batch)  # [batch, 256]


class DnnBranch(nn.Module):
    def __init__(self, in_dim: int = FINGERPRINT_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
        )

    def forward(self, fingerprint: torch.Tensor) -> torch.Tensor:
        return self.net(fingerprint)  # [batch, 128]


class GatnnDnn(nn.Module):
    """Model hybrid dua-cabang. `forward` menerima Batch (torch_geometric) yang
    sudah punya atribut `fingerprint` [batch, 1200] tertempel per-graph (lihat
    train.py untuk cara menempelkannya saat membangun Data/Batch)."""

    def __init__(self):
        super().__init__()
        self.graph_branch = GraphBranch()
        self.dnn_branch = DnnBranch()
        self.head = nn.Sequential(
            nn.Linear(CONCAT_DIM, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
        )

    def forward(self, batch: Batch) -> torch.Tensor:
        graph_repr = self.graph_branch(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        dnn_repr = self.dnn_branch(batch.fingerprint)
        combined = torch.cat([graph_repr, dnn_repr], dim=1)
        logit = self.head(combined)  # [batch, 1] -- LOGIT, bukan probabilitas
        return logit.squeeze(-1)
