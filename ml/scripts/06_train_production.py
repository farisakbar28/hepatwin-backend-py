"""06 — Latih model final di jalur terpilih.

Dasar: PRD §8.3 · EXECUTION_PLAN.md T1.13.

⚠️ ATURAN PROSES (ditetapkan 2026-07-24, lihat docs/Decission_lead.md §3 poin 5):
script ini HANYA boleh dijalankan MANUAL oleh MANUSIA dengan konfirmasi
eksplisit setelah gerbang T1.11 diratifikasi (docs/GATE_DECISION_GNN.md kotak
keputusan terisi tanda tangan Ketua Tim asli) — TIDAK oleh agent otonom.

Aturan:
- Karena gerbang kelayakan menetapkan ML_BACKEND=tabular (LightGBM), kita melatih model
  tabular final menggunakan seluruh training set (dilirank train + valid = 838 baris).
- Simpan artefak model ke backend/app/artifacts/: model.joblib, model_meta.json
- model_meta.json memuat: model_version, backend, trained_at, n_train, feature_names_hash,
  metrics (diisi null sampai T1.16 dijalankan).
"""
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from rdkit import Chem

# Barrier: pastikan root repo di sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _common import DATA_PROCESSED

from app.chem.features import feature_names, featurize_batch
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    seed = 42
    
    # Load both train.csv and valid.csv to train the final production model (838 samples total)
    train_path = DATA_PROCESSED / "train.csv"
    valid_path = DATA_PROCESSED / "valid.csv"
    
    if not train_path.exists() or not valid_path.exists():
        logger.error("File data training/validasi tidak ditemukan. Pastikan 04_dedup_split.py sudah dijalankan.")
        sys.exit(1)
        
    df_train = pd.read_csv(train_path)
    df_valid = pd.read_csv(valid_path)
    df_full = pd.concat([df_train, df_valid], ignore_index=True)
    
    logger.info("Menggabungkan train (%d) dan valid (%d). Total dataset latih: %d", len(df_train), len(df_valid), len(df_full))
    
    # Parse SMILES
    mols = []
    y = []
    for idx, row in df_full.iterrows():
        mol = Chem.MolFromSmiles(row["smiles"])
        if mol is not None:
            mols.append(mol)
            y.append(row["label"])
        else:
            logger.warning("Gagal parse SMILES: %s", row["smiles"])
            
    y = np.array(y, dtype=np.int32)
    
    # Featurize
    logger.info("Ekstraksi fitur menggunakan app.chem.features...")
    X = featurize_batch(mols)
    logger.info("Bentuk matriks fitur final: %s", X.shape)
    
    # Model Parameter sesuai Arsitektur D.6
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
    
    logger.info("Melatih model LightGBM produksi final...")
    model.fit(X, y)
    
    # Simpan ke artifacts
    artifacts_dir = Path(settings.ARTIFACTS_DIR)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = artifacts_dir / "model.joblib"
    joblib.dump(model, model_path)
    logger.info("Model final disimpan ke %s", model_path)
    
    # Hitung hash nama fitur untuk verifikasi integritas
    features = feature_names()
    features_str = ",".join(features)
    feature_names_hash = hashlib.sha256(features_str.encode("utf-8")).hexdigest()
    
    # model_meta.json
    meta = {
        "model_version": "hepatwin-tabular-1.0.0",
        "backend": "tabular",
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "n_train": len(X),
        "feature_names_hash": feature_names_hash,
        "metrics": None  # Wajib NULL sampai T1.16 dijalankan
    }
    
    meta_path = artifacts_dir / "model_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
    logger.info("Metadata model disimpan ke %s dengan metrics=null", meta_path)


if __name__ == "__main__":
    main()
