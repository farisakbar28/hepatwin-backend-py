"""TU.8/TU.9 -- Training loop GATNN-DNN + evaluasi L1/L2 x 5 seed.

Hyperparameter mengikuti UPSCALE.md SS5.5 persis: AdamW lr=1e-3 wd=1e-4,
batch_size=32, max_epochs=300, early_stopping patience=30 monitor=val_auc
mode=max, ReduceLROnPlateau(factor=0.5, patience=10), BCEWithLogitsLoss
dengan pos_weight dari train fold, seed=[42,43,44,45,46].
"""
import argparse
import copy
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from rdkit import Chem
from sklearn.metrics import roc_auc_score
from torch_geometric.data import Batch, Data
from torch_geometric.loader import DataLoader

from hepatwin_ml.data.splits import random_kfold, scaffold_kfold
from hepatwin_ml.evaluate import compute_metrics, summarize_across_seeds
from hepatwin_ml.features.fingerprints import dnn_feature_vector
from hepatwin_ml.features.graph import smiles_to_graph
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SEEDS = [42, 43, 44, 45, 46]
MAX_EPOCHS = 300
PATIENCE = 30
BATCH_SIZE = 32
LR = 1e-3
WEIGHT_DECAY = 1e-4


def build_graph_dataset(df: pd.DataFrame) -> list[Data]:
    graphs = []
    for _, row in df.iterrows():
        g = smiles_to_graph(row["canonical_smiles"])
        mol = Chem.MolFromSmiles(row["canonical_smiles"])
        g.fingerprint = torch.tensor(dnn_feature_vector(mol), dtype=torch.float).unsqueeze(0)
        g.y = torch.tensor([float(row["label_binary"])], dtype=torch.float)
        graphs.append(g)
    return graphs


def train_gatnn(
    train_graphs: list[Data],
    val_graphs: list[Data],
    seed: int,
    max_epochs: int = MAX_EPOCHS,
    patience: int = PATIENCE,
    verbose: bool = False,
    lr: float = LR,
    hidden: int = 64,
    dropout: float = 0.3,
) -> tuple[GatnnDnn, np.ndarray, np.ndarray]:
    """lr/hidden/dropout: dipakai nested_cv.py (TU.20) untuk hyperparameter
    search -- sebelumnya diam-diam DIABAIKAN di sini (bug ditemukan & diperbaiki
    saat audit TU.22, lihat 20_nested_cv_scores.md untuk detail)."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    model = GatnnDnn(hidden=hidden, dropout=dropout)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=10)

    train_labels = np.array([g.y.item() for g in train_graphs])
    n_pos = max(int(train_labels.sum()), 1)
    n_neg = max(len(train_labels) - n_pos, 1)
    pos_weight = torch.tensor([n_neg / n_pos], dtype=torch.float)
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    train_loader = DataLoader(train_graphs, batch_size=BATCH_SIZE, shuffle=True)
    val_batch = Batch.from_data_list(val_graphs)
    val_y = np.array([g.y.item() for g in val_graphs])

    best_val_auc = -np.inf
    best_state = None
    epochs_no_improve = 0
    best_val_probs = None

    for epoch in range(max_epochs):
        model.train()
        for batch in train_loader:
            optimizer.zero_grad()
            logits = model(batch)
            loss = loss_fn(logits, batch.y)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(val_batch)
            val_probs = torch.sigmoid(val_logits).numpy()
        val_auc = roc_auc_score(val_y, val_probs) if len(set(val_y)) > 1 else 0.5
        scheduler.step(val_auc)

        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_state = copy.deepcopy(model.state_dict())
            best_val_probs = val_probs
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if verbose and epoch % 20 == 0:
            logger.info("epoch %d loss=%.4f val_auc=%.4f best=%.4f", epoch, loss.item(), val_auc, best_val_auc)

        if epochs_no_improve >= patience:
            if verbose:
                logger.info("Early stopping di epoch %d (best_val_auc=%.4f)", epoch, best_val_auc)
            break

    model.load_state_dict(best_state)
    return model, val_y, best_val_probs


def run_arm(
    parquet_path: str,
    split_type: str,
    out_json: str,
    out_md: str,
    seeds: list[int] = SEEDS,
    k: int = 5,
    max_epochs: int = MAX_EPOCHS,
) -> dict:
    df = pd.read_parquet(parquet_path)
    logger.info("Dataset: %d senyawa dari %s, split=%s", len(df), parquet_path, split_type)

    split_fn = random_kfold if split_type == "random" else scaffold_kfold

    out_json_path = Path(out_json)
    all_metrics: list[dict] = []
    done: set[tuple[int, int]] = set()
    if out_json_path.exists():
        prior = json.loads(out_json_path.read_text(encoding="utf-8"))
        all_metrics = prior.get("per_run", [])
        done = {(m["seed"], m["fold"]) for m in all_metrics}
        logger.info("Resume: %d run sudah ada di %s, dilewati", len(done), out_json)

    def _write_partial() -> None:
        summary = summarize_across_seeds(all_metrics) if all_metrics else {}
        result = {"split_type": split_type, "n_total": len(df), "per_run": all_metrics, "summary": summary}
        out_json_path.parent.mkdir(parents=True, exist_ok=True)
        out_json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    t0 = time.time()
    for seed in seeds:
        for fold_i, (train_idx, val_idx) in enumerate(split_fn(df, k=k, seed=seed)):
            if (seed, fold_i) in done:
                continue
            train_df = df.iloc[train_idx].reset_index(drop=True)
            val_df = df.iloc[val_idx].reset_index(drop=True)
            train_graphs = build_graph_dataset(train_df)
            val_graphs = build_graph_dataset(val_df)

            _, val_y, val_probs = train_gatnn(train_graphs, val_graphs, seed=seed, max_epochs=max_epochs)
            metrics = compute_metrics(val_y, val_probs)
            metrics["seed"] = seed
            metrics["fold"] = fold_i
            all_metrics.append(metrics)
            _write_partial()  # tulis progres tiap fold -- jangan hilang bila proses terputus
            logger.info(
                "seed=%d fold=%d auc=%.4f mcc=%.4f (n_train=%d n_val=%d) [%.1fs elapsed]",
                seed, fold_i, metrics["auc_roc"], metrics["mcc"], len(train_idx), len(val_idx), time.time() - t0,
            )

    summary = summarize_across_seeds(all_metrics)

    lines = [
        f"# Evaluasi GATNN-DNN -- split={split_type}",
        "",
        f"Dataset: `{parquet_path}` ({len(df)} senyawa), {len(seeds)} seed x {k} fold = {len(all_metrics)} run",
        "",
        "| Metrik | Mean | Std |",
        "|---|---|---|",
    ]
    for key, (mean, std) in summary.items():
        if key in ("seed", "fold"):
            continue
        lines.append(f"| {key} | {mean:.4f} | {std:.4f} |")
    Path(out_md).write_text("\n".join(lines), encoding="utf-8")
    logger.info("Selesai split=%s dalam %.1f menit -> %s", split_type, (time.time() - t0) / 60, out_json)
    return {"split_type": split_type, "n_total": len(df), "per_run": all_metrics, "summary": summary}


def main() -> None:
    ap = argparse.ArgumentParser(description="Training + evaluasi GATNN-DNN")
    ap.add_argument("--parquet", default="ml/data/processed/arm_a.parquet")
    ap.add_argument("--split", choices=["random", "scaffold"], required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--max-epochs", type=int, default=MAX_EPOCHS)
    args = ap.parse_args()
    run_arm(args.parquet, args.split, args.out_json, args.out_md, args.seeds, args.k, args.max_epochs)


if __name__ == "__main__":
    main()
