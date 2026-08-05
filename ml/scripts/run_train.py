"""C6 -- Pelatihan final GATNN-DNN dengan hyperparameter tervalidasi (PROJECT_FIX_MODEL.md SS3).

Hyperparameter JANGAN dicari ulang -- dipakai langsung dari nested CV 10-fold
`upscale` (ml/reports/_upscale_archive/22_final_holdout_eval.json): lr=0.0005,
hidden=64, dropout=0.2. Dilatih dengan 5 seed [42,43,44,45,46] pada train/val
C5; mean+-std dilaporkan. SATU model dipilih untuk produksi: seed=42,
ditetapkan DI SINI SEBELUM melihat hasil seed manapun -- bukan cherry-pick
setelah tahu seed mana yang kebetulan terbaik.

Checkpoint disimpan berdasarkan val_auc TERBAIK selama training (bukan epoch
terakhir) -- logika ini sudah ada di train_gatnn() (upscale, dipakai apa adanya).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "ml" / "src"))

import pandas as pd
import torch

from hepatwin_ml.evaluate import compute_metrics, summarize_across_seeds
from hepatwin_ml.train import SEEDS, build_graph_dataset, train_gatnn

TRAIN_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "train.parquet"
VAL_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "val.parquet"
SPLIT_MANIFEST_PATH = _REPO_ROOT / "ml" / "data" / "interim" / "split_manifest.json"

MODEL_OUT = _REPO_ROOT / "ml" / "models" / "model_gatnn_dnn.pt"
METADATA_OUT = _REPO_ROOT / "ml" / "models" / "model_gatnn_dnn_metadata.json"
LOG_DIR = _REPO_ROOT / "ml" / "reports" / "C6_train_log"
REPORT_OUT = _REPO_ROOT / "ml" / "reports" / "C6_train_summary.md"

FINAL_LR = 0.0005
FINAL_HIDDEN = 64
FINAL_DROPOUT = 0.2
MAX_EPOCHS = 300
PATIENCE = 30
PRODUCTION_SEED = 42  # ditetapkan di awal -- lihat docstring modul


def main() -> None:
    train_df = pd.read_parquet(TRAIN_PATH)
    val_df = pd.read_parquet(VAL_PATH)
    print(f"train: {len(train_df)} senyawa, val: {len(val_df)} senyawa")

    train_graphs = build_graph_dataset(train_df)
    val_graphs = build_graph_dataset(val_df)

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    production_model = None
    t_all = time.time()
    for seed in SEEDS:
        t0 = time.time()
        model, val_y, val_probs = train_gatnn(
            train_graphs,
            val_graphs,
            seed=seed,
            max_epochs=MAX_EPOCHS,
            patience=PATIENCE,
            verbose=True,
            lr=FINAL_LR,
            hidden=FINAL_HIDDEN,
            dropout=FINAL_DROPOUT,
        )
        elapsed = time.time() - t0
        metrics = compute_metrics(val_y, val_probs)
        metrics["seed"] = seed
        metrics["train_seconds"] = round(elapsed, 1)
        results.append(metrics)
        print(f"seed={seed}: val_auc={metrics['auc_roc']:.4f} mcc={metrics['mcc']:.4f} ({elapsed:.1f}s)")

        (LOG_DIR / f"seed_{seed}_val_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )

        if seed == PRODUCTION_SEED:
            production_model = model

    total_elapsed = time.time() - t_all
    assert production_model is not None, f"seed produksi {PRODUCTION_SEED} tidak ditemukan di SEEDS={SEEDS}"

    summary = summarize_across_seeds(results)

    # Determinisme: latih ulang seed produksi, bandingkan val_auc identik (AC C6).
    model_repeat, val_y_repeat, val_probs_repeat = train_gatnn(
        train_graphs,
        val_graphs,
        seed=PRODUCTION_SEED,
        max_epochs=MAX_EPOCHS,
        patience=PATIENCE,
        verbose=False,
        lr=FINAL_LR,
        hidden=FINAL_HIDDEN,
        dropout=FINAL_DROPOUT,
    )
    metrics_repeat = compute_metrics(val_y_repeat, val_probs_repeat)
    metrics_original = next(r for r in results if r["seed"] == PRODUCTION_SEED)
    determinism_ok = abs(metrics_repeat["auc_roc"] - metrics_original["auc_roc"]) < 1e-9

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    torch.save(production_model.state_dict(), MODEL_OUT)

    split_manifest_sha256 = hashlib.sha256(SPLIT_MANIFEST_PATH.read_bytes()).hexdigest()

    metadata = {
        "model_version": "gatnn-dnn-fixmodel-v1",
        "architecture": "GATv2Conv x2 (heads=4, edge_dim=6) + DNN(1200->512->128) -> fusion(384->128->1), logit",
        "hyperparameters": {
            "lr": FINAL_LR,
            "hidden": FINAL_HIDDEN,
            "dropout": FINAL_DROPOUT,
            "weight_decay": 1e-4,
            "batch_size": 32,
            "max_epochs": MAX_EPOCHS,
            "patience": PATIENCE,
            "optimizer": "AdamW",
            "scheduler": "ReduceLROnPlateau(mode=max, factor=0.5, patience=10)",
            "loss": "BCEWithLogitsLoss(pos_weight=from train fold only)",
        },
        "hyperparameter_provenance": (
            "nested CV 10-fold, branch upscale, "
            "ml/reports/_upscale_archive/22_final_holdout_eval.json -- TIDAK dicari ulang"
        ),
        "production_seed": PRODUCTION_SEED,
        "n_train": len(train_df),
        "n_val": len(val_df),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "split_manifest_sha256": split_manifest_sha256,
        "checkpoint_selection": "val_auc terbaik selama training (bukan epoch terakhir)",
        "val_metrics_production_seed": metrics_original,
        "val_metrics_across_5_seeds_mean_std": summary,
        "determinism_check": {
            "repeat_seed": PRODUCTION_SEED,
            "auc_roc_original": metrics_original["auc_roc"],
            "auc_roc_repeat": metrics_repeat["auc_roc"],
            "identical": determinism_ok,
        },
    }
    METADATA_OUT.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    lines = [
        "# C6_train_summary.md -- Pelatihan Model & Checkpointing",
        "",
        f"Dataset: train={len(train_df)} senyawa, val={len(val_df)} senyawa "
        f"(dari ml/data/processed/{{train,val}}.parquet, C5).",
        f"Hyperparameter (JANGAN dicari ulang, PROJECT_FIX_MODEL.md SS3): "
        f"lr={FINAL_LR}, hidden={FINAL_HIDDEN}, dropout={FINAL_DROPOUT}.",
        f"Total waktu pelatihan 5 seed: {total_elapsed/60:.1f} menit.",
        "",
        "## Hasil per seed (val set)",
        "",
        "| Seed | AUC-ROC | AUC-PR | MCC | Accuracy | Brier | ECE | Waktu (s) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['seed']} | {r['auc_roc']:.4f} | {r['auc_pr']:.4f} | {r['mcc']:.4f} | "
            f"{r['accuracy']:.4f} | {r['brier']:.4f} | {r['ece']:.4f} | {r['train_seconds']:.1f} |"
        )

    lines += [
        "",
        "## Ringkasan lintas 5 seed (mean +- std)",
        "",
        "| Metrik | Mean | Std |",
        "|---|---|---|",
    ]
    for key, (mean, std) in summary.items():
        if key in ("seed", "train_seconds"):
            continue
        lines.append(f"| {key} | {mean:.4f} | {std:.4f} |")

    lines += [
        "",
        f"## Model produksi: seed={PRODUCTION_SEED}",
        "",
        f"Ditetapkan **sebelum** melihat hasil seed manapun (anti cherry-pick, "
        "EXECUTION_PLAN_FIX_MODEL.md C6 langkah 5). Checkpoint disimpan berdasarkan "
        "`val_auc` terbaik selama training, bukan epoch terakhir.",
        "",
        f"- val_auc: {metrics_original['auc_roc']:.4f}",
        f"- val_mcc: {metrics_original['mcc']:.4f}",
        "",
        "## Uji determinisme",
        "",
        f"Melatih ulang seed={PRODUCTION_SEED} dengan hyperparameter identik: "
        f"val_auc run pertama={metrics_original['auc_roc']:.6f}, "
        f"run kedua={metrics_repeat['auc_roc']:.6f} -> "
        f"**{'IDENTIK' if determinism_ok else 'BERBEDA (perlu investigasi)'}**.",
        "",
        "## Artefak",
        "",
        f"- `ml/models/model_gatnn_dnn.pt` (state_dict model seed={PRODUCTION_SEED})",
        "- `ml/models/model_gatnn_dnn_metadata.json` (hyperparameter, seed, n_train, "
        "tanggal, hash split_manifest.json, metrik val)",
        "- `ml/reports/C6_train_log/seed_<n>_val_metrics.json` (log per seed)",
    ]
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nWrote {MODEL_OUT}")
    print(f"Wrote {METADATA_OUT}")
    print(f"Wrote {REPORT_OUT}")
    print(f"Determinism check: {'OK' if determinism_ok else 'FAILED'}")

    if not determinism_ok:
        raise SystemExit(
            "C6 AC gagal: melatih ulang seed yang sama menghasilkan val_auc berbeda "
            f"({metrics_original['auc_roc']} vs {metrics_repeat['auc_roc']})."
        )


if __name__ == "__main__":
    main()
