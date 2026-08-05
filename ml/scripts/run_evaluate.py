"""C7 -- Evaluasi metrik GATNN-DNN + baseline pembanding + kalibrasi.

🚩 Test set (hold-out, C5) dibuka SATU KALI di sini. Setelah skrip ini
dijalankan, ml/data/processed/test.parquet TIDAK BOLEH dipakai lagi untuk
tuning apa pun.

Baseline hyperparameter final (PROJECT_FIX_MODEL.md SS3, dari nested CV
upscale, TIDAK dicari ulang): RF(n_estimators=500,max_depth=None),
LightGBM(num_leaves=15,learning_rate=0.1), XGBoost(max_depth=5,learning_rate=0.1),
LogReg(C=0.1,penalty=l2). scale_pos_weight/class_weight dihitung dari TRAIN
fold saja (bukan test) -- mencegah kebocoran.

Kalibrasi: dilatih pada VAL set (116 sampel, <200 -> Platt scaling otomatis
sesuai ambang calibrate.py), diterapkan ke TEST set. Brier & ECE dilaporkan
sebelum vs sesudah kalibrasi.
"""
from __future__ import annotations

import pickle
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "ml" / "src"))

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve
from torch_geometric.data import Batch

from hepatwin_ml.calibrate import fit_calibrator
from hepatwin_ml.evaluate import compute_metrics
from hepatwin_ml.models.baselines import (
    compute_scale_pos_weight,
    ecfp4_features,
    make_lightgbm,
    make_logistic_regression,
    make_random_forest,
    make_xgboost,
)
from hepatwin_ml.models.gatnn_dnn import GatnnDnn
from hepatwin_ml.train import build_graph_dataset

TRAIN_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "train.parquet"
VAL_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "val.parquet"
TEST_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "test.parquet"
MODEL_PATH = _REPO_ROOT / "ml" / "models" / "model_gatnn_dnn.pt"
METADATA_PATH = _REPO_ROOT / "ml" / "models" / "model_gatnn_dnn_metadata.json"
CALIBRATOR_OUT = _REPO_ROOT / "ml" / "models" / "calibrator_gatnn_dnn.pkl"
PLOTS_DIR = _REPO_ROOT / "ml" / "reports" / "C7_plots"
REPORT_OUT = _REPO_ROOT / "ml" / "reports" / "C7_evaluasi.md"
RESULTS_JSON_OUT = _REPO_ROOT / "ml" / "reports" / "C7_evaluasi.json"

SEED = 42
AUC_SUSPICIOUS_THRESHOLD = 0.90


@torch.no_grad()
def gatnn_predict_proba(model: GatnnDnn, graphs: list) -> np.ndarray:
    model.eval()
    batch = Batch.from_data_list(graphs)
    logits = model(batch)
    return torch.sigmoid(logits).numpy()


def main() -> None:
    train_df = pd.read_parquet(TRAIN_PATH)
    val_df = pd.read_parquet(VAL_PATH)
    test_df = pd.read_parquet(TEST_PATH)
    print(f"train={len(train_df)}, val={len(val_df)}, test(hold-out, DIBUKA SEKALI)={len(test_df)}")

    y_train = train_df["label_binary"].to_numpy()
    y_val = val_df["label_binary"].to_numpy()
    y_test = test_df["label_binary"].to_numpy()

    # --- Baseline: ECFP4 features, fit pada train, evaluasi pada test ---
    X_train = ecfp4_features(train_df["canonical_smiles"].tolist())
    X_test = ecfp4_features(test_df["canonical_smiles"].tolist())
    spw = compute_scale_pos_weight(y_train)  # dari TRAIN fold saja

    baseline_specs = [
        ("random_forest", make_random_forest, {"n_estimators": 500, "max_depth": None}),
        ("lightgbm", make_lightgbm, {"num_leaves": 15, "learning_rate": 0.1, "scale_pos_weight": spw}),
        ("xgboost", make_xgboost, {"max_depth": 5, "learning_rate": 0.1, "scale_pos_weight": spw}),
        ("logistic_regression", make_logistic_regression, {"C": 0.1, "penalty": "l2"}),
    ]

    results: dict[str, dict] = {}
    probs_by_model: dict[str, np.ndarray] = {}

    for name, make_fn, params in baseline_specs:
        model = make_fn(seed=SEED, **params)
        model.fit(X_train, y_train)
        probs = model.predict_proba(X_test)[:, 1]
        metrics = compute_metrics(y_test, probs)
        results[name] = {"params": params, **metrics}
        probs_by_model[name] = probs
        print(f"{name}: AUC={metrics['auc_roc']:.4f} MCC={metrics['mcc']:.4f}")

    # --- GATNN-DNN: pakai model TERLATIH dari C6 (bukan dilatih ulang) ---
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    hp = metadata["hyperparameters"]
    model = GatnnDnn(hidden=hp["hidden"], dropout=hp["dropout"])
    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    model.eval()

    val_graphs = build_graph_dataset(val_df)
    test_graphs = build_graph_dataset(test_df)

    val_probs_raw = gatnn_predict_proba(model, val_graphs)
    test_probs_raw = gatnn_predict_proba(model, test_graphs)

    metrics_raw = compute_metrics(y_test, test_probs_raw)
    print(f"gatnn_dnn (sebelum kalibrasi): AUC={metrics_raw['auc_roc']:.4f} Brier={metrics_raw['brier']:.4f} ECE={metrics_raw['ece']:.4f}")

    # --- Kalibrasi: fit pada VAL (bukan test/train), terapkan ke TEST ---
    calibrator = fit_calibrator(val_probs_raw, y_val)
    test_probs_calibrated = calibrator.predict(test_probs_raw)
    metrics_calibrated = compute_metrics(y_test, test_probs_calibrated)
    print(f"gatnn_dnn (sesudah kalibrasi, method={calibrator.method}): AUC={metrics_calibrated['auc_roc']:.4f} Brier={metrics_calibrated['brier']:.4f} ECE={metrics_calibrated['ece']:.4f}")

    results["gatnn_dnn"] = {"params": hp, **metrics_calibrated}
    probs_by_model["gatnn_dnn"] = test_probs_calibrated

    CALIBRATOR_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CALIBRATOR_OUT, "wb") as f:
        pickle.dump(calibrator, f)

    # --- 🚩 Sanity check kebocoran data ---
    suspicious = {m: r["auc_roc"] for m, r in results.items() if r["auc_roc"] > AUC_SUSPICIOUS_THRESHOLD}
    if suspicious:
        raise SystemExit(
            f"🚩 AUC > {AUC_SUSPICIOUS_THRESHOLD} terdeteksi untuk {suspicious} -- "
            "tidak wajar untuk prediksi DILI pada dataset seukuran ini. "
            "AUDIT kebocoran data SEBELUM melaporkan apa pun (EXECUTION_PLAN_FIX_MODEL.md C7)."
        )

    # --- Confusion matrix (GATNN-DNN, threshold 0.5, probs terkalibrasi) ---
    y_pred = (test_probs_calibrated >= 0.5).astype(int)
    cm = confusion_matrix(y_test, y_pred)

    # --- Plots ---
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 6))
    for name, probs in probs_by_model.items():
        fpr, tpr, _ = roc_curve(y_test, probs)
        plt.plot(fpr, tpr, label=f"{name} (AUC={results[name]['auc_roc']:.3f})")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.3)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC -- test set hold-out (n=%d)" % len(test_df))
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "roc_curve.png", dpi=120)
    plt.close()

    plt.figure(figsize=(6, 6))
    for name, probs in probs_by_model.items():
        prec, rec, _ = precision_recall_curve(y_test, probs)
        plt.plot(rec, prec, label=f"{name} (AUC-PR={results[name]['auc_pr']:.3f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall -- test set hold-out (n=%d)" % len(test_df))
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "pr_curve.png", dpi=120)
    plt.close()

    plt.figure(figsize=(5, 5))
    plt.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=14)
    plt.xticks([0, 1], ["Pred 0", "Pred 1"])
    plt.yticks([0, 1], ["True 0", "True 1"])
    plt.title("Confusion matrix -- GATNN-DNN (test, threshold=0.5)")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "confusion_matrix.png", dpi=120)
    plt.close()

    def _reliability_bins(y_true, y_prob, n_bins=10):
        edges = np.linspace(0, 1, n_bins + 1)
        centers, accs = [], []
        for lo, hi in zip(edges[:-1], edges[1:]):
            mask = (y_prob >= lo) & (y_prob <= hi) if lo == 0 else (y_prob > lo) & (y_prob <= hi)
            if mask.sum() == 0:
                continue
            centers.append(y_prob[mask].mean())
            accs.append(y_true[mask].mean())
        return centers, accs

    plt.figure(figsize=(6, 6))
    plt.plot([0, 1], [0, 1], "k--", alpha=0.3, label="ideal")
    c_before, a_before = _reliability_bins(y_test, test_probs_raw)
    c_after, a_after = _reliability_bins(y_test, test_probs_calibrated)
    plt.plot(c_before, a_before, "o-", label=f"sebelum kalibrasi (ECE={metrics_raw['ece']:.3f})")
    plt.plot(c_after, a_after, "s-", label=f"sesudah kalibrasi (ECE={metrics_calibrated['ece']:.3f})")
    plt.xlabel("Confidence (probabilitas prediksi)")
    plt.ylabel("Akurasi observasi")
    plt.title("Reliability diagram -- GATNN-DNN (test set)")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "reliability_before_after.png", dpi=120)
    plt.close()

    # --- Laporan ---
    lines = [
        "# C7_evaluasi.md -- Evaluasi Metrik Model",
        "",
        f"Test set (hold-out, C5, scaffold-disjoint): **n={len(test_df)}**, "
        f"dibuka **SATU KALI** di sini (skrip ini). Tidak boleh dipakai lagi untuk tuning.",
        "",
        f"Ekspektasi jujur (PROJECT_FIX_MODEL.md SS/EXECUTION_PLAN_FIX_MODEL.md C7): "
        f"AUC 0.63-0.75 wajar untuk DILI pada dataset seukuran ini; AUC > "
        f"{AUC_SUSPICIOUS_THRESHOLD} berarti audit kebocoran. Tidak ada model di bawah "
        f"yang melewati ambang itu (diverifikasi lewat assert, bukan dibaca manual).",
        "",
        "## Tabel metrik lengkap (test set hold-out)",
        "",
        "| Model | AUC-ROC | AUC-PR | Accuracy | Sensitivity | Specificity | Precision | F1 | MCC | Brier | ECE |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name in ["gatnn_dnn", "random_forest", "lightgbm", "xgboost", "logistic_regression"]:
        r = results[name]
        lines.append(
            f"| {name} | {r['auc_roc']:.4f} | {r['auc_pr']:.4f} | {r['accuracy']:.4f} | "
            f"{r['sensitivity']:.4f} | {r['specificity']:.4f} | {r['precision']:.4f} | "
            f"{r['f1']:.4f} | {r['mcc']:.4f} | {r['brier']:.4f} | {r['ece']:.4f} |"
        )

    best_model = max(results, key=lambda m: results[m]["auc_roc"])
    lines += [
        "",
        f"**Model AUC tertinggi pada test set: `{best_model}`** "
        f"({'GATNN-DNN MENANG' if best_model == 'gatnn_dnn' else 'GATNN-DNN TIDAK menang dari baseline -- dilaporkan apa adanya, tidak di-tuning ulang demi angka lebih bagus'}).",
        "",
        "## Confusion matrix -- GATNN-DNN (test, threshold=0.5, probabilitas terkalibrasi)",
        "",
        "| | Pred 0 | Pred 1 |",
        "|---|---|---|",
        f"| **True 0** | {cm[0][0]} | {cm[0][1]} |",
        f"| **True 1** | {cm[1][0]} | {cm[1][1]} |",
        "",
        "![Confusion Matrix](C7_plots/confusion_matrix.png)",
        "",
        "## Kurva ROC & PR (seluruh model, test set)",
        "",
        "![ROC](C7_plots/roc_curve.png)",
        "",
        "![PR](C7_plots/pr_curve.png)",
        "",
        "## Kalibrasi probabilitas -- GATNN-DNN",
        "",
        f"Kalibrator dilatih pada **VAL set (n={len(val_df)}, <200 sampel -> "
        f"Platt scaling otomatis sesuai ambang `calibrate.py`)**, method terpakai: "
        f"**`{calibrator.method}`**. Diterapkan ke TEST set (probabilitas mentah TEST "
        "tidak pernah dipakai untuk fit kalibrator).",
        "",
        "| | Brier (test) | ECE (test) | AUC-ROC (test, tidak berubah -- kalibrasi monoton) |",
        "|---|---|---|---|",
        f"| Sebelum kalibrasi | {metrics_raw['brier']:.4f} | {metrics_raw['ece']:.4f} | {metrics_raw['auc_roc']:.4f} |",
        f"| Sesudah kalibrasi | {metrics_calibrated['brier']:.4f} | {metrics_calibrated['ece']:.4f} | {metrics_calibrated['auc_roc']:.4f} |",
        "",
        f"**ECE {'membaik' if metrics_calibrated['ece'] < metrics_raw['ece'] else 'TIDAK membaik'} "
        f"setelah kalibrasi** ({metrics_raw['ece']:.4f} -> {metrics_calibrated['ece']:.4f}).",
        "",
        "![Reliability](C7_plots/reliability_before_after.png)",
        "",
        "## Baseline: hyperparameter final (nested CV upscale, TIDAK dicari ulang)",
        "",
        "| Baseline | Hyperparameter | scale_pos_weight/class_weight (dari TRAIN fold) |",
        "|---|---|---|",
        "| Random Forest | n_estimators=500, max_depth=None | class_weight=balanced (built-in) |",
        f"| LightGBM | num_leaves=15, learning_rate=0.1 | scale_pos_weight={spw:.4f} |",
        f"| XGBoost | max_depth=5, learning_rate=0.1 | scale_pos_weight={spw:.4f} |",
        "| Logistic Regression | C=0.1, penalty=l2 | class_weight=balanced (built-in) |",
        "",
        "## Catatan jujur",
        "",
        "- Test set dipakai **satu kali** di eksekusi skrip ini -- riwayat commit membuktikan "
        "`ml/data/processed/test.parquet` baru dibaca pertama kali di commit C7, tidak pernah "
        "di C6 atau sebelumnya.",
        f"- GATNN-DNN {'mengungguli' if best_model == 'gatnn_dnn' else 'tidak mengungguli semua'} "
        "baseline pada test set ini -- angka dilaporkan apa adanya, tidak ada tuning tambahan "
        "setelah test set dibuka.",
        "- Dataset training (~870 senyawa) BERBEDA dari Arm A `upscale` (839 senyawa) -- "
        "AUC absolut di sini tidak dapat dibandingkan 1:1 dengan `22_final_holdout_eval.json` "
        "(_upscale_archive/), hanya dipakai sebagai konteks kewajaran (lihat C4_arsitektur.md SS5).",
    ]
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")

    results_json = {
        "metrics": {m: {k: v for k, v in r.items() if k != "params"} for m, r in results.items()},
        "gatnn_dnn_calibration": {
            "method": calibrator.method,
            "brier_before": metrics_raw["brier"],
            "brier_after": metrics_calibrated["brier"],
            "ece_before": metrics_raw["ece"],
            "ece_after": metrics_calibrated["ece"],
        },
        "confusion_matrix_gatnn_dnn": cm.tolist(),
        "n_train": len(train_df),
        "n_val": len(val_df),
        "n_test": len(test_df),
    }
    RESULTS_JSON_OUT.write_text(json.dumps(results_json, indent=2), encoding="utf-8")

    print(f"\nWrote {REPORT_OUT}")
    print(f"Wrote {RESULTS_JSON_OUT}")
    print(f"Wrote {CALIBRATOR_OUT}")
    print(f"Best model by test AUC: {best_model}")


if __name__ == "__main__":
    main()
