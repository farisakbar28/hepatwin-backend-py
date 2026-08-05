"""TU.22 -- Evaluasi akhir hold-out (SEKALI JALAN).

Dasar: UPSCALE.md SS13.5, SS13.6.

Urutan wajib:
1. Verifikasi TU.21 lolos (Y-randomization wajar, tidak ada leakage)
2. Tentukan hyperparameter final per model: MODUS (kombinasi paling sering
   menang) dari 10 fold outer TU.20, tie-break dgn rata-rata inner_cv_auc
   tertinggi di antara kandidat seri
3. Latih ulang KELIMA model pada SELURUH dev_pool (672 senyawa) pakai
   hyperparameter final
4. Evaluasi SATU KALI pada holdout_set (167 senyawa) -- TIDAK PERNAH disentuh
   sebelum baris kode ini
5. DeLong test + bootstrap CI pada holdout_set
6. Setelah ini, holdout_set TIDAK BOLEH dipakai lagi
"""
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score
from torch_geometric.data import Batch

from hepatwin_ml.evaluate import compute_metrics
from hepatwin_ml.models.baselines import (
    compute_scale_pos_weight,
    ecfp4_features,
    make_lightgbm,
    make_logistic_regression,
    make_random_forest,
    make_xgboost,
)
from hepatwin_ml.significance import bootstrap_auc_ci, delong_test
from hepatwin_ml.train import build_graph_dataset, train_gatnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODELS = ["gatnn_dnn", "random_forest", "lightgbm", "xgboost", "logistic_regression"]
SEED = 42


def _verify_tu21_passed() -> None:
    result = json.loads(Path("ml/reports/21_significance_devpool.json").read_text(encoding="utf-8"))
    auc_mean = result["y_randomization"]["auc_mean"]
    if abs(auc_mean - 0.5) / 0.08 > 2:  # ambang kasar konsisten dgn run_significance_devpool.py
        raise SystemExit(
            f"BLOCKED: Y-randomization TU.21 menunjukkan indikasi leakage (AUC={auc_mean:.4f}). "
            "TU.22 tidak boleh lanjut sebelum diaudit (UPSCALE.md SS13.4/SS13.7)."
        )
    logger.info("TU.21 terverifikasi lolos (Y-randomization AUC=%.4f, wajar). Lanjut TU.22.", auc_mean)


def select_final_params(scores: list[dict], model_name: str, exclude_keys: tuple = ()) -> dict:
    """Modus kombinasi hyperparameter dari 10 fold, tie-break rata-rata inner_cv_auc tertinggi."""
    param_counts: Counter = Counter()
    param_aucs: dict = defaultdict(list)
    for fold in scores:
        p = {k: v for k, v in fold[model_name]["best_params"].items() if k not in exclude_keys}
        key = json.dumps(p, sort_keys=True)
        param_counts[key] += 1
        param_aucs[key].append(fold[model_name]["inner_cv_auc"])
    max_count = max(param_counts.values())
    candidates = [k for k, c in param_counts.items() if c == max_count]
    best_key = max(candidates, key=lambda k: sum(param_aucs[k]) / len(param_aucs[k]))
    return json.loads(best_key)


def main() -> None:
    _verify_tu21_passed()

    scores = json.loads(Path("ml/reports/20_nested_cv_scores.json").read_text(encoding="utf-8"))
    final_params = {
        "gatnn_dnn": select_final_params(scores, "gatnn_dnn"),
        "random_forest": select_final_params(scores, "random_forest"),
        "lightgbm": select_final_params(scores, "lightgbm", exclude_keys=("scale_pos_weight",)),
        "xgboost": select_final_params(scores, "xgboost", exclude_keys=("scale_pos_weight",)),
        "logistic_regression": select_final_params(scores, "logistic_regression"),
    }
    logger.info("Hyperparameter final terpilih (modus dari 10 fold TU.20):")
    for m, p in final_params.items():
        logger.info("  %s: %s", m, p)

    dev_pool = pd.read_parquet("ml/data/processed/arm_a_devpool.parquet")
    holdout = pd.read_parquet("ml/data/processed/arm_a_holdout.parquet")
    logger.info("dev_pool=%d, holdout_set=%d -- holdout SEKARANG DIBUKA untuk evaluasi SATU KALI", len(dev_pool), len(holdout))

    X_dev_ecfp4 = ecfp4_features(dev_pool["canonical_smiles"].tolist())
    y_dev = dev_pool["label_binary"].to_numpy()
    X_holdout_ecfp4 = ecfp4_features(holdout["canonical_smiles"].tolist())
    y_holdout = holdout["label_binary"].to_numpy()
    spw_full = compute_scale_pos_weight(y_dev)

    results = {}

    baseline_specs = [
        ("random_forest", make_random_forest, {}),
        ("lightgbm", make_lightgbm, {"scale_pos_weight": spw_full}),
        ("xgboost", make_xgboost, {"scale_pos_weight": spw_full}),
        ("logistic_regression", make_logistic_regression, {}),
    ]
    for name, make_fn, fixed_kwargs in baseline_specs:
        params = {**final_params[name], **fixed_kwargs}
        model = make_fn(seed=SEED, **params)
        model.fit(X_dev_ecfp4, y_dev)
        probs = model.predict_proba(X_holdout_ecfp4)[:, 1]
        metrics = compute_metrics(y_holdout, probs)
        results[name] = {"final_params": final_params[name], "holdout_probs": probs.tolist(), **metrics}
        logger.info("%s pada holdout: AUC=%.4f", name, metrics["auc_roc"])

    gp = final_params["gatnn_dnn"]
    dev_graphs = build_graph_dataset(dev_pool)
    holdout_graphs = build_graph_dataset(holdout)
    _, y_holdout_gatnn, gatnn_probs = train_gatnn(
        dev_graphs, holdout_graphs, seed=SEED, max_epochs=300, patience=30,
        lr=gp["lr"], hidden=gp["hidden"], dropout=gp["dropout"],
    )
    gatnn_metrics = compute_metrics(y_holdout_gatnn, gatnn_probs)
    results["gatnn_dnn"] = {"final_params": gp, "holdout_probs": gatnn_probs.tolist(), **gatnn_metrics}
    logger.info("gatnn_dnn pada holdout: AUC=%.4f", gatnn_metrics["auc_roc"])

    logger.info("=== holdout_set SUDAH DIPAKAI. Tidak boleh dipakai lagi setelah ini. ===")

    delong_results = {}
    bootstrap_results = {}
    gatnn_probs_arr = np.array(results["gatnn_dnn"]["holdout_probs"])
    for name in MODELS:
        bootstrap_results[name] = bootstrap_auc_ci(y_holdout, np.array(results[name]["holdout_probs"]), n_resample=1000, seed=SEED)
        if name != "gatnn_dnn":
            delong_results[name] = delong_test(y_holdout, gatnn_probs_arr, np.array(results[name]["holdout_probs"]))
            logger.info("DeLong GATNN vs %s: diff=%.4f p=%.4f", name, delong_results[name]["diff"], delong_results[name]["p_value"])

    output = {
        "final_params": final_params,
        "holdout_metrics": {m: {k: v for k, v in results[m].items() if k != "holdout_probs"} for m in MODELS},
        "delong_vs_gatnn": delong_results,
        "bootstrap_ci": bootstrap_results,
        "n_dev_pool": len(dev_pool),
        "n_holdout": len(holdout),
    }
    Path("ml/reports/22_final_holdout_eval.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    logger.info("Selesai TU.22. Hasil -> ml/reports/22_final_holdout_eval.json")


if __name__ == "__main__":
    main()
