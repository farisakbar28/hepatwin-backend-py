"""R2 -- Uji ulang keterjangkauan LOW_EXPOSURE di bawah Mesin A v2.3
(PROJECT_FUSION_V23.md SS1.1, EXECUTION_PLAN_FUSION_V23.md R2).

v2.1 (arsip, reports/_v21_archive/F2_exposure_reachability_finding.md): exposure_category berbasis
`cmax_auc_ratio` (dose-independent secara matematis pada ODE linear) -- 0/20.250 kombinasi realistis
mencapai LOW_EXPOSURE.

v2.3 (app/services/exposure_evaluator.py, app/services/pbpk_calibration.py): exposure_category berbasis
`exposure_index = log1p(cmax_liver) + log1p(auc_liver)` dibandingkan kuantil beku
p33=8.238769621406693 / p66=10.919181899644531 dari calibration sweep internal (1.728.324 sampel).
`exposure_index` MAGNITUDE-based -- naik seiring dosis (BEDA fundamental dari rasio v2.1).

Skrip ini men-sweep RENTANG YANG SAMA seperti probe v2.1 supaya perbandingan apel-ke-apel:
usia 18-90 (step 3), tinggi 150-190cm, BMI 16-40 (berat = BMI x (tinggi/100)^2, dibatasi 30-250kg),
kedua jenis kelamin, dosis 0.5-50 mg/kg -- total ~20.250 kombinasi.

XLogP TIDAK divariasikan (di luar cakupan sweep v2.1 asli) -- dipakai None (fallback xlogp_eff=0.0),
opsi paling netral/konservatif, dicatat eksplisit sbg keterbatasan metodologis.

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/probe_exposure_reachability.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services import pbpk_calibration  # noqa: E402
from app.services.exposure_evaluator import ExposureEvaluatorService  # noqa: E402
from app.services.pbpk_engine import PBPKEngine  # noqa: E402

REPORTS_DIR = ROOT / "reports"

# Perbandingan v2.1 (arsip) -- angka literal dari reports/_v21_archive/F2_exposure_reachability_finding.md
V21_COUNTS = {"LOW_EXPOSURE": 0, "MODERATE_EXPOSURE": 2602, "HIGH_EXPOSURE": 17648}
V21_TOTAL = 20250


def main() -> None:
    engine = PBPKEngine()

    usias = range(18, 91, 3)
    tinggis = [150, 160, 170, 180, 190]
    bmis = [16, 18.5, 22, 25, 28, 30, 33, 37, 40]
    jks = ["L", "P"]
    doses_per_kg = [0.5, 1, 3, 5, 8, 10, 15, 30, 50]

    counts = {"LOW_EXPOSURE": 0, "MODERATE_EXPOSURE": 0, "HIGH_EXPOSURE": 0}
    total = 0
    exposure_indices: list[float] = []
    low_examples: list[tuple] = []
    raw_rows: list[dict] = []

    for usia in usias:
        for tinggi in tinggis:
            for bmi in bmis:
                berat = bmi * (tinggi / 100) ** 2
                if not (30 <= berat <= 250):
                    continue
                for jk in jks:
                    for dpk in doses_per_kg:
                        dose = dpk * berat
                        result = engine.simulate_with_diagnostics(
                            dosis_mg=dose, usia=usia, jenis_kelamin=jk,
                            berat_badan_kg=berat, tinggi_badan_cm=tinggi, xlogp=None,
                        )
                        exp = ExposureEvaluatorService.evaluate_relative_exposure(
                            cmax=result.cmax_hati, auc=result.auc_hati
                        )
                        total += 1
                        counts[exp["risk_level"]] += 1
                        exposure_indices.append(exp["exposure_index"])
                        raw_rows.append({
                            "usia": usia, "tinggi": tinggi, "bmi": bmi, "berat": round(berat, 1),
                            "jk": jk, "dosis_mg_per_kg": dpk, "dosis_mg": round(dose, 1),
                            "exposure_index": exp["exposure_index"], "exposure_category": exp["risk_level"],
                        })
                        if exp["risk_level"] == "LOW_EXPOSURE" and len(low_examples) < 20:
                            low_examples.append((usia, tinggi, bmi, round(berat, 1), jk, dpk, round(exp["exposure_index"], 4)))

    # -- Simpan CSV mentah --
    csv_path = REPORTS_DIR / "R2_sweep_raw.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(raw_rows[0].keys()))
        writer.writeheader()
        writer.writerows(raw_rows)

    # -- Uji ketergantungan dosis (v2.1 menunjukkan rasio TETAP 0.441640 di semua dosis -- v2.3 harus berubah) --
    dose_dependency = []
    for dose in [50.0, 200.0, 500.0, 1000.0, 4000.0]:
        result = engine.simulate_with_diagnostics(
            dosis_mg=dose, usia=30, jenis_kelamin="P", berat_badan_kg=65.0, tinggi_badan_cm=165.0, xlogp=None
        )
        exp = ExposureEvaluatorService.evaluate_relative_exposure(cmax=result.cmax_hati, auc=result.auc_hati)
        dose_dependency.append((dose, exp["exposure_index"], exp["shape_ratio_h_inv"], exp["risk_level"]))

    arr = np.array(exposure_indices)
    p33, p66 = pbpk_calibration.P33_EXPOSURE_INDEX, pbpk_calibration.P66_EXPOSURE_INDEX

    lines: list[str] = []
    lines.append("# R2 -- Uji Ulang Keterjangkauan LOW_EXPOSURE (Mesin A v2.3)\n")
    lines.append(f"Sweep {total} kombinasi (usia 18-90 step 3, tinggi 150-190cm, BMI 16-40, kedua jenis kelamin, dosis 0.5-50 mg/kg) -- rentang IDENTIK dengan sweep v2.1 arsip untuk perbandingan apel-ke-apel. XLogP tidak divariasikan (`xlogp=None`, fallback `xlogp_eff=0.0`) -- di luar cakupan sweep asli, dicatat sbg keterbatasan metodologis.\n")

    lines.append("## Tabel perbandingan v2.1 (arsip) vs v2.3\n")
    lines.append("| exposure_category | v2.1 (arsip) | v2.3 (sekarang) |")
    lines.append("|---|---|---|")
    for cat in ("LOW_EXPOSURE", "MODERATE_EXPOSURE", "HIGH_EXPOSURE"):
        v21_pct = V21_COUNTS[cat] / V21_TOTAL * 100
        v23_pct = counts[cat] / total * 100
        lines.append(f"| {cat} | {V21_COUNTS[cat]} ({v21_pct:.2f}%) | {counts[cat]} ({v23_pct:.2f}%) |")
    lines.append("")

    if low_examples:
        lines.append(f"## Contoh kombinasi yang mencapai LOW_EXPOSURE (menampilkan {len(low_examples)} dari {counts['LOW_EXPOSURE']})\n")
        lines.append("| usia | tinggi | BMI | berat(kg) | jk | dosis(mg/kg) | exposure_index |")
        lines.append("|---|---|---|---|---|---|---|")
        for ex in low_examples:
            lines.append(f"| {ex[0]} | {ex[1]} | {ex[2]} | {ex[3]} | {ex[4]} | {ex[5]} | {ex[6]} |")
        lines.append("")
    else:
        lines.append("## Contoh kombinasi yang mencapai LOW_EXPOSURE\n")
        lines.append(
            f"\U0001F6A8 **TIDAK ADA** -- 0 dari {total} kombinasi realistis mencapai LOW_EXPOSURE, "
            "SAMA seperti v2.1. Ini temuan besar yang wajib dieskalasi ke Ketua Tim -- kalibrasi grid "
            "v2.3 tidak mewakili pemakaian nyata aplikasi.\n"
        )

    lines.append("## Sebaran exposure_index\n")
    lines.append(f"Ambang beku: **p33 = {p33:.4f}**, **p66 = {p66:.4f}**\n")
    lines.append("| Statistik | exposure_index |")
    lines.append("|---|---|")
    for label, val in [
        ("min", np.min(arr)), ("p5", np.percentile(arr, 5)), ("p25", np.percentile(arr, 25)),
        ("median", np.median(arr)), ("p75", np.percentile(arr, 75)), ("p95", np.percentile(arr, 95)),
        ("max", np.max(arr)),
    ]:
        lines.append(f"| {label} | {val:.4f} |")
    lines.append("")
    lines.append(
        f"Posisi relatif: {np.sum(arr < p33)} dari {total} sampel ({np.sum(arr < p33)/total*100:.2f}%) "
        f"di bawah p33; {np.sum(arr > p66)} ({np.sum(arr > p66)/total*100:.2f}%) di atas p66.\n"
    )

    lines.append("## Uji ketergantungan dosis (rusak di v2.1, harus berubah di v2.3)\n")
    lines.append("Profil tetap: usia=30, jk=P, berat=65kg, tinggi=165cm. v2.1 (arsip) menunjukkan `cmax_auc_ratio` TETAP PERSIS `0.441640` di semua dosis (50-4000mg) -- bukti bug dose-independence.\n")
    lines.append("| dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |")
    lines.append("|---|---|---|---|")
    for dose, ei, ratio, cat in dose_dependency:
        lines.append(f"| {dose:.0f} | {ei:.4f} | {ratio:.6f} | {cat} |")
    lines.append("")
    ei_values = [d[1] for d in dose_dependency]
    ei_changes = len(set(round(v, 6) for v in ei_values)) > 1
    lines.append(
        f"**exposure_index {'BERUBAH' if ei_changes else 'TETAP KONSTAN'} terhadap dosis** "
        f"({'kontras dgn v2.1 -- bukti perbaikan berhasil' if ei_changes else 'MASIH BUG, sama seperti v2.1'}). "
        f"`shape_ratio_h_inv` (alias `cmax_auc_ratio` lama) {'tetap konstan seperti diharapkan (rasio, bukan magnitude)' if len(set(round(d[2],6) for d in dose_dependency))==1 else 'BERUBAH -- tidak sesuai ekspektasi rasio'}.\n"
    )

    with open(REPORTS_DIR / "R2_exposure_reachability_v23.md", "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print(f"Laporan disimpan: reports/R2_exposure_reachability_v23.md")
    print(f"Total: {total}, LOW={counts['LOW_EXPOSURE']} MODERATE={counts['MODERATE_EXPOSURE']} HIGH={counts['HIGH_EXPOSURE']}")
    print(f"exposure_index changes with dose: {ei_changes}")


if __name__ == "__main__":
    main()
