"""TU.14 -- Latih model produksi final (Arm A, seed pre-registered 42, TIDAK
di-cherry-pick dari 5 seed TU.9 -- Aturan Main #4).

Split train/cal 80/20 stratified (seed=42). cal set dipakai baik sebagai
validasi early-stopping maupun sebagai set fit kalibrator (isotonic/Platt),
konsisten dengan run_calibration.py (TU.10). Metrik performa yang dilaporkan
ke pengguna (internal_cv_auc) TETAP angka cross-validation TU.9 (0.7385/0.7336),
BUKAN metrik dari split train/cal ini -- karena TU.9 sudah representasi yang
lebih robust (5 seed x 5 fold) dibanding satu split tunggal.

Keluaran: ml/models/model_arm_a.pt, ml/models/calibrator_arm_a.pkl,
ml/models/model_arm_a_metadata.json
"""
import json
import logging
import pickle
from pathlib import Path

import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch_geometric.data import Batch

from hepatwin_ml.calibrate import fit_calibrator
from hepatwin_ml.train import build_graph_dataset, train_gatnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PRODUCTION_SEED = 42  # pertama di SEEDS TU.9 -- pre-registered, bukan hasil cherry-pick


def main() -> None:
    df = pd.read_parquet("ml/data/processed/arm_a.parquet")
    train_df, cal_df = train_test_split(
        df, test_size=0.2, stratify=df["label_binary"], random_state=PRODUCTION_SEED
    )
    train_df, cal_df = train_df.reset_index(drop=True), cal_df.reset_index(drop=True)
    logger.info("train=%d cal=%d (seed=%d)", len(train_df), len(cal_df), PRODUCTION_SEED)

    train_graphs = build_graph_dataset(train_df)
    cal_graphs = build_graph_dataset(cal_df)

    model, cal_y, cal_probs_raw = train_gatnn(train_graphs, cal_graphs, seed=PRODUCTION_SEED, verbose=True)
    calibrator = fit_calibrator(cal_probs_raw, cal_y)
    logger.info("Kalibrator terpilih: %s (n_cal=%d)", calibrator.method, len(cal_df))

    Path("ml/models").mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), "ml/models/model_arm_a.pt")
    with open("ml/models/calibrator_arm_a.pkl", "wb") as f:
        pickle.dump(calibrator, f)

    metadata = {
        "model_version": "gatnn-dnn-arm-a-v1",
        "arm": "A",
        "architecture": "GATNN-DNN (GATv2Conv x2 + DNN, Wibowo et al. 2025)",
        "training_seed": PRODUCTION_SEED,
        "n_train": len(train_df),
        "n_cal": len(cal_df),
        "calibrator_method": calibrator.method,
        "internal_cv_auc_l1_random": 0.7385,
        "internal_cv_auc_l1_std": 0.0291,
        "internal_cv_auc_l2_scaffold": 0.7336,
        "internal_cv_auc_l2_std": 0.0382,
        "internal_cv_source": "ml/reports/09_arm_a_random_l1.json, ml/reports/09_arm_a_scaffold_l2.json (5 seed x 5 fold)",
        "note": "AUC di atas dari cross-validation TU.9 (bukan dari split train/cal script ini), representasi performa yang lebih robust.",
    }
    Path("ml/models/model_arm_a_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Selesai. Artefak tersimpan di ml/models/")


if __name__ == "__main__":
    main()
