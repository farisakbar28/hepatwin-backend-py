"""TU.8/TU.9 -- Jalankan baseline RF (ECFP4) & MLP (MACCS+deskriptor) pada
split yang sama dengan GATNN-DNN, untuk tabel perbandingan (UPSCALE.md SS4.4).
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from hepatwin_ml.data.splits import random_kfold, scaffold_kfold
from hepatwin_ml.evaluate import compute_metrics, summarize_across_seeds
from hepatwin_ml.models.baselines import (
    ecfp4_features,
    maccs_descriptor_features,
    make_mlp,
    make_random_forest,
)

SEEDS = [42, 43, 44, 45, 46]


def run_baselines(parquet_path: str, split_type: str, out_json: str, out_md: str, seeds=SEEDS, k: int = 5) -> None:
    df = pd.read_parquet(parquet_path)
    split_fn = random_kfold if split_type == "random" else scaffold_kfold

    ecfp4 = ecfp4_features(df["canonical_smiles"].tolist())
    maccs_desc = maccs_descriptor_features(df["canonical_smiles"].tolist())
    y_all = df["label_binary"].to_numpy()

    rf_metrics, mlp_metrics = [], []
    for seed in seeds:
        for fold_i, (train_idx, val_idx) in enumerate(split_fn(df, k=k, seed=seed)):
            y_train, y_val = y_all[train_idx], y_all[val_idx]

            rf = make_random_forest(seed=seed)
            rf.fit(ecfp4[train_idx], y_train)
            rf_probs = rf.predict_proba(ecfp4[val_idx])[:, 1]
            m = compute_metrics(y_val, rf_probs)
            m["seed"], m["fold"] = seed, fold_i
            rf_metrics.append(m)

            mlp = make_mlp(seed=seed)
            mlp.fit(maccs_desc[train_idx], y_train)
            mlp_probs = mlp.predict_proba(maccs_desc[val_idx])[:, 1]
            m = compute_metrics(y_val, mlp_probs)
            m["seed"], m["fold"] = seed, fold_i
            mlp_metrics.append(m)

    result = {
        "split_type": split_type,
        "n_total": len(df),
        "random_forest": {"per_run": rf_metrics, "summary": summarize_across_seeds(rf_metrics)},
        "mlp": {"per_run": mlp_metrics, "summary": summarize_across_seeds(mlp_metrics)},
    }
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        f"# Baseline RF & MLP -- split={split_type}",
        "",
        f"Dataset: `{parquet_path}` ({len(df)} senyawa), {len(seeds)} seed x {k} fold",
        "",
        "| Metrik | RF mean | RF std | MLP mean | MLP std |",
        "|---|---|---|---|---|",
    ]
    rf_summary = result["random_forest"]["summary"]
    mlp_summary = result["mlp"]["summary"]
    for key in rf_summary:
        if key in ("seed", "fold"):
            continue
        rf_mean, rf_std = rf_summary[key]
        mlp_mean, mlp_std = mlp_summary[key]
        lines.append(f"| {key} | {rf_mean:.4f} | {rf_std:.4f} | {mlp_mean:.4f} | {mlp_std:.4f} |")
    Path(out_md).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="ml/data/processed/arm_a.parquet")
    ap.add_argument("--split", choices=["random", "scaffold"], required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    run_baselines(args.parquet, args.split, args.out_json, args.out_md)


if __name__ == "__main__":
    main()
