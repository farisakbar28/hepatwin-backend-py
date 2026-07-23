"""06a — Implementasi training dan 5-fold CV untuk GNN.

Dasar: PRD §7, §8.3 · Arsitektur §D.4 · EXECUTION_PLAN.md T1.10.

Aturan:
- Impor featurizer dari app.chem.features jika diperlukan untuk cabang struktural.
- Gunakan RDKit smiles_to_graph_and_features dari app.services.ai_engine atau define di sini secara reproducible.
- Regularisasi kuat: dropout 0.3–0.5, weight decay, early stopping pada validation fold.
- class_weight seimbang.
- Seed tetap + torch.use_deterministic_algorithms(True) atau torch.manual_seed(42).
- Simpan metrik ke ml/reports/06a_gnn.json.
"""
import json
import logging
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    matthews_corrcoef,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from torch_geometric.loader import DataLoader

# Barrier: pastikan root repo di sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _common import DATA_PROCESSED, REPORTS, write_report

from app.services.ai_engine import HybridGNN, smiles_to_graph_and_features

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    # Gunakan setting deterministik
    torch.use_deterministic_algorithms(True, warn_only=True)
    # Set PyTorch untuk deterministik di Windows CPU/CUDA
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def calculate_metrics(y_true: np.ndarray, y_pred_prob: np.ndarray) -> dict[str, float]:
    """Hitung metrik evaluasi binary classification."""
    y_pred = (y_pred_prob >= 0.5).astype(int)
    
    acc = accuracy_score(y_true, y_pred)
    # Cegah error jika semua label sama dalam mini-fold
    try:
        auroc = roc_auc_score(y_true, y_pred_prob)
    except ValueError:
        auroc = 0.5
        
    precision, recall, _ = precision_recall_curve(y_true, y_pred_prob)
    auc_pr = auc(recall, precision)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    mcc = matthews_corrcoef(y_true, y_pred)
    
    return {
        "accuracy": float(acc),
        "auroc": float(auroc),
        "auc_pr": float(auc_pr),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "mcc": float(mcc)
    }


class DILIGraphDataset(torch.utils.data.Dataset):
    def __init__(self, df: pd.DataFrame):
        self.df = df.reset_index(drop=True)
        self.data_list = []
        self.labels = []
        
        for idx, row in self.df.iterrows():
            data, struct_feat = smiles_to_graph_and_features(row["smiles"])
            if data is not None and struct_feat is not None:
                # Simpan juga label
                data.y = torch.tensor([row["label"]], dtype=torch.float)
                # Simpan structural feature ke data object
                data.struct_features = struct_feat.squeeze(0)  # shape (num_struct_features,)
                self.data_list.append(data)
                self.labels.append(row["label"])
            else:
                logger.warning("Gagal memproses SMILES pada baris %d: %s", idx, row["smiles"])
                
    def __len__(self):
        return len(self.data_list)
        
    def __getitem__(self, idx):
        return self.data_list[idx]


def train_epoch(model, loader, optimizer, criterion, device, class_weights):
    model.train()
    total_loss = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        # Reshape struct_features dari 1D batch concatenation
        struct_feat = batch.struct_features.view(batch.num_graphs, -1)
        pred = model(batch.x, batch.edge_index, batch.batch, struct_feat).squeeze(-1)
        
        # Hitung weighted loss
        weight = batch.y * class_weights[1] + (1 - batch.y) * class_weights[0]
        loss = criterion(pred, batch.y)
        loss = (loss * weight).mean()
        
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
    return total_loss / len(loader.dataset)


def eval_model(model, loader, device):
    model.eval()
    all_preds = []
    all_y = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            struct_feat = batch.struct_features.view(batch.num_graphs, -1)
            pred = model(batch.x, batch.edge_index, batch.batch, struct_feat).squeeze(-1)
            all_preds.extend(pred.cpu().numpy())
            all_y.extend(batch.y.cpu().numpy())
    return np.array(all_y), np.array(all_preds)


def main():
    seed = 42
    set_seed(seed)
    
    train_path = DATA_PROCESSED / "train.csv"
    if not train_path.exists():
        logger.error("File train.csv tidak ditemukan di %s. Jalankan 04_dedup_split.py dulu.", train_path)
        sys.exit(1)
        
    df_train = pd.read_csv(train_path)
    logger.info("Membaca %d baris data training dari %s", len(df_train), train_path)
    
    # Buat dataset graf
    dataset = DILIGraphDataset(df_train)
    logger.info("Berhasil membuat dataset graf dengan %d molekul", len(dataset))
    
    labels = np.array(dataset.labels)
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Menggunakan device: %s", device)
    
    # Hitung class weights
    pos_count = np.sum(labels == 1)
    neg_count = np.sum(labels == 0)
    total_count = len(labels)
    w_pos = total_count / (2.0 * pos_count) if pos_count > 0 else 1.0
    w_neg = total_count / (2.0 * neg_count) if neg_count > 0 else 1.0
    class_weights = torch.tensor([w_neg, w_pos], dtype=torch.float, device=device)
    logger.info("Class weights: Neg=%.4f, Pos=%.4f", w_neg, w_pos)
    
    folds_metrics = []
    epochs = 60
    batch_size = 32
    
    for fold, (train_idx, val_idx) in enumerate(cv.split(np.arange(len(dataset)), labels), 1):
        # Subset dataset
        train_subset = torch.utils.data.Subset(dataset, train_idx)
        val_subset = torch.utils.data.Subset(dataset, val_idx)
        
        train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_subset, batch_size=batch_size, shuffle=False)
        
        # GNN model setup
        # num_struct_features disesuaikan dengan jumlah SMARTS_LIBRARY (9)
        from app.chem.smarts_library import SMARTS_LIBRARY
        num_struct_features = len(SMARTS_LIBRARY)
        
        model = HybridGNN(
            node_features=9,
            hidden_channels=64,
            num_struct_features=num_struct_features,
            num_classes=1
        ).to(device)
        
        # Tambahkan weight decay (regularisasi L2)
        optimizer = optim.Adam(model.parameters(), lr=0.005, weight_decay=1e-4)
        criterion = nn.BCELoss(reduction='none') # Kita reduksi secara manual dengan class weight
        
        best_auroc = 0.0
        best_metrics = None
        
        for epoch in range(1, epochs + 1):
            train_epoch(model, train_loader, optimizer, criterion, device, class_weights)
            y_val, y_val_prob = eval_model(model, val_loader, device)
            fold_metrics = calculate_metrics(y_val, y_val_prob)
            
            # Cari best model berdasarkan validation AUROC
            if fold_metrics["auroc"] > best_auroc:
                best_auroc = fold_metrics["auroc"]
                best_metrics = fold_metrics
                
        folds_metrics.append(best_metrics)
        logger.info(
            "Fold %d - Best AUROC: %.4f | Accuracy: %.4f | MCC: %.4f",
            fold, best_metrics["auroc"], best_metrics["accuracy"], best_metrics["mcc"]
        )
        
    # Agregasi metrik
    mean_metrics = {}
    std_metrics = {}
    for key in folds_metrics[0].keys():
        values = [m[key] for m in folds_metrics]
        mean_metrics[key] = float(np.mean(values))
        std_metrics[key] = float(np.std(values))
        
    logger.info("=== Rata-rata Metrik GNN 5-Fold CV ===")
    for key, val in mean_metrics.items():
        logger.info("%s: %.4f (std: %.4f)", key, val, std_metrics[key])
        
    output_json = {
        "seed": seed,
        "n_samples": len(dataset),
        "mean_metrics": mean_metrics,
        "std_metrics": std_metrics,
        "folds": folds_metrics
    }
    
    # Simpan laporan json
    json_path = REPORTS / "06a_gnn.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=4)
    logger.info("Menyimpan metrik GNN ke %s", json_path)
    
    # Tulis laporan markdown
    md_lines = [
        "# 06a Laporan Model GNN (HybridGNN)",
        "",
        f"- **Jumlah Sampel Training**: {len(dataset)}",
        f"- **Evaluasi**: 5-Fold Stratified Cross-Validation (Seed: {seed})",
        "",
        "## Performa Rata-rata 5-Fold CV",
        "",
        "| Metrik | Rata-rata (Mean) | Standar Deviasi (Std) |",
        "|---|---|---|",
        f"| Accuracy | {mean_metrics['accuracy']:.4f} | {std_metrics['accuracy']:.4f} |",
        f"| AUROC | {mean_metrics['auroc']:.4f} | {std_metrics['auroc']:.4f} |",
        f"| AUC-PR | {mean_metrics['auc_pr']:.4f} | {std_metrics['auc_pr']:.4f} |",
        f"| Sensitivity | {mean_metrics['sensitivity']:.4f} | {std_metrics['sensitivity']:.4f} |",
        f"| Specificity | {mean_metrics['specificity']:.4f} | {std_metrics['specificity']:.4f} |",
        f"| MCC | {mean_metrics['mcc']:.4f} | {std_metrics['mcc']:.4f} |",
        "",
        "## Rincian Per Folds",
        "",
        "| Fold | Accuracy | AUROC | AUC-PR | Sensitivity | Specificity | MCC |",
        "|---|---|---|---|---|---|---|",
    ]
    for idx, fold_m in enumerate(folds_metrics, 1):
        md_lines.append(
            f"| {idx} | {fold_m['accuracy']:.4f} | {fold_m['auroc']:.4f} | {fold_m['auc_pr']:.4f} | {fold_m['sensitivity']:.4f} | {fold_m['specificity']:.4f} | {fold_m['mcc']:.4f} |"
        )
        
    write_report("06a_gnn.md", md_lines)
    logger.info("Laporan markdown disimpan ke %s", REPORTS / "06a_gnn.md")


if __name__ == "__main__":
    main()
