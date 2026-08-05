"""Bangun model .pt final GATNN-DNN pakai hyperparameter pemenang TU.20/TU.22
(nested CV, ujian ketat v3.0), dilatih pada SELURUH Arm A (839 senyawa =
dev_pool 672 + holdout_set 167).

PENTING (transparansi, konsisten Aturan Main #4/#5): holdout_set SUDAH selesai
tugas EVALUASI-nya di TU.22 (angka AUC 0,6821 dilaporkan di
14_final_comparison.md, dilatih dari dev_pool SAJA). Model .pt di sini
BUKAN model yang sama persis dengan yang menghasilkan angka itu -- ini model
BARU, dilatih ulang dari nol dengan hyperparameter yang SAMA, tapi data
training yang LEBIH BESAR (839 vs 672). Ini praktik standar ML (refit pada
seluruh data setelah nested CV selesai menentukan hyperparameter & melaporkan
performa tak bias) -- TIDAK mencemari validitas angka 0,6821 yang sudah
dilaporkan (evaluasi itu sudah selesai & tidak diulang), tapi juga berarti
performa .pt ini SECARA TEKNIS belum diukur langsung (tidak ada data lain
yang tersisa untuk diuji tanpa bias, karena 839 = seluruh Arm A yang ada).

Split validasi 90/10 di bawah HANYA untuk mekanisme early stopping (kapan
berhenti training), BUKAN evaluasi performa -- makanya cukup random
stratified, bukan scaffold-disjoint (beda tujuan dari holdout_set TU.18).
"""
import json
import logging
from pathlib import Path

import pandas as pd
import torch
from sklearn.model_selection import train_test_split

from hepatwin_ml.train import build_graph_dataset, train_gatnn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Hyperparameter pemenang TU.20 (modus dari 10 fold outer nested CV, tie-break
# rata-rata inner_cv_auc) -- PERSIS yang dipakai GATNN-DNN di TU.22 holdout eval.
FINAL_HYPERPARAMS = {"lr": 0.0005, "hidden": 64, "dropout": 0.2}
SEED = 42
EARLY_STOP_VAL_FRACTION = 0.10


def main() -> None:
    dev_pool = pd.read_parquet("ml/data/processed/arm_a_devpool.parquet")
    holdout = pd.read_parquet("ml/data/processed/arm_a_holdout.parquet")
    full_arm_a = pd.concat([dev_pool, holdout], ignore_index=True)
    logger.info(
        "Arm A penuh: %d senyawa (dev_pool=%d + holdout_set=%d, holdout SUDAH selesai tugas evaluasinya di TU.22)",
        len(full_arm_a), len(dev_pool), len(holdout),
    )

    train_df, earlystop_df = train_test_split(
        full_arm_a, test_size=EARLY_STOP_VAL_FRACTION, stratify=full_arm_a["label_binary"], random_state=SEED
    )
    train_df, earlystop_df = train_df.reset_index(drop=True), earlystop_df.reset_index(drop=True)
    logger.info(
        "Split internal (HANYA utk early stopping, bukan evaluasi performa): train=%d, early-stop-val=%d",
        len(train_df), len(earlystop_df),
    )

    train_graphs = build_graph_dataset(train_df)
    earlystop_graphs = build_graph_dataset(earlystop_df)

    model, _, _ = train_gatnn(
        train_graphs, earlystop_graphs, seed=SEED, max_epochs=300, patience=30, verbose=True,
        lr=FINAL_HYPERPARAMS["lr"], hidden=FINAL_HYPERPARAMS["hidden"], dropout=FINAL_HYPERPARAMS["dropout"],
    )

    Path("ml/models").mkdir(parents=True, exist_ok=True)
    out_pt = "ml/models/model_arm_a_v3_final.pt"
    torch.save(model.state_dict(), out_pt)

    metadata = {
        "model_version": "gatnn-dnn-arm-a-v3-tuned",
        "arm": "A (DILIrank 2.0 saja, 839 senyawa)",
        "architecture": "GATNN-DNN (GATv2Conv x2 + DNN, Wibowo et al. 2025)",
        "hyperparameters": FINAL_HYPERPARAMS,
        "hyperparameter_source": (
            "Modus (kombinasi paling sering menang) dari 10 fold outer nested CV TU.20, "
            "tie-break rata-rata inner_cv_auc tertinggi -- lihat ml/reports/20_nested_cv_scores.md "
            "dan ml/scripts/run_final_holdout_eval.py::select_final_params()"
        ),
        "training_seed": SEED,
        "n_train": len(train_df),
        "n_earlystop_val": len(earlystop_df),
        "n_total_arm_a": len(full_arm_a),
        "note_holdout_reuse": (
            "Model ini dilatih pada SELURUH Arm A (839) termasuk 167 senyawa holdout_set TU.18 -- "
            "holdout SUDAH selesai dipakai untuk evaluasi tak bias di TU.22 (dilaporkan di "
            "14_final_comparison.md, AUC 0.6821 dari model yang dilatih dev_pool SAJA/672 senyawa). "
            "Model .pt INI BUKAN model yang sama persis dengan yang menghasilkan angka 0.6821 -- "
            "ini refit standar pada seluruh data yang tersedia, praktik lazim setelah nested CV "
            "selesai. Performa .pt ini sendiri TIDAK diukur pada data yang belum pernah dilihat "
            "(karena tidak ada lagi data Arm A yang tersisa) -- estimasi performa paling kredibel "
            "yang tersedia untuk arsitektur+hyperparameter ini TETAP AUC 0.6821 dari 14_final_comparison.md."
        ),
        "reference_holdout_auc": 0.6821,
        "reference_holdout_auc_source": "ml/reports/14_final_comparison.md (TU.22, model dilatih dev_pool 672 senyawa)",
    }
    Path("ml/models/model_arm_a_v3_final_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Selesai. Model -> %s", out_pt)


if __name__ == "__main__":
    main()
