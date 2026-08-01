"""Perbaikan TU.20: ulang HANYA bagian GATNN-DNN nested CV (baseline sudah
benar, tidak diulang) setelah bug ditemukan -- hyperparameter lr/hidden/dropout
yang di-sample tidak pernah benar-benar dipakai train_gatnn()/GatnnDnn()
sebelumnya (lihat commit fix). Overwrite key 'gatnn_dnn' per fold di JSON yang
sudah ada, baseline lain (random_forest/lightgbm/xgboost/logistic_regression)
dipertahankan apa adanya.
"""
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from hepatwin_ml.evaluate import compute_metrics
from hepatwin_ml.nested_cv import GATNN_SEARCH_SPACE, N_TRIALS, SEED, _make_inner_folds, _sample_trials
from hepatwin_ml.train import build_graph_dataset, train_gatnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def refix_fold(df: pd.DataFrame, train_idx: np.ndarray, test_idx: np.ndarray, fold_i: int, seed: int = SEED) -> dict:
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)
    inner_folds = _make_inner_folds(train_df, seed=seed)

    gatnn_trials = _sample_trials(GATNN_SEARCH_SPACE, N_TRIALS, seed=seed + fold_i)
    best_score, best_params = -np.inf, gatnn_trials[0]
    for params in gatnn_trials:
        aucs = []
        for tr_idx, val_idx in inner_folds:
            tr_graphs = build_graph_dataset(train_df.iloc[tr_idx].reset_index(drop=True))
            val_graphs = build_graph_dataset(train_df.iloc[val_idx].reset_index(drop=True))
            _, val_y, val_probs = train_gatnn(
                tr_graphs, val_graphs, seed=seed, max_epochs=150, patience=20,
                lr=params["lr"], hidden=params["hidden"], dropout=params["dropout"],
            )
            aucs.append(roc_auc_score(val_y, val_probs) if len(set(val_y)) > 1 else 0.5)
        score = float(np.mean(aucs))
        if score > best_score:
            best_score, best_params = score, params

    train_graphs_full = build_graph_dataset(train_df)
    test_graphs = build_graph_dataset(test_df)
    _, test_y_gatnn, test_probs_gatnn = train_gatnn(
        train_graphs_full, test_graphs, seed=seed, max_epochs=300, patience=30,
        lr=best_params["lr"], hidden=best_params["hidden"], dropout=best_params["dropout"],
    )
    gatnn_metrics = compute_metrics(test_y_gatnn, test_probs_gatnn)
    return {
        "best_params": best_params, "inner_cv_auc": best_score,
        "test_probs": test_probs_gatnn.tolist(), "y_test": test_y_gatnn.tolist(), **gatnn_metrics,
    }


def main() -> None:
    df = pd.read_parquet("ml/data/processed/arm_a_devpool.parquet")
    fold_data = json.loads(Path("ml/data/interim/outer_fold_indices.json").read_text(encoding="utf-8"))
    scores_path = Path("ml/reports/20_nested_cv_scores.json")
    scores = json.loads(scores_path.read_text(encoding="utf-8"))

    t0 = time.time()
    for fold_i, fold in enumerate(fold_data["folds"]):
        if "_gatnn_refixed" in scores[fold_i]:
            logger.info("Fold %d sudah diperbaiki, skip", fold_i)
            continue
        train_idx, test_idx = np.array(fold["train_idx"]), np.array(fold["test_idx"])
        old_auc = scores[fold_i]["gatnn_dnn"]["auc_roc"]
        new_gatnn = refix_fold(df, train_idx, test_idx, fold_i, seed=SEED)
        scores[fold_i]["gatnn_dnn"] = new_gatnn
        scores[fold_i]["_gatnn_refixed"] = True
        scores_path.write_text(json.dumps(scores, indent=2), encoding="utf-8")
        logger.info(
            "Fold %d diperbaiki [%.1f menit total]: AUC lama(bug)=%.4f -> AUC baru(benar)=%.4f, best_params=%s",
            fold_i, (time.time() - t0) / 60, old_auc, new_gatnn["auc_roc"], new_gatnn["best_params"],
        )

    logger.info("Selesai perbaikan GATNN-DNN nested CV dalam %.1f menit", (time.time() - t0) / 60)


if __name__ == "__main__":
    main()
