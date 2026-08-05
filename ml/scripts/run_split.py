"""C5 -- Bangun korpus training berlabel + split train/val/test scaffold-disjoint.

🔴 Gerbang G1 (korpus 870 berlabel vs 1231 lingkup simulatable) dan G2 (label
InChIKey bertentangan setelah dedup) -- default diterapkan di sini, ditandai
[KEPUTUSAN AI -- PENDING REVIEW], TIDAK memblokir eksekusi (PROJECT_FIX_MODEL.md SS7).

Langkah: buang Ambiguous-DILI-concern -> binerisasi -> dedup InChIKey (G2:
label positif menang) -> hold-out scaffold-disjoint 15-20% (test, dikunci) ->
sisanya dibagi scaffold-kfold jadi train/val.

Keluaran: ml/data/processed/{train,val,test}.parquet, ml/data/interim/split_manifest.json
Laporan: ml/reports/C5_split.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "ml" / "src"))

import numpy as np
import pandas as pd

from hepatwin_ml.data.harmonize_labels import harmonize_vdili_concern
from hepatwin_ml.data.holdout import build_holdout_split
from hepatwin_ml.data.splits import _bemis_murcko_scaffold, scaffold_kfold

FEATURES_IN = _REPO_ROOT / "ml" / "data" / "processed" / "features_all.parquet"
TRAIN_OUT = _REPO_ROOT / "ml" / "data" / "processed" / "train.parquet"
VAL_OUT = _REPO_ROOT / "ml" / "data" / "processed" / "val.parquet"
TEST_OUT = _REPO_ROOT / "ml" / "data" / "processed" / "test.parquet"
MANIFEST_OUT = _REPO_ROOT / "ml" / "data" / "interim" / "split_manifest.json"
REPORT_OUT = _REPO_ROOT / "ml" / "reports" / "C5_split.md"

SEED = 42
N_SIMULATABLE_SCOPE = 1231  # G1: lingkup senyawa simulatable (C2), BUKAN korpus training


def build_labeled_corpus(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict], dict[str, int]]:
    funnel: dict[str, int] = {"is_simulatable=TRUE dengan fingerprint valid (C2)": len(df)}

    labels: list[int | None] = []
    for v in df["dili_concern"]:
        try:
            labels.append(harmonize_vdili_concern(v))
        except ValueError as exc:
            raise SystemExit(f"C5: nilai dili_concern tak dikenal, hentikan: {exc}")
    df = df.assign(label_binary=labels)

    df = df[df["label_binary"].notna()].reset_index(drop=True)
    df["label_binary"] = df["label_binary"].astype(int)
    funnel["Buang Ambiguous-DILI-concern (label biner)"] = len(df)

    # Konvensi: canonical_smiles = smiles_standardized (C2), inchikey = inchikey_std (C2) --
    # supaya ml/src/hepatwin_ml/{data/splits,data/holdout,train}.py (upscale, dipakai apa
    # adanya) yang hardcode nama kolom "canonical_smiles"/"inchikey" tetap bekerja tanpa
    # modifikasi, DAN graf/fingerprint yang dibangun dari kolom ini konsisten dengan C2/C3.
    df = df.rename(columns={"smiles_standardized": "canonical_smiles", "inchikey_std": "inchikey"})

    # G2: dedup InChIKey (garam & basa bebas menyatu setelah standardisasi C2).
    n_collision_groups = 0
    g2_conflicts: list[dict] = []
    resolved_rows = []
    for inchikey, group in df.groupby("inchikey", sort=False):
        if len(group) > 1:
            n_collision_groups += 1
            labels_in_group = sorted(set(group["label_binary"].tolist()))
            if len(labels_in_group) > 1:
                g2_conflicts.append(
                    {
                        "inchikey": inchikey,
                        "hepatwin_ids": group["hepatwin_id"].tolist(),
                        "compound_names": group["compound_name"].tolist(),
                        "labels": group["label_binary"].tolist(),
                    }
                )
                # [KEPUTUSAN AI -- PENDING REVIEW FARMASI] G2 default: label positif
                # menang (paling konservatif untuk alat keselamatan obat).
                winner = group[group["label_binary"] == 1].iloc[0]
            else:
                winner = group.iloc[0]
        else:
            winner = group.iloc[0]
        resolved_rows.append(winner)

    df_dedup = pd.DataFrame(resolved_rows).reset_index(drop=True)
    funnel["Tabrakan dedup (garam<->basa menyatu, n grup)"] = n_collision_groups
    funnel["InChIKey dengan label bertentangan (G2)"] = len(g2_conflicts)
    funnel["Setelah dedup InChIKey (korpus training final)"] = len(df_dedup)
    funnel["Label positif (label_binary=1)"] = int((df_dedup["label_binary"] == 1).sum())
    funnel["Label negatif (label_binary=0)"] = int((df_dedup["label_binary"] == 0).sum())

    return df_dedup, g2_conflicts, funnel


def main() -> None:
    df_features = pd.read_parquet(FEATURES_IN)
    df_corpus, g2_conflicts, funnel = build_labeled_corpus(df_features)

    holdout_df, dev_pool_df = build_holdout_split(df_corpus, seed=SEED)

    # Train/val scaffold split dari dev_pool (bukan random murni, C5 langkah 4).
    # Ambil SATU fold (fold-0) dari scaffold_kfold sebagai val, sisanya train --
    # scaffold_kfold sendiri (upscale, dipakai apa adanya) menjamin satu scaffold
    # tidak terbelah dua fold.
    train_idx, val_idx = next(iter(scaffold_kfold(dev_pool_df, k=5, seed=SEED)))
    train_df = dev_pool_df.iloc[train_idx].reset_index(drop=True)
    val_df = dev_pool_df.iloc[val_idx].reset_index(drop=True)
    test_df = holdout_df  # sudah reset_index di build_holdout_split

    # Verifikasi anti-kebocoran: overlap InChIKey & scaffold antar-subset harus 0.
    subsets = {"train": train_df, "val": val_df, "test": test_df}
    inchikey_sets = {name: set(d["inchikey"]) for name, d in subsets.items()}
    scaffold_sets = {
        name: set(d["canonical_smiles"].apply(_bemis_murcko_scaffold)) for name, d in subsets.items()
    }

    overlap_report: list[str] = []
    names = list(subsets.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            ik_overlap = inchikey_sets[a] & inchikey_sets[b]
            sc_overlap = scaffold_sets[a] & scaffold_sets[b]
            overlap_report.append(f"{a} vs {b}: InChIKey overlap={len(ik_overlap)}, scaffold overlap={len(sc_overlap)}")
            if ik_overlap or sc_overlap:
                raise SystemExit(
                    f"C5 AC gagal: kebocoran data terdeteksi antara {a} dan {b} "
                    f"(InChIKey overlap={len(ik_overlap)}, scaffold overlap={len(sc_overlap)}). "
                    "Hentikan sebelum melanjutkan ke C6."
                )

    TRAIN_OUT.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_parquet(TRAIN_OUT, index=False)
    val_df.to_parquet(VAL_OUT, index=False)
    test_df.to_parquet(TEST_OUT, index=False)

    manifest = {
        "seed": SEED,
        "n_simulatable_scope_G1": N_SIMULATABLE_SCOPE,
        "n_training_corpus_G1": len(df_corpus),
        "splits": {
            name: {
                "n": len(d),
                "n_positive": int((d["label_binary"] == 1).sum()),
                "inchikeys": sorted(d["inchikey"].tolist()),
            }
            for name, d in subsets.items()
        },
        "g2_label_conflicts": g2_conflicts,
    }
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = [
        "# C5_split.md -- Split Dataset Training/Validasi/Testing",
        "",
        "## 🔴 Gerbang G1 -- dua angka korpus, JANGAN disamakan",
        "",
        f"- **{N_SIMULATABLE_SCOPE}** = lingkup senyawa `is_simulatable = TRUE` "
        "(dipakai C2 featurisasi & inferensi runtime -- semua senyawa ini bisa dipilih "
        "pengguna di autocomplete dan akan mendapat skor dari model).",
        f"- **{len(df_corpus)}** = korpus BERLABEL yang benar-benar dipakai training "
        "(setelah buang `Ambiguous-DILI-concern` + dedup InChIKey).",
        "",
        "`[KEPUTUSAN AI -- PENDING REVIEW KETUA TIM]` kedua angka di atas benar dengan arti "
        "berbeda -- tidak digabung/disamakan di laporan mana pun sesuai PROJECT_FIX_MODEL.md SS4.3.",
        "",
        "## Tabel corong",
        "",
        "| Tahap | n |",
        "|---|---|",
    ]
    for stage, n in funnel.items():
        lines.append(f"| {stage} | {n} |")

    lines += [
        "",
        "## 🔴 Gerbang G2 -- InChIKey dengan label bertentangan setelah dedup",
        "",
        f"`[KEPUTUSAN AI -- PENDING REVIEW FARMASI]` ditemukan **{len(g2_conflicts)}** "
        "InChIKey dengan label bertentangan setelah garam & basa bebas menyatu ke "
        "InChIKey standar yang sama. Default diterapkan: **label positif menang** "
        "(paling konservatif untuk alat keselamatan obat).",
        "",
    ]
    if g2_conflicts:
        lines.append("| InChIKey | hepatwin_id | Nama senyawa | Label (per baris) | Pemenang |")
        lines.append("|---|---|---|---|---|")
        for c in g2_conflicts:
            lines.append(
                f"| {c['inchikey']} | {', '.join(c['hepatwin_ids'])} | "
                f"{', '.join(c['compound_names'])} | {c['labels']} | 1 (positif) |"
            )
    else:
        lines.append("(tidak ada konflik ditemukan pada eksekusi ini)")

    lines += [
        "",
        "## Skema split & anti-kebocoran",
        "",
        "- **Test (hold-out):** scaffold-disjoint, 15-20% dari korpus training, "
        "dibangun `hepatwin_ml.data.holdout.build_holdout_split` (upscale, apa adanya). "
        "**Dikunci sejak sini -- tidak disentuh sampai C7.**",
        "- **Train/Val:** sisanya (`dev_pool`), dibagi scaffold-kfold "
        "(`hepatwin_ml.data.splits.scaffold_kfold`, k=5, fold-0 = val, sisanya = train) -- "
        "**bukan random murni**, sesuai penyimpangan yang disengaja dari teks DoD C5 "
        "(stratifikasi label diusahakan tapi scaffold-disjoint diprioritaskan bila konflik, "
        "PROJECT_FIX_MODEL.md/EXECUTION_PLAN_FIX_MODEL.md C5 langkah 4).",
        "",
        "| Subset | n | n label positif | Proporsi positif |",
        "|---|---|---|---|",
    ]
    for name, d in subsets.items():
        n_pos = int((d["label_binary"] == 1).sum())
        lines.append(f"| {name} | {len(d)} | {n_pos} | {n_pos / len(d):.4f} |")

    lines += [
        "",
        "**Verifikasi anti-kebocoran (dieksekusi, bukan diasumsikan):**",
        "",
    ]
    lines += [f"- {r}" for r in overlap_report]

    lines += [
        "",
        "## Segel reproduktibilitas",
        "",
        f"Daftar lengkap InChIKey tiap subset (train/val/test) disimpan di "
        f"`ml/data/interim/split_manifest.json` (di-commit, tidak di-gitignore).",
    ]

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")

    print("=== C5 funnel ===")
    for stage, n in funnel.items():
        print(f"{stage}: {n}")
    print("\n=== splits ===")
    for name, d in subsets.items():
        print(f"{name}: n={len(d)}, n_pos={(d['label_binary'] == 1).sum()}")
    print("\n=== overlap check ===")
    for r in overlap_report:
        print(r)
    print(f"\nWrote {TRAIN_OUT}, {VAL_OUT}, {TEST_OUT}")
    print(f"Wrote {MANIFEST_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
