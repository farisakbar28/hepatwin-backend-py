"""TU.16 -- Ablasi Tox21 auxiliary head: AUC DILI dengan vs tanpa, Arm A.

5-fold CV (seed=42 saja -- eksperimen tambahan terpisah dari tabel utama
TU.9/TU.13, bukan pengganti evaluasi 5-seed resminya, UPSCALE.md TU.16).
"""
import json
import logging
from pathlib import Path

import pandas as pd
import torch
from torch_geometric.data import Batch

from hepatwin_ml.data.splits import random_kfold
from hepatwin_ml.evaluate import compute_metrics, summarize_across_seeds
from hepatwin_ml.stretch.tox21_multitask import load_tox21_graphs, train_gatnn_with_tox21_auxiliary
from hepatwin_ml.train import build_graph_dataset, train_gatnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SEED = 42
K = 5


def main() -> None:
    df = pd.read_parquet("ml/data/processed/arm_a.parquet")
    tox21_graphs = load_tox21_graphs("ml/data/raw/tox21.csv")

    without_aux = []
    with_aux = []

    for fold_i, (train_idx, val_idx) in enumerate(random_kfold(df, k=K, seed=SEED)):
        train_df = df.iloc[train_idx].reset_index(drop=True)
        val_df = df.iloc[val_idx].reset_index(drop=True)
        train_graphs = build_graph_dataset(train_df)
        val_graphs = build_graph_dataset(val_df)

        logger.info("Fold %d -- tanpa auxiliary head", fold_i)
        _, val_y, val_probs = train_gatnn(train_graphs, val_graphs, seed=SEED)
        m = compute_metrics(val_y, val_probs)
        m["fold"] = fold_i
        without_aux.append(m)
        logger.info("Fold %d tanpa aux: AUC=%.4f", fold_i, m["auc_roc"])

        logger.info("Fold %d -- dengan Tox21 auxiliary head", fold_i)
        _, val_y2, val_probs2 = train_gatnn_with_tox21_auxiliary(
            train_graphs, val_graphs, tox21_graphs, seed=SEED, lambda_tox21=0.1
        )
        m2 = compute_metrics(val_y2, val_probs2)
        m2["fold"] = fold_i
        with_aux.append(m2)
        logger.info("Fold %d dengan aux: AUC=%.4f", fold_i, m2["auc_roc"])

    summary_without = summarize_across_seeds(without_aux)
    summary_with = summarize_across_seeds(with_aux)

    result = {
        "seed": SEED,
        "k": K,
        "without_tox21_aux": {"per_fold": without_aux, "summary": summary_without},
        "with_tox21_aux": {"per_fold": with_aux, "summary": summary_with},
    }
    Path("ml/reports/08_tox21_ablation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "# 08 -- Ablasi Tox21 Multi-Task Auxiliary Head (TU.16, stretch)",
        "",
        f"Arm A (839 senyawa), 5-fold CV random split, seed={SEED} saja "
        "(eksperimen tambahan, TIDAK menggantikan tabel utama Arm A/B TU.9/TU.13).",
        "",
        "| Kondisi | AUC-ROC (mean+-std) | MCC (mean+-std) |",
        "|---|---|---|",
        f"| Tanpa auxiliary head | {summary_without['auc_roc'][0]:.4f} +/- {summary_without['auc_roc'][1]:.4f} | "
        f"{summary_without['mcc'][0]:.4f} +/- {summary_without['mcc'][1]:.4f} |",
        f"| Dengan Tox21 auxiliary head (lambda=0.1) | {summary_with['auc_roc'][0]:.4f} +/- {summary_with['auc_roc'][1]:.4f} | "
        f"{summary_with['mcc'][0]:.4f} +/- {summary_with['mcc'][1]:.4f} |",
        "",
        "**Label jelas:** ini eksperimen tambahan terpisah (TU.16, stretch, opsional -- "
        "UPSCALE.md SS3.4), TIDAK menggantikan atau mengubah kesimpulan Arm A vs Arm B "
        "di `07_comparison.md`.",
    ]
    Path("ml/reports/08_tox21_ablation.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info(
        "Selesai. Tanpa aux AUC=%.4f, Dengan aux AUC=%.4f",
        summary_without["auc_roc"][0], summary_with["auc_roc"][0],
    )


if __name__ == "__main__":
    main()
