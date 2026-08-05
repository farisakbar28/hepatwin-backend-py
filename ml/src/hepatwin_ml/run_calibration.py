"""TU.10 -- Demonstrasi kalibrasi end-to-end pada Arm A.

Skema split (wajib TIGA bagian terpisah -- kalibrasi tidak boleh dievaluasi
pada data yang sama dengan yang dipakai untuk fit kalibrator, atau pada data
yang dipakai untuk memilih model/early stopping):
  - train (60%): melatih GATNN-DNN (dengan validasi internal utk early stopping
    diambil dari dalam train, lihat train.py)
  - cal (20%): fit kalibrator (isotonic/Platt)
  - test (20%): evaluasi akhir Brier/ECE before-after, TIDAK pernah dilihat
    model maupun kalibrator sebelumnya

Model dilatih 1 seed (42) untuk demonstrasi -- bukan pengganti evaluasi 5-seed
TU.9, semata untuk memvalidasi pipeline kalibrasi bekerja pada model nyata.
"""
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch_geometric.data import Batch

from hepatwin_ml.calibrate import fit_calibrator
from hepatwin_ml.evaluate import expected_calibration_error
from hepatwin_ml.train import build_graph_dataset, train_gatnn
from sklearn.metrics import brier_score_loss

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    df = pd.read_parquet("ml/data/processed/arm_a.parquet")

    # train 50% / cal 30% / test 20% -- cal set sengaja dibuat >=200 supaya jalur
    # isotonic (bukan cuma fallback Platt) juga terdemonstrasi nyata di Arm A.
    train_df, rest_df = train_test_split(df, test_size=0.5, stratify=df["label_binary"], random_state=42)
    cal_df, test_df = train_test_split(rest_df, test_size=0.4, stratify=rest_df["label_binary"], random_state=42)
    train_df, cal_df, test_df = (d.reset_index(drop=True) for d in (train_df, cal_df, test_df))

    logger.info("train=%d cal=%d test=%d", len(train_df), len(cal_df), len(test_df))

    train_graphs = build_graph_dataset(train_df)
    cal_graphs = build_graph_dataset(cal_df)
    test_graphs = build_graph_dataset(test_df)

    # Pakai cal set sebagai "validasi" early stopping juga -- wajar karena model
    # tidak pernah melihat test set, dan cal set memang bukan test set.
    model, _, _ = train_gatnn(train_graphs, cal_graphs, seed=42, verbose=True)

    model.eval()
    with torch.no_grad():
        cal_probs_raw = torch.sigmoid(model(Batch.from_data_list(cal_graphs))).numpy()
        test_probs_raw = torch.sigmoid(model(Batch.from_data_list(test_graphs))).numpy()
    cal_y = cal_df["label_binary"].to_numpy()
    test_y = test_df["label_binary"].to_numpy()

    calibrator = fit_calibrator(cal_probs_raw, cal_y)
    test_probs_calibrated = calibrator.predict(test_probs_raw)

    before = {
        "brier": brier_score_loss(test_y, test_probs_raw),
        "ece": expected_calibration_error(test_y, test_probs_raw),
    }
    after = {
        "brier": brier_score_loss(test_y, test_probs_calibrated),
        "ece": expected_calibration_error(test_y, test_probs_calibrated),
    }

    # Reliability diagram (10 bin) before vs after, sebagai tabel (bukan PNG).
    bins = np.linspace(0, 1, 11)
    reliability_rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        for label, probs in (("before", test_probs_raw), ("after", test_probs_calibrated)):
            mask = (probs > lo) & (probs <= hi) if lo > 0 else (probs >= lo) & (probs <= hi)
            if mask.sum() == 0:
                continue
            reliability_rows.append(
                {
                    "bin": f"{lo:.1f}-{hi:.1f}",
                    "stage": label,
                    "n": int(mask.sum()),
                    "mean_predicted": float(probs[mask].mean()),
                    "mean_observed": float(test_y[mask].mean()),
                }
            )

    result = {
        "n_train": len(train_df),
        "n_cal": len(cal_df),
        "n_test": len(test_df),
        "calibrator_method": calibrator.method,
        "before": before,
        "after": after,
        "reliability": reliability_rows,
    }
    Path("ml/reports/10_calibration.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "# TU.10 -- Kalibrasi Probabilitas (Arm A, demonstrasi 1-seed)",
        "",
        f"Split: train={len(train_df)}, cal={len(cal_df)}, test={len(test_df)} (stratified, seed=42)",
        f"Metode kalibrator terpilih otomatis: **{calibrator.method}** "
        f"(ambang isotonic UPSCALE.md SS6: cal set >= 200 -> isotonic, dipakai n_cal={len(cal_df)})",
        "",
        "| Tahap | Brier | ECE |",
        "|---|---|---|",
        f"| Sebelum kalibrasi | {before['brier']:.4f} | {before['ece']:.4f} |",
        f"| Sesudah kalibrasi | {after['brier']:.4f} | {after['ece']:.4f} |",
        "",
        "## Reliability diagram (per bin confidence, before vs after)",
        "",
        "| Bin | Tahap | n | Mean predicted | Mean observed |",
        "|---|---|---|---|---|",
    ]
    for row in reliability_rows:
        lines.append(
            f"| {row['bin']} | {row['stage']} | {row['n']} | {row['mean_predicted']:.3f} | {row['mean_observed']:.3f} |"
        )
    Path("ml/reports/10_calibration.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("Selesai. Brier %.4f->%.4f, ECE %.4f->%.4f", before["brier"], after["brier"], before["ece"], after["ece"])


if __name__ == "__main__":
    main()
