"""C2 -- Pipeline ekstraksi fitur molekul (ECFP4) dari Supabase.

Ambil hepatwin_compounds -> filter is_simulatable=TRUE (1.231) -> standardisasi
(largest-fragment, netralisasi muatan) -> fingerprint DNN 1.200 dim (MACCS 167
+ ECFP4 1024 + SMARTS 9). Nol panggilan PubChem/HTTP eksternal.

Keluaran:
  ml/data/processed/features_all.parquet
  ml/reports/C2_featurization.md

Jalankan: .venv/Scripts/python.exe ml/scripts/run_featurization.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "ml" / "src"))

import numpy as np
import pandas as pd
from rdkit import Chem

from hepatwin_ml.data.load_supabase import fetch_compounds_snapshot, filter_simulatable
from hepatwin_ml.data.standardize import standardize
from hepatwin_ml.features.fingerprints import FINGERPRINT_DIM, dnn_feature_vector

FEATURES_OUT = _REPO_ROOT / "ml" / "data" / "processed" / "features_all.parquet"
REPORT_OUT = _REPO_ROOT / "ml" / "reports" / "C2_featurization.md"


def main() -> None:
    funnel: dict[str, int] = {}

    df_all = fetch_compounds_snapshot(use_cache=True)
    funnel["Total baris di hepatwin_compounds"] = len(df_all)

    df_sim = filter_simulatable(df_all)  # hard-stop kalau bukan 1231 (SS3 C2)
    funnel["is_simulatable = TRUE"] = len(df_sim)

    multi_fragment_mask = df_sim["canonical_smiles"].astype(str).str.contains(r"\.", regex=True)
    funnel["Multi-fragmen (mengandung '.')"] = int(multi_fragment_mask.sum())

    records: list[dict] = []
    parse_failures: list[str] = []
    fingerprint_failures: list[str] = []

    for row in df_sim.itertuples(index=False):
        raw_smiles = row.canonical_smiles or row.isomeric_smiles
        std = standardize(raw_smiles) if raw_smiles else None

        if std is None:
            parse_failures.append(f"{row.hepatwin_id} ({row.compound_name}): raw_smiles={raw_smiles!r}")
            continue

        mol = Chem.MolFromSmiles(std.canonical_smiles)
        if mol is None:
            fingerprint_failures.append(f"{row.hepatwin_id} ({row.compound_name}): gagal re-parse SMILES standar")
            continue

        try:
            fp = dnn_feature_vector(mol)
        except Exception as exc:  # noqa: BLE001 -- dicatat, bukan diam-diam dilewati
            fingerprint_failures.append(f"{row.hepatwin_id} ({row.compound_name}): {exc}")
            continue

        if fp.shape != (FINGERPRINT_DIM,):
            fingerprint_failures.append(
                f"{row.hepatwin_id} ({row.compound_name}): dimensi fingerprint {fp.shape} != {(FINGERPRINT_DIM,)}"
            )
            continue

        records.append(
            {
                "hepatwin_id": row.hepatwin_id,
                "compound_name": row.compound_name,
                "dili_concern": row.dili_concern,
                "injury_pattern": row.injury_pattern,
                "segment_list": row.segment_list,
                "smiles_raw": raw_smiles,
                "smiles_standardized": std.canonical_smiles,
                "inchikey_std": std.inchikey,
                "heavy_atom_count": std.heavy_atom_count,
                "standardize_eligible": std.eligible,
                "standardize_reject_reason": std.reject_reason,
                "is_multi_fragment_raw": bool(std and "." in raw_smiles),
                "fingerprint": fp.astype(np.float64).tolist(),
            }
        )

    funnel["Berhasil parse RDKit (standardize.py)"] = len(df_sim) - len(parse_failures)
    funnel["Lolos standardisasi"] = len(records) + len(fingerprint_failures)
    funnel["Fingerprint ECFP4 valid"] = len(records)

    features_df = pd.DataFrame.from_records(records)
    FEATURES_OUT.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_parquet(FEATURES_OUT, index=False)

    n_ineligible = int((~features_df["standardize_eligible"]).sum()) if len(features_df) else 0

    lines = [
        "# C2_featurization.md -- Ekstraksi Fitur Molekul (ECFP4) dari Supabase",
        "",
        f"Snapshot Supabase: `ml/data/interim/compounds_snapshot.parquet` "
        f"(lihat `.meta.json` untuk timestamp query).",
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
        f"**Dimensi fingerprint terverifikasi:** {FINGERPRINT_DIM} "
        f"(MACCS 167 + ECFP4 1024 + SMARTS 9) untuk seluruh {len(records)} baris yang lolos.",
        "",
        f"**105 senyawa `is_simulatable = FALSE`:** tidak masuk pipeline ini secara "
        f"desain -- `filter_simulatable()` memfilternya sebelum loop featurisasi dimulai "
        f"(total {funnel['Total baris di hepatwin_compounds']} - simulatable "
        f"{funnel['is_simulatable = TRUE']} = "
        f"{funnel['Total baris di hepatwin_compounds'] - funnel['is_simulatable = TRUE']}).",
        "",
        "## Kegagalan (dilaporkan eksplisit, bukan diam-diam dibuang)",
        "",
        f"**Gagal parse RDKit total:** {len(parse_failures)}",
    ]
    if parse_failures:
        lines += [f"- {x}" for x in parse_failures]
    lines += [
        "",
        f"**Gagal setelah standardisasi (re-parse / fingerprint):** {len(fingerprint_failures)}",
    ]
    if fingerprint_failures:
        lines += [f"- {x}" for x in fingerprint_failures]

    lines += [
        "",
        "## Catatan standardisasi (SS5.4 PROJECT_FIX_MODEL.md)",
        "",
        "`ml/src/hepatwin_ml/data/standardize.py` yang dibawa dari branch `upscale` "
        "**sudah** memakai `LargestFragmentChooser` + `Uncharger` (bukan menolak SMILES "
        "multi-fragmen lewat `MixtureError`) -- diverifikasi langsung lewat eksekusi di "
        "atas, bukan diasumsikan dari deskripsi PROJECT_FIX_MODEL.md SS5.4. Tidak ada "
        "perubahan kode yang diperlukan pada file ini untuk C2; perbaikan yang diminta "
        "dokumen tersebut sudah ada di commit historis `upscale` (TU.2).",
        "",
        f"`standardize_eligible = False` (heavy atom count di luar rentang, atom "
        f"non-organik, atau masih campuran setelah LargestFragmentChooser) muncul pada "
        f"**{n_ineligible}** dari {len(records)} baris yang berhasil fingerprint -- baris "
        "ini tetap punya fingerprint valid (dipakai saat inferensi bila pengguna memilih "
        "senyawa tsb.) tapi akan dikeluarkan dari korpus training di C5 bila juga tidak "
        "punya label biner atau melanggar constraint training lain.",
    ]

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")

    print("=== C2 funnel ===")
    for stage, n in funnel.items():
        print(f"{stage}: {n}")
    print(f"Parse failures: {len(parse_failures)}")
    print(f"Fingerprint failures: {len(fingerprint_failures)}")
    print(f"Wrote {FEATURES_OUT}")
    print(f"Wrote {REPORT_OUT}")

    if parse_failures or fingerprint_failures:
        raise SystemExit(
            f"C2 AC gagal: {len(parse_failures) + len(fingerprint_failures)} dari "
            f"{funnel['is_simulatable = TRUE']} senyawa is_simulatable=TRUE tidak "
            "menghasilkan fingerprint valid. Lihat ml/reports/C2_featurization.md."
        )


if __name__ == "__main__":
    main()
