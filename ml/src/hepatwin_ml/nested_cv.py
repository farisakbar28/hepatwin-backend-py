"""TU.20 -- Nested cross-validation: hyperparameter tuning adil untuk GATNN-DNN
+ 4 baseline (RF, LightGBM, XGBoost, LogReg), budget identik.

Dasar: UPSCALE.md SS13.3. dev_pool SAJA (holdout_set tidak boleh disentuh).

Outer: 10-fold scaffold CV. Inner: 3-fold CV, budget 10 trial random search,
SAMA untuk semua model. Fold outer disimpan ke file supaya TU.21 (uji
berpasangan) valid secara statistik.
"""
import itertools
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from hepatwin_ml.data.splits import scaffold_kfold
from hepatwin_ml.evaluate import compute_metrics
from hepatwin_ml.models.baselines import (
    compute_scale_pos_weight,
    ecfp4_features,
    make_lightgbm,
    make_logistic_regression,
    make_random_forest,
    make_xgboost,
)
from hepatwin_ml.train import build_graph_dataset, train_gatnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

N_OUTER = 10
N_INNER = 3
N_TRIALS = 10
SEED = 42

# Ruang pencarian persis UPSCALE.md SS13.3
GATNN_SEARCH_SPACE = {"lr": [1e-3, 5e-4], "hidden": [64, 128], "dropout": [0.2, 0.3, 0.4]}
RF_SEARCH_SPACE = {"n_estimators": [300, 500, 800], "max_depth": [None, 10, 20]}
LGBM_SEARCH_SPACE = {"num_leaves": [15, 31, 63], "learning_rate": [0.01, 0.05, 0.1]}
XGB_SEARCH_SPACE = {"max_depth": [3, 5, 7], "learning_rate": [0.01, 0.05, 0.1]}
LOGREG_SEARCH_SPACE = {"C": [0.01, 0.1, 1, 10], "penalty": ["l1", "l2"]}


def _sample_trials(search_space: dict, n_trials: int, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    keys = list(search_space.keys())
    all_combos = list(itertools.product(*[search_space[k] for k in keys]))
    n_trials = min(n_trials, len(all_combos))
    chosen_idx = rng.choice(len(all_combos), size=n_trials, replace=False)
    return [dict(zip(keys, all_combos[i])) for i in chosen_idx]


def _make_inner_folds(df_subset: pd.DataFrame, seed: int) -> list:
    return list(scaffold_kfold(df_subset.reset_index(drop=True), k=N_INNER, seed=seed))


def tune_and_eval_outer_fold(
    df: pd.DataFrame, train_idx: np.ndarray, test_idx: np.ndarray, fold_i: int, seed: int = SEED
) -> dict:
    """Satu fold outer: tuning (inner 3-fold, budget 10 trial) utk kelima
    model, lalu evaluasi pada fold outer test yang belum pernah dilihat."""
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)
    inner_folds = _make_inner_folds(train_df, seed=seed)

    X_train_ecfp4 = ecfp4_features(train_df["canonical_smiles"].tolist())
    y_train = train_df["label_binary"].to_numpy()
    X_test_ecfp4 = ecfp4_features(test_df["canonical_smiles"].tolist())
    y_test = test_df["label_binary"].to_numpy()
    spw = compute_scale_pos_weight(y_train)

    results = {}

    # --- baseline sklearn-compatible ---
    baseline_specs = [
        ("random_forest", make_random_forest, RF_SEARCH_SPACE, {}),
        ("lightgbm", make_lightgbm, LGBM_SEARCH_SPACE, {"scale_pos_weight": spw}),
        ("xgboost", make_xgboost, XGB_SEARCH_SPACE, {"scale_pos_weight": spw}),
        ("logistic_regression", make_logistic_regression, LOGREG_SEARCH_SPACE, {}),
    ]
    for name, make_fn, space, fixed_kwargs in baseline_specs:
        trials = _sample_trials(space, N_TRIALS, seed=seed + fold_i)
        best_score, best_params = -np.inf, trials[0]
        for params in trials:
            full_params = {**params, **fixed_kwargs}
            aucs = []
            for tr_idx, val_idx in inner_folds:
                model = make_fn(seed=seed, **full_params)
                model.fit(X_train_ecfp4[tr_idx], y_train[tr_idx])
                probs = model.predict_proba(X_train_ecfp4[val_idx])[:, 1]
                aucs.append(roc_auc_score(y_train[val_idx], probs) if len(set(y_train[val_idx])) > 1 else 0.5)
            score = float(np.mean(aucs))
            if score > best_score:
                best_score, best_params = score, full_params

        final_model = make_fn(seed=seed, **best_params)
        final_model.fit(X_train_ecfp4, y_train)
        test_probs = final_model.predict_proba(X_test_ecfp4)[:, 1]
        metrics = compute_metrics(y_test, test_probs)
        results[name] = {"best_params": best_params, "inner_cv_auc": best_score, "test_probs": test_probs.tolist(), "y_test": y_test.tolist(), **metrics}

    # --- GATNN-DNN ---
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
    results["gatnn_dnn"] = {
        "best_params": best_params, "inner_cv_auc": best_score,
        "test_probs": test_probs_gatnn.tolist(), "y_test": test_y_gatnn.tolist(), **gatnn_metrics,
    }

    return results


def main(n_outer: int = N_OUTER, out_json: str = "ml/reports/20_nested_cv_scores.json") -> None:
    df = pd.read_parquet("ml/data/processed/arm_a_devpool.parquet")
    logger.info("dev_pool: %d senyawa, outer=%d fold, inner=%d fold, budget=%d trial", len(df), n_outer, N_INNER, N_TRIALS)

    outer_folds = list(scaffold_kfold(df, k=n_outer, seed=SEED))
    fold_indices_serializable = [
        {"train_idx": tr.tolist(), "test_idx": te.tolist()} for tr, te in outer_folds
    ]
    Path("ml/data/interim/outer_fold_indices.json").parent.mkdir(parents=True, exist_ok=True)
    Path("ml/data/interim/outer_fold_indices.json").write_text(
        json.dumps({"seed": SEED, "k": n_outer, "folds": fold_indices_serializable}, indent=2), encoding="utf-8"
    )

    all_results = []
    t0 = time.time()
    out_path = Path(out_json)
    if out_path.exists():
        all_results = json.loads(out_path.read_text(encoding="utf-8"))
        logger.info("Resume: %d fold outer sudah ada", len(all_results))

    for fold_i, (train_idx, test_idx) in enumerate(outer_folds):
        if fold_i < len(all_results):
            continue
        logger.info("=== Outer fold %d/%d ===", fold_i, n_outer)
        fold_result = tune_and_eval_outer_fold(df, train_idx, test_idx, fold_i, seed=SEED)
        fold_result["fold"] = fold_i
        all_results.append(fold_result)
        out_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
        logger.info(
            "Fold %d selesai [%.1f menit total]. AUC: RF=%.3f LGBM=%.3f XGB=%.3f LogReg=%.3f GATNN=%.3f",
            fold_i, (time.time() - t0) / 60,
            all_results[-1]["random_forest"]["auc_roc"], all_results[-1]["lightgbm"]["auc_roc"],
            all_results[-1]["xgboost"]["auc_roc"], all_results[-1]["logistic_regression"]["auc_roc"],
            all_results[-1]["gatnn_dnn"]["auc_roc"],
        )

    logger.info("Nested CV selesai dalam %.1f menit", (time.time() - t0) / 60)


if __name__ == "__main__":
    main()
