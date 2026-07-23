"""05 — Model baseline tabular LightGBM.

Dasar: PRD §13 item #4 · Arsitektur §D.6 · EXECUTION_PLAN.md T1.9.

Aturan:
- Impor featurizer dari app.chem.features — JANGAN salin kodenya.
- Load HANYA ml/data/processed/train.csv (708 baris). JANGAN sentuh valid.csv
  atau external_test.csv untuk training/baseline validation.
- LightGBM param sesuai Arsitektur §D.6 (class_weight="balanced", dll).
- 5-fold CV pada train saja. Hitung: akurasi, AUROC, AUC-PR, sensitivity,
  specificity, MCC.
- Simpan ke ml/reports/05_baseline.json — angka nyata dari eksekusi.
- Verifikasi reproducibility: jalankan 2x dengan seed sama → angka identik.
"""
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Barrier: pastikan root repo di sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import lightgbm as lgb
from _common import DATA_PROCESSED, REPORTS, write_report
from rdkit import Chem
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    matthews_corrcoef,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold

from app.chem.features import featurize_batch

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def calculate_metrics(y_true: np.ndarray, y_pred_prob: np.ndarray) -> dict[str, float]:
    """Hitung metrik evaluasi binary classification."""
    y_pred = (y_pred_prob >= 0.5).astype(int)
    
    acc = accuracy_score(y_true, y_pred)
    auroc = roc_auc_score(y_true, y_pred_prob)
    
    # AUC-PR
    precision, recall, _ = precision_recall_curve(y_true, y_pred_prob)
    auc_pr = auc(recall, precision)
    
    # Sensitivity (Recall), Specificity
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
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


def main() -> None:
    seed = 42
    train_path = DATA_PROCESSED / "train.csv"
    if not train_path.exists():
        logger.error("File train.csv tidak ditemukan di %s. Jalankan 04_dedup_split.py dulu.", train_path)
        sys.exit(1)
        
    df_train = pd.read_csv(train_path)
    logger.info("Membaca %d baris data training dari %s", len(df_train), train_path)
    
    # Extract RDKit Mol objects
    mols = []
    y = []
    for idx, row in df_train.iterrows():
        mol = Chem.MolFromSmiles(row["smiles"])
        if mol is not None:
            mols.append(mol)
            y.append(row["label"])
        else:
            logger.warning("Gagal parse SMILES baris ke-%d: %s", idx, row["smiles"])
            
    y = np.array(y, dtype=np.int32)
    logger.info("Berhasil mem-parse %d SMILES menjadi objek RDKit Mol", len(mols))
    
    # Featurize
    logger.info("Ekstraksi fitur menggunakan app.chem.features...")
    X = featurize_batch(mols)
    logger.info("Bentuk matriks fitur: %s", X.shape)
    
    # 5-fold CV on train set only
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    
    metrics_list = []
    
    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y), 1):
        X_train_fold, y_train_fold = X[train_idx], y[train_idx]
        X_val_fold, y_val_fold = X[val_idx], y[val_idx]
        
        # LightGBM Classifier parameter sesuai Arsitektur D.6 & EXECUTION_PLAN T1.9
        model = lgb.LGBMClassifier(
            n_estimators=400,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.6,
            class_weight="balanced",
            random_state=seed,
            verbosity=-1
        )
        
        model.fit(X_train_fold, y_train_fold)
        y_val_prob = model.predict_proba(X_val_fold)[:, 1]
        
        fold_metrics = calculate_metrics(y_val_fold, y_val_prob)
        metrics_list.append(fold_metrics)
        logger.info("Fold %d: AUROC=%.4f, MCC=%.4f", fold, fold_metrics["auroc"], fold_metrics["mcc"])
        
    # Aggregate metrics
    mean_metrics = {}
    std_metrics = {}
    for key in metrics_list[0].keys():
        values = [m[key] for m in metrics_list]
        mean_metrics[key] = float(np.mean(values))
        std_metrics[key] = float(np.std(values))
        
    logger.info("=== Rata-rata Metrik 5-Fold CV ===")
    for key, val in mean_metrics.items():
        logger.info("%s: %.4f (std: %.4f)", key, val, std_metrics[key])
        
    output_json = {
        "seed": seed,
        "n_samples": len(X),
        "n_features": X.shape[1],
        "mean_metrics": mean_metrics,
        "std_metrics": std_metrics,
        "folds": metrics_list
    }
    
    # Simpan laporan json
    json_path = REPORTS / "05_baseline.json"
    REPORTS.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=4)
    logger.info("Menyimpan metrik baseline ke %s", json_path)
    
    # Tulis laporan markdown
    md_lines = [
        "# 05 Laporan Baseline Tabular (LightGBM)",
        "",
        f"- **Jumlah Sampel Training**: {len(X)}",
        f"- **Jumlah Fitur**: {X.shape[1]} (Morgan Fingerprint 2048-bit + 10 Deskriptor + 9 Gugus SMARTS)",
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
    for idx, fold_m in enumerate(metrics_list, 1):
        md_lines.append(
            f"| {idx} | {fold_m['accuracy']:.4f} | {fold_m['auroc']:.4f} | {fold_m['auc_pr']:.4f} | {fold_m['sensitivity']:.4f} | {fold_m['specificity']:.4f} | {fold_m['mcc']:.4f} |"
        )
        
    write_report("05_baseline.md", md_lines)
    logger.info("Laporan markdown disimpan ke %s", REPORTS / "05_baseline.md")


if __name__ == "__main__":
    main()
