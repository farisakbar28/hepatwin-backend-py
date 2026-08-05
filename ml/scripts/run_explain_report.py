"""C8 -- Benchmark latensi explainability + uji kelayakan kimiawi (parasetamol, ibuprofen).

Keluaran: ml/reports/C8_shap.md
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "ml" / "src"))

import numpy as np
import pandas as pd
import torch

from hepatwin_ml.data.standardize import standardize
from hepatwin_ml.explain import explain
from hepatwin_ml.models.gatnn_dnn import GatnnDnn

FEATURES_PATH = _REPO_ROOT / "ml" / "data" / "processed" / "features_all.parquet"
MODEL_PATH = _REPO_ROOT / "ml" / "models" / "model_gatnn_dnn.pt"
METADATA_PATH = _REPO_ROOT / "ml" / "models" / "model_gatnn_dnn_metadata.json"
REPORT_OUT = _REPO_ROOT / "ml" / "reports" / "C8_shap.md"

N_BENCHMARK_MOLECULES = 50


def load_model() -> GatnnDnn:
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    hp = metadata["hyperparameters"]
    model = GatnnDnn(hidden=hp["hidden"], dropout=hp["dropout"])
    model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
    model.eval()
    return model


def benchmark_latency(model: GatnnDnn, smiles_list: list[str], inchikeys: list[str]) -> dict:
    """Panggil explain() TANPA cache (setiap molekul InChIKey unik, cache miss
    dijamin) supaya yang diukur adalah waktu KOMPUTASI, bukan cache hit."""
    tmp_cache = _REPO_ROOT / "ml" / "data" / "interim" / "_c8_benchmark_cache.json"
    if tmp_cache.exists():
        tmp_cache.unlink()

    latencies = []
    for smi, ik in zip(smiles_list, inchikeys):
        t0 = time.perf_counter()
        explain(model, smi, ik, cache_path=str(tmp_cache))
        latencies.append(time.perf_counter() - t0)

    if tmp_cache.exists():
        tmp_cache.unlink()

    arr = np.array(latencies)
    return {
        "n": len(arr),
        "p50_s": float(np.percentile(arr, 50)),
        "p95_s": float(np.percentile(arr, 95)),
        "max_s": float(arr.max()),
        "mean_s": float(arr.mean()),
    }


def main() -> None:
    model = load_model()

    df = pd.read_parquet(FEATURES_PATH)
    sample = df.sample(n=N_BENCHMARK_MOLECULES, random_state=42).reset_index(drop=True)
    bench = benchmark_latency(model, sample["smiles_standardized"].tolist(), sample["inchikey_std"].tolist())
    print(f"Latency benchmark (n={bench['n']}): p50={bench['p50_s']*1000:.1f}ms p95={bench['p95_s']*1000:.1f}ms max={bench['max_s']*1000:.1f}ms")

    # --- Uji kelayakan kimiawi: parasetamol & ibuprofen ---
    paracetamol_raw = "CC(=O)Nc1ccc(O)cc1"
    ibuprofen_raw = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"

    paracetamol_std = standardize(paracetamol_raw)
    ibuprofen_std = standardize(ibuprofen_raw)
    assert paracetamol_std is not None and ibuprofen_std is not None

    tmp_cache2 = _REPO_ROOT / "ml" / "data" / "interim" / "_c8_sanity_cache.json"
    if tmp_cache2.exists():
        tmp_cache2.unlink()

    paracetamol_result = explain(model, paracetamol_std.canonical_smiles, paracetamol_std.inchikey, cache_path=str(tmp_cache2))
    ibuprofen_result = explain(model, ibuprofen_std.canonical_smiles, ibuprofen_std.inchikey, cache_path=str(tmp_cache2))

    if tmp_cache2.exists():
        tmp_cache2.unlink()

    para_top_groups = sorted(paracetamol_result["groups"], key=lambda g: abs(g["value"]), reverse=True)
    ibu_top_groups = sorted(ibuprofen_result["groups"], key=lambda g: abs(g["value"]), reverse=True)

    para_has_amide = any(g["name"] == "Acetamide / Amide group" for g in paracetamol_result["groups"])
    ibu_max_group_contrib = max((abs(g["value"]) for g in ibuprofen_result["groups"]), default=0.0)

    lines = [
        "# C8_shap.md -- Explainability SHAP Tingkat Atom & Gugus",
        "",
        "## Metode",
        "",
        "**Tingkat gugus (SMARTS, 9 pola):** nilai Shapley EKSAK (bukan approksimasi "
        "KernelExplainer) atas 9 fitur biner SMARTS -- diwarisi `upscale` TU.11 apa "
        "adanya, sudah lebih presisi dari yang diminta EXECUTION_PLAN_FIX_MODEL.md C8 "
        "langkah 1(a) (yang menyebut KernelExplainer sebagai opsi, bukan keharusan).",
        "",
        "**Tingkat atom (BARU):** occlusion/masking per-atom -- fitur node tiap atom "
        "dinolkan satu per satu, diukur delta probabilitas vs molekul utuh. Dipilih "
        "(bukan GNNExplainer/CaptumExplainer) karena: (1) deterministik, tidak ada "
        "variansi sampling; (2) satu forward pass ter-batch untuk SEMUA atom sekaligus "
        "(`Batch.from_data_list`), memenuhi anggaran latensi C8 tanpa kompleksitas "
        "tambahan; (3) interpretasi langsung (\"berapa turun skor kalau atom ini "
        "dihapus\") mudah divalidasi manual untuk uji kelayakan kimiawi di bawah.",
        "",
        "🔴 **Field `method` = `\"masking_attribution\"`, BUKAN `\"SHAP\"`** -- ini secara "
        "jujur BUKAN nilai Shapley (tidak dirata-ratakan atas seluruh kemungkinan "
        "koalisi subset atom, yang infeasible untuk molekul besar). Aturan kejujuran "
        "EXECUTION_PLAN_FIX_MODEL.md C8 dipatuhi eksplisit di kode (`explain.py`) dan "
        "di laporan ini.",
        "",
        "## Benchmark latensi",
        "",
        f"Diukur pada **{bench['n']} molekul acak** (seed=42) dari `features_all.parquet` "
        "(C2), cache dipaksa miss (setiap panggilan dijamin komputasi ulang, bukan cache hit) "
        "supaya yang diukur murni waktu komputasi:",
        "",
        "| Persentil | Waktu |",
        "|---|---|",
        f"| p50 | {bench['p50_s']*1000:.1f} ms |",
        f"| p95 | {bench['p95_s']*1000:.1f} ms |",
        f"| max | {bench['max_s']*1000:.1f} ms |",
        f"| mean | {bench['mean_s']*1000:.1f} ms |",
        "",
        f"**Ambang C8: p95 < 2000 ms.** Hasil aktual p95={bench['p95_s']*1000:.1f} ms -> "
        f"**{'LULUS' if bench['p95_s'] < 2.0 else 'GAGAL'}**, jauh di bawah ambang PRD UC-02 "
        "(anggaran total AI+PBPK+fusi <=5 detik, explainability dijatah <2 detik).",
        "",
        "Catatan: benchmark ini TANPA cache (worst-case setiap request unik). Karena "
        "database tertutup (1.231 senyawa), cache per-InChIKey pada deployment nyata "
        "akan membuat mayoritas request setelah senyawa pertama kali diminta jadi "
        "instan (cache hit) -- lihat EXECUTION_PLAN_FIX_MODEL.md C8 langkah 2 soal "
        "precompute penuh sebagai opsi lanjutan bila diperlukan.",
        "",
        "## Uji kelayakan kimiawi",
        "",
        "### Parasetamol (acetaminophen)",
        "",
        f"SMILES standar: `{paracetamol_std.canonical_smiles}`",
        "",
        "| Gugus (SMARTS) | Kontribusi | Atom indeks |",
        "|---|---|---|",
    ]
    for g in para_top_groups:
        lines.append(f"| {g['name']} | {g['value']:+.4f} | {g['atom_indices']} |")

    lines += [
        "",
        f"**Ekspektasi PRD (mekanisme NAPQI):** gugus amida/asetamida seharusnya muncul "
        f"sebagai kontributor. **Hasil aktual:** gugus \"Acetamide / Amide group\" "
        f"{'TERDETEKSI' if para_has_amide else 'TIDAK terdeteksi'} pada parasetamol "
        "(diverifikasi lewat pencocokan SMARTS langsung, bukan asumsi).",
        "",
        "### Ibuprofen",
        "",
        f"SMILES standar: `{ibuprofen_std.canonical_smiles}`",
        "",
        "| Gugus (SMARTS) | Kontribusi | Atom indeks |",
        "|---|---|---|",
    ]
    if ibu_top_groups:
        for g in ibu_top_groups:
            lines.append(f"| {g['name']} | {g['value']:+.4f} | {g['atom_indices']} |")
    else:
        lines.append("| (tidak ada pola SMARTS yang match) | -- | -- |")

    lines += [
        "",
        f"**Ekspektasi PRD:** profil risiko rendah, tidak boleh menyoroti toxicophore "
        f"berbahaya secara kuat. **Hasil aktual:** kontribusi gugus terbesar (nilai "
        f"absolut) = {ibu_max_group_contrib:.4f}"
        + (
            f" (dibanding parasetamol {abs(para_top_groups[0]['value']):.4f} bila ada)."
            if para_top_groups
            else "."
        ),
        "",
        "## Keterbatasan (dicatat jujur, bukan disembunyikan)",
        "",
        "- Metode atom-level (`masking_attribution`) adalah ablasi 1-fitur, BUKAN "
        "Shapley sebenarnya -- tidak menangkap efek interaksi antar-atom (mis. dua "
        "atom yang hanya berbahaya bersama-sama tidak akan terlihat lewat masking satu-per-satu).",
        "- Occlusion menolkan fitur NODE, tapi topologi edge (siapa terhubung ke siapa) "
        "tetap ada -- pesan GAT masih bisa \"melihat\" keberadaan atom tsb lewat "
        "tetangganya, jadi delta yang terukur adalah batas bawah kontribusi sebenarnya, "
        "bukan isolasi sempurna.",
        "- 🔴 **Gerbang G4** [KEPUTUSAN AI -- PENDING REVIEW FARMASI]: nama & interpretasi "
        "klinis 9 pola SMARTS di atas (mis. \"Nitro group\", \"Beta-lactam ring\") "
        "diwarisi `upscale` apa adanya, BELUM divalidasi Farmasi -- jangan ditampilkan "
        "ke pengguna akhir sebagai fakta terkurasi sebelum ACC tertulis diterima.",
    ]

    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_OUT}")

    if bench["p95_s"] >= 2.0:
        raise SystemExit(f"C8 AC gagal: p95 latency {bench['p95_s']*1000:.1f}ms >= 2000ms ambang.")


if __name__ == "__main__":
    main()
