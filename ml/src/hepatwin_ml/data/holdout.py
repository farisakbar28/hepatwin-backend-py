"""TU.18 (v3.0) -- Bangun external hold-out set, scaffold-disjoint, 15-20%.

Dasar: UPSCALE.md SS13.1 (K3 dibalik -- external hold-out kini wajib,
instruksi Ketua Tim via Panduan_Training_GATNN-DNN_vs_Konvensional.md).

Urutan wajib: kelompokkan dulu berdasarkan scaffold Bemis-Murcko, ACAK
KELOMPOK SCAFFOLD (bukan senyawa individual) supaya satu scaffold tidak
pernah terbelah antara holdout_set dan dev_pool, lalu ambil kelompok sampai
total 15-20% tercapai. Scaffold-disjoint lebih diutamakan daripada
stratifikasi label sempurna bila keduanya berkonflik (UPSCALE.md SS13.1 poin 6).

🚩 Setelah holdout_set dibangun, file `arm_a_holdout.parquet` TIDAK BOLEH
dibaca lagi oleh kode training/tuning apa pun sampai TU.22 (evaluasi akhir,
sekali jalan).
"""
import json
import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from hepatwin_ml.data.splits import _bemis_murcko_scaffold

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HOLDOUT_FRACTION_MIN = 0.15
HOLDOUT_FRACTION_MAX = 0.20
SEED = 42


def build_holdout_split(df: pd.DataFrame, seed: int = SEED) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """df (Arm A penuh) -> (holdout_df, dev_pool_df), scaffold-disjoint,
    holdout 15-20% dari total. Kelompok scaffold diacak (bukan baris individual)."""
    scaffolds = df["canonical_smiles"].apply(_bemis_murcko_scaffold)
    groups: dict[str, list[int]] = {}
    for idx, scaf in zip(df.index, scaffolds):
        groups.setdefault(scaf, []).append(idx)

    scaffold_keys = list(groups.keys())
    rng = np.random.default_rng(seed)
    shuffled_keys = rng.permutation(scaffold_keys)

    n_total = len(df)
    target_min = int(np.ceil(HOLDOUT_FRACTION_MIN * n_total))
    target_max = int(np.floor(HOLDOUT_FRACTION_MAX * n_total))

    holdout_idx: list[int] = []
    for key in shuffled_keys:
        candidate_size = len(holdout_idx) + len(groups[key])
        if candidate_size > target_max and len(holdout_idx) >= target_min:
            break
        holdout_idx.extend(groups[key])
        if len(holdout_idx) >= target_max:
            break

    holdout_df = df.loc[holdout_idx].reset_index(drop=True)
    dev_pool_df = df.drop(index=holdout_idx).reset_index(drop=True)

    logger.info(
        "Holdout: %d senyawa (%.1f%%), dev_pool: %d senyawa (%.1f%%)",
        len(holdout_df), 100 * len(holdout_df) / n_total,
        len(dev_pool_df), 100 * len(dev_pool_df) / n_total,
    )
    return holdout_df, dev_pool_df


def main() -> None:
    df = pd.read_parquet("ml/data/processed/arm_a.parquet")
    holdout_df, dev_pool_df = build_holdout_split(df, seed=SEED)

    Path("ml/data/processed").mkdir(parents=True, exist_ok=True)
    holdout_df.to_parquet("ml/data/processed/arm_a_holdout.parquet", index=False)
    dev_pool_df.to_parquet("ml/data/processed/arm_a_devpool.parquet", index=False)

    seal = {
        "seed": SEED,
        "n_total": len(df),
        "n_holdout": len(holdout_df),
        "n_dev_pool": len(dev_pool_df),
        "holdout_fraction": len(holdout_df) / len(df),
        "holdout_inchikeys": sorted(holdout_df["inchikey"].tolist()),
    }
    Path("ml/data/interim").mkdir(parents=True, exist_ok=True)
    Path("ml/data/interim/holdout_inchikeys.json").write_text(json.dumps(seal, indent=2), encoding="utf-8")

    holdout_pos_rate = holdout_df["label_binary"].mean()
    dev_pos_rate = dev_pool_df["label_binary"].mean()
    total_pos_rate = df["label_binary"].mean()

    lines = [
        "# 18 -- Konstruksi External Hold-out Set (Arm A, v3.0 K3)",
        "",
        f"Seed: {SEED} (scaffold GROUP shuffle, bukan senyawa individual -- UPSCALE.md SS13.1)",
        "",
        "| Set | n | % dari total | Proporsi label positif |",
        "|---|---|---|---|",
        f"| Total (Arm A) | {len(df)} | 100% | {total_pos_rate:.4f} |",
        f"| holdout_set | {len(holdout_df)} | {100*len(holdout_df)/len(df):.1f}% | {holdout_pos_rate:.4f} |",
        f"| dev_pool | {len(dev_pool_df)} | {100*len(dev_pool_df)/len(df):.1f}% | {dev_pos_rate:.4f} |",
        "",
        f"Selisih proporsi label (holdout vs total): {abs(holdout_pos_rate - total_pos_rate):.4f} "
        "(scaffold-disjoint diutamakan di atas stratifikasi sempurna, sesuai UPSCALE.md SS13.1 poin 6).",
        "",
        "## Segel reproduksibilitas",
        "",
        f"Daftar lengkap {len(holdout_df)} InChIKey holdout_set disimpan di "
        "`ml/data/interim/holdout_inchikeys.json` -- dicek ulang di TU.22 untuk "
        "membuktikan hold-out tidak pernah disentuh sebelum evaluasi akhir.",
    ]
    Path("ml/reports/18_holdout_construction.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("Selesai. Laporan -> ml/reports/18_holdout_construction.md")


if __name__ == "__main__":
    main()
