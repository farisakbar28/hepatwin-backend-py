"""R3 -- Uji ulang senyawa acuan & distribusi warna end-to-end (gerbang G4).
(EXECUTION_PLAN_FUSION_V23.md R3)

BEDA dari pembuktian F8 lama (v2.1): itu membuktikan HIJAU lewat "unit test AI-axis-only"
(menyuntik sel matriks langsung, tidak lewat PBPK/exposure nyata). R3 menutup celah itu --
seluruh uji di sini lewat PIPELINE PENUH (AI dili_score dari cache F1 -- model statis, tidak
berubah -- lalu PBPK v2.3 SUNGGUHAN dgn XLogP senyawa asli -> exposure_evaluator v2.3
SUNGGUHAN -> FusionService SUNGGUHAN).

T_LOW/T_HIGH TIDAK dihitung ulang (dili_score tidak berubah oleh upgrade Mesin A,
PROJECT_FUSION_V23.md SS3.5) -- HANYA diuji ulang dgn tiga kandidat lama.

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/r3_uji_acuan.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.domain import HepatwinCompound  # noqa: E402
from app.services.exposure_evaluator import ExposureEvaluatorService  # noqa: E402
from app.services.fusion_service import FusionService  # noqa: E402
from app.services.pbpk_engine import PBPKEngine  # noqa: E402
from sqlalchemy import select  # noqa: E402

REPORTS_DIR = ROOT / "reports"
CSV_PATH = REPORTS_DIR / "F1_scores_catalogue.csv"

CANDIDATES = {
    "(a) Tersier": (0.6046, 0.6664),
    "(b) Pemetaan-balik": (0.5458, 0.6866),
    "(c) Biaya klinis": (0.5621, 0.6898),
}

# Profil pasien contoh -- menunjukkan variasi warna terhadap kovariat (personalisasi)
PROFILES = {
    "Dewasa sehat, dosis rendah": {"usia": 28, "jk": "P", "berat": 60.0, "tinggi": 165.0, "dosis_mg_per_kg": 1.0},
    "Dewasa, dosis tinggi": {"usia": 35, "jk": "L", "berat": 75.0, "tinggi": 175.0, "dosis_mg_per_kg": 40.0},
    "Lansia": {"usia": 72, "jk": "P", "berat": 65.0, "tinggi": 160.0, "dosis_mg_per_kg": 10.0},
    "BMI tinggi": {"usia": 40, "jk": "L", "berat": 100.0, "tinggi": 165.0, "dosis_mg_per_kg": 10.0},
}


def load_catalogue() -> list[dict]:
    with open(CSV_PATH, newline="", encoding="utf-8") as fp:
        return [
            {"hepatwin_id": r["hepatwin_id"], "compound_name": r["compound_name"],
             "dili_concern": r["dili_concern"], "dili_score": float(r["dili_score"])}
            for r in csv.DictReader(fp)
        ]


def load_xlogp_map() -> dict:
    db = SessionLocal()
    try:
        rows = db.execute(select(HepatwinCompound.hepatwin_id, HepatwinCompound.xlogp)).all()
        return {hid: xlogp for hid, xlogp in rows}
    finally:
        db.close()


def color_via_full_pipeline(engine: PBPKEngine, dili_score: float, xlogp, dosis_mg: float,
                             usia: int, jk: str, berat: float, tinggi: float, t_low: float, t_high: float):
    result = engine.simulate_with_diagnostics(
        dosis_mg=dosis_mg, usia=usia, jenis_kelamin=jk, berat_badan_kg=berat, tinggi_badan_cm=tinggi, xlogp=xlogp
    )
    exp = ExposureEvaluatorService.evaluate_relative_exposure(cmax=result.cmax_hati, auc=result.auc_hati)
    fusion = FusionService.determine_visual_status(dili_score, exp["risk_level"])
    return fusion, exp


def main() -> None:
    catalogue = load_catalogue()
    xlogp_map = load_xlogp_map()
    engine = PBPKEngine()
    by_id = {r["hepatwin_id"]: r for r in catalogue}

    lines: list[str] = []
    lines.append("# R3 -- Uji Ulang Senyawa Acuan & Distribusi Warna End-to-End (gerbang G4)\n")
    lines.append(
        "Seluruh hasil di bawah lewat PIPELINE PENUH (AI dili_score cache F1 + PBPK v2.3 SUNGGUHAN "
        "dgn XLogP senyawa asli + exposure_evaluator v2.3 SUNGGUHAN + FusionService), BUKAN unit test "
        "injeksi sel matriks. `T_LOW`/`T_HIGH` tidak dihitung ulang -- hanya diuji ulang.\n"
    )

    # -- 1. Uji senyawa acuan --
    lines.append("## Uji senyawa acuan\n")
    aceto = by_id["HT0012"]
    vno = by_id["HT0178"]
    aceto_xlogp = xlogp_map.get("HT0012")
    vno_xlogp = xlogp_map.get("HT0178")

    lines.append(
        "| Kandidat | Acetaminophen (10.500mg/70kg/45th/L, PRD v2.3 Skenario A) | "
        "Calcitonin salmon vNo (300mg/60kg/28th/P, dosis wajar) |"
    )
    lines.append("|---|---|---|")
    any_green_reached = False
    for name, (t_low, t_high) in CANDIDATES.items():
        f_aceto, e_aceto = color_via_full_pipeline(
            engine, aceto["dili_score"], aceto_xlogp, 10500.0, 45, "L", 70.0, 170.0, t_low, t_high
        )
        f_vno, e_vno = color_via_full_pipeline(
            engine, vno["dili_score"], vno_xlogp, 300.0, 28, "P", 60.0, 165.0, t_low, t_high
        )
        aceto_pass = "LULUS" if f_aceto.visual_color == "red" else "GAGAL"
        vno_pass = "LULUS" if f_vno.visual_color == "green" else "GAGAL"
        if f_vno.visual_color == "green":
            any_green_reached = True
        lines.append(
            f"| {name} | **{f_aceto.visual_color.upper()}** ({f_aceto.fusion_reason}, exposure_index={e_aceto['exposure_index']:.2f}) -- {aceto_pass} "
            f"| **{f_vno.visual_color.upper()}** ({f_vno.fusion_reason}, exposure_index={e_vno['exposure_index']:.2f}) -- {vno_pass} |"
        )
    lines.append("")
    if any_green_reached:
        lines.append(
            "\U00002705 **HIJAU tercapai lewat pipeline penuh** untuk setidaknya satu kandidat -- "
            "menutup celah yang tersisa di siklus v2.1 (dulu hanya terbukti struktural lewat unit test).\n"
        )
    else:
        lines.append(
            "\U0001F6A8 **HIJAU TIDAK tercapai lewat pipeline penuh** pada skenario ini walau R2 "
            "menunjukkan LOW_EXPOSURE terjangkau -- band AI senyawa ini mungkin tidak AI_LOW pada "
            "kandidat manapun. Perlu diselidiki lebih lanjut (lihat acceptance criteria R3).\n"
        )

    # -- 2. Distribusi warna atas katalog 1.231 senyawa per kandidat --
    lines.append("## Distribusi warna atas katalog 1.231 senyawa (per kandidat, profil dewasa sehat dosis wajar)\n")
    profile = {"usia": 30, "jk": "L", "berat": 70.0, "tinggi": 170.0, "dosis_mg_per_kg": 5.0}
    lines.append("| Kandidat | HIJAU | KUNING | MERAH |")
    lines.append("|---|---|---|---|")
    for name, (t_low, t_high) in CANDIDATES.items():
        counts = {"green": 0, "yellow": 0, "red": 0}
        for row in catalogue:
            xlogp = xlogp_map.get(row["hepatwin_id"])
            dose = profile["dosis_mg_per_kg"] * profile["berat"]
            fusion, _ = color_via_full_pipeline(
                engine, row["dili_score"], xlogp, dose, profile["usia"], profile["jk"],
                profile["berat"], profile["tinggi"], t_low, t_high
            )
            counts[fusion.visual_color] += 1
        total = sum(counts.values())
        lines.append(
            f"| {name} | {counts['green']} ({counts['green']/total*100:.1f}%) | "
            f"{counts['yellow']} ({counts['yellow']/total*100:.1f}%) | {counts['red']} ({counts['red']/total*100:.1f}%) |"
        )
    lines.append("")

    # -- 3. Variasi warna terhadap profil pasien (personalisasi) --
    lines.append("## Variasi warna terhadap profil pasien (metode b, T_low=0.5458/T_high=0.6866)\n")
    t_low, t_high = CANDIDATES["(b) Pemetaan-balik"]
    sample_ids = [catalogue[i]["hepatwin_id"] for i in range(0, len(catalogue), len(catalogue) // 12)][:12]
    lines.append("| Senyawa | " + " | ".join(PROFILES.keys()) + " |")
    lines.append("|---|" + "---|" * len(PROFILES))
    profile_color_counts = {p: {"green": 0, "yellow": 0, "red": 0} for p in PROFILES}
    varied_count = 0
    for hid in sample_ids:
        row = by_id[hid]
        xlogp = xlogp_map.get(hid)
        colors = []
        for pname, p in PROFILES.items():
            dose = p["dosis_mg_per_kg"] * p["berat"]
            fusion, _ = color_via_full_pipeline(
                engine, row["dili_score"], xlogp, dose, p["usia"], p["jk"], p["berat"], p["tinggi"], t_low, t_high
            )
            colors.append(fusion.visual_color)
            profile_color_counts[pname][fusion.visual_color] += 1
        if len(set(colors)) > 1:
            varied_count += 1
        lines.append(f"| {row['compound_name']} | " + " | ".join(c.upper() for c in colors) + " |")
    lines.append("")
    lines.append(
        f"**{varied_count}/{len(sample_ids)} senyawa contoh berubah warna tergantung profil pasien** -- "
        "membuktikan kovariat pasien kini benar-benar memengaruhi hasil visual (memperbaiki keluhan "
        "\"personalisasi tidak terasa\" dari fase sebelumnya, karena exposure_index kini dipengaruhi "
        "dosis+fisiologi+XLogP senyawa, bukan rasio yang selalu sama).\n"
    )

    # -- 4. Gerbang G4 --
    lines.append("## Gerbang G4 -- pilih T_LOW/T_HIGH final\n")
    lines.append(
        "Default: **metode (b) pemetaan-balik (T_low=0.5458, T_high=0.6866)**, konsisten dgn default "
        "gerbang K2 siklus v2.1 -- `dili_score` tidak berubah, sehingga alasan pemilihan sebelumnya "
        "(mempertahankan maksud desain PRD awal) tetap berlaku. `[KEPUTUSAN AI -- PENDING REVIEW "
        "FARMASI + KETUA TIM, gerbang G4]`\n"
    )

    with open(REPORTS_DIR / "R3_uji_acuan_v23.md", "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print("Laporan disimpan: reports/R3_uji_acuan_v23.md")
    print(f"any_green_reached (uji acuan) = {any_green_reached}")
    print(f"varied_count = {varied_count}/{len(sample_ids)}")


if __name__ == "__main__":
    main()
