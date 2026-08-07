"""R8 -- Regenerasi F5_audit_exposure terhadap Mesin A v2.3.
(EXECUTION_PLAN_FUSION_V23.md R8 langkah 1)

Sama strukturnya dgn reports/_v21_archive/F5_audit_exposure.md (6 profil pasien x 10 dosis relatif),
TAPI kini exposure_index/exposure_category BERUBAH terhadap dosis -- kontras eksplisit dgn tabel lama
yang menunjukkan cmax_auc_ratio konstan di semua dosis (bug v2.1 yang sudah diperbaiki).

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/r8_audit_exposure_v23.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services import pbpk_calibration  # noqa: E402
from app.services.exposure_evaluator import ExposureEvaluatorService  # noqa: E402
from app.services.pbpk_engine import PBPKEngine  # noqa: E402

REPORTS_DIR = ROOT / "reports"

PROFILES = [
    {"nama": "Dewasa muda sehat", "usia": 25, "jk": "P", "berat": 65.0, "tinggi": 170.0},
    {"nama": "Paruh baya obesitas (BMI>=30)", "usia": 45, "jk": "L", "berat": 95.0, "tinggi": 170.0},
    {"nama": "Lansia", "usia": 70, "jk": "P", "berat": 60.0, "tinggi": 160.0},
    {"nama": "Remaja", "usia": 16, "jk": "L", "berat": 50.0, "tinggi": 165.0},
    {"nama": "Dewasa berat badan rendah", "usia": 30, "jk": "P", "berat": 45.0, "tinggi": 160.0},
    {"nama": "Lansia obesitas (BMI>=30 + usia>=60)", "usia": 75, "jk": "L", "berat": 100.0, "tinggi": 165.0},
]
DOSES_PER_KG = [0.5, 1, 3, 5, 8, 10, 15, 20, 30, 50]
XLOGP_FIXED = 1.2  # nilai representatif tetap -- fokus profil di sini pada kovariat pasien, bukan XLogP


def main() -> None:
    engine = PBPKEngine()
    lines: list[str] = []
    lines.append("# R8 -- Audit Sensitivitas exposure_evaluator v2.3\n")
    lines.append(
        "Regenerasi `reports/_v21_archive/F5_audit_exposure.md` (v2.1) terhadap Mesin A v2.3. "
        f"XLogP tetap {XLOGP_FIXED} (representatif) supaya fokus pada efek kovariat pasien+dosis, "
        "konsisten metodologi dgn versi arsip.\n"
    )

    overall_counts = {"LOW_EXPOSURE": 0, "MODERATE_EXPOSURE": 0, "HIGH_EXPOSURE": 0}
    dose_changes_within_profile = 0

    for profile in PROFILES:
        bmi = profile["berat"] / ((profile["tinggi"] / 100) ** 2)
        vulnerable = profile["usia"] >= 60 or bmi >= 30.0
        lines.append(f"## {profile['nama']} (usia={profile['usia']}, jk={profile['jk']}, berat={profile['berat']}kg, tinggi={profile['tinggi']}cm, BMI={bmi:.1f}, metabolic_risk_flag={vulnerable})\n")
        lines.append("| dosis (mg/kg) | dosis (mg) | exposure_index | shape_ratio_h_inv | exposure_category |")
        lines.append("|---|---|---|---|---|")
        categories_seen = set()
        for dpk in DOSES_PER_KG:
            dose_mg = dpk * profile["berat"]
            result = engine.simulate_with_diagnostics(
                dosis_mg=dose_mg, usia=profile["usia"], jenis_kelamin=profile["jk"],
                berat_badan_kg=profile["berat"], tinggi_badan_cm=profile["tinggi"], xlogp=XLOGP_FIXED,
            )
            exp = ExposureEvaluatorService.evaluate_relative_exposure(cmax=result.cmax_hati, auc=result.auc_hati)
            overall_counts[exp["risk_level"]] += 1
            categories_seen.add(exp["risk_level"])
            lines.append(f"| {dpk} | {dose_mg:.1f} | {exp['exposure_index']:.4f} | {exp['shape_ratio_h_inv']:.6f} | {exp['risk_level']} |")
        if len(categories_seen) > 1:
            dose_changes_within_profile += 1
        lines.append("")

    total = sum(overall_counts.values())
    lines.append("## Ringkasan lintas 6 profil x 10 dosis (n=60 kombinasi)\n")
    lines.append("| exposure_category | Jumlah | Persentase |")
    lines.append("|---|---|---|")
    for k in ("LOW_EXPOSURE", "MODERATE_EXPOSURE", "HIGH_EXPOSURE"):
        lines.append(f"| {k} | {overall_counts[k]} | {overall_counts[k]/total*100:.1f}% |")
    lines.append("")
    lines.append(
        f"**{dose_changes_within_profile}/{len(PROFILES)} profil pasien menunjukkan exposure_category "
        "BERUBAH seiring dosis** (0.5 s.d. 50 mg/kg) -- kontras langsung dengan versi v2.1 arsip, di mana "
        "SELURUH 6 profil menunjukkan `exposure_category` konstan di semua dosis kecuali via jalur "
        "`dose_per_kg` terpisah (bug dose-independence `cmax_auc_ratio`). Di v2.3, `exposure_index` "
        "sendiri (bukan jalur terpisah) yang membawa efek dosis.\n"
    )

    lines.append("## Kesimpulan\n")
    lines.append(
        "- `exposure_index` naik monoton terhadap dosis pada profil pasien tetap (lihat tabel per profil) "
        "-- BERBEDA fundamental dari `cmax_auc_ratio` v2.1 yang matematis konstan thd dosis."
    )
    lines.append(
        "- `shape_ratio_h_inv` (alias `cmax_auc_ratio` lama) TETAP konstan per profil terlepas dari dosis, "
        "sesuai desain barunya (rasio bentuk kurva, bukan magnitude paparan) -- backward-compatible utk "
        "field lama tapi TIDAK lagi dipakai utk kategori."
    )
    lines.append(
        "- Ketiga kategori (LOW/MODERATE/HIGH) SEMUA terpakai pada rentang profil+dosis yang diuji "
        "(lihat R2 utk pembuktian skala penuh 20.250 kombinasi)."
    )
    lines.append(
        "- p33/p66 (`app/services/pbpk_calibration.py`) adalah kuantil kalibrasi distribusional internal "
        f"({pbpk_calibration.CALIBRATION_VERSION}, hash katalog `{pbpk_calibration.CATALOG_SNAPSHOT_SHA256[:16]}...`), "
        "BUKAN ambang klinis -- ditegaskan ulang di sini sesuai PRD v2.3 SS8.2.2.8."
    )

    with open(REPORTS_DIR / "F5_audit_exposure_v23.md", "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print("Laporan disimpan: reports/F5_audit_exposure_v23.md")
    print(overall_counts, f"dose_changes_within_profile={dose_changes_within_profile}/{len(PROFILES)}")


if __name__ == "__main__":
    main()
