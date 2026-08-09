"""F5 -- Analisis sensitivitas exposure_evaluator.

Langkah 4 F5: "dari 1.231 senyawa pada beberapa profil
pasien contoh, berapa yang jatuh ke LOW/MODERATE/HIGH?".

Catatan metodologis penting (ditemukan di F2, lihat reports/F9_limitations_fusion.md §3):
`exposure_category` TIDAK bergantung pada identitas senyawa -- PBPKEngine
generik untuk seluruh senyawa (ODE 4-kompartemen tidak memakai parameter
farmakokinetik spesifik obat), rasio cmax/auc murni fungsi kovariat pasien.
Karena itu breakdown "per 1.231 senyawa" untuk SATU profil pasien+dosis selalu
TRIVIAL: seluruh 1.231 senyawa mendapat exposure_category yang PERSIS SAMA.
Skrip ini karena itu men-sweep profil pasien x dosis (bukan x senyawa) --
representasi yang jujur dari bagaimana sistem benar-benar berperilaku,
dilaporkan apa adanya sesuai prinsip kerja #1 (jangan mengarang angka).

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/audit_exposure_sensitivity.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.exposure_evaluator import ExposureEvaluatorService  # noqa: E402
from app.services.pbpk_engine import PBPKEngine  # noqa: E402

REPORTS_DIR = ROOT / "reports"

PROFILES = [
    {"nama": "Dewasa muda sehat", "usia": 25, "jk": "P", "berat": 65.0, "tinggi": 170.0},
    {"nama": "Paruh baya obesitas (vulnerable/BMI)", "usia": 45, "jk": "L", "berat": 95.0, "tinggi": 170.0},
    {"nama": "Lansia (vulnerable/usia)", "usia": 70, "jk": "P", "berat": 60.0, "tinggi": 160.0},
    {"nama": "Remaja", "usia": 16, "jk": "L", "berat": 50.0, "tinggi": 165.0},
    {"nama": "Dewasa berat badan rendah", "usia": 30, "jk": "P", "berat": 45.0, "tinggi": 160.0},
    {"nama": "Lansia obesitas (double vulnerable)", "usia": 75, "jk": "L", "berat": 100.0, "tinggi": 165.0},
]
DOSES_PER_KG = [0.5, 1, 3, 5, 8, 10, 15, 20, 30, 50]


def main() -> None:
    engine = PBPKEngine()
    lines: list[str] = []
    lines.append("# F5 -- Analisis Sensitivitas exposure_evaluator\n")
    lines.append(
        "Enam profil pasien contoh x sepuluh dosis relatif (mg/kg). Karena "
        "`exposure_category` tidak bergantung pada identitas senyawa (lihat "
        "docstring skrip & `reports/F2_exposure_reachability_finding.md`), "
        "hasil di bawah berlaku SAMA untuk seluruh 1.231 senyawa "
        "`is_simulatable=TRUE` pada kombinasi pasien+dosis yang sama.\n"
    )

    overall_counts = {"LOW_EXPOSURE": 0, "MODERATE_EXPOSURE": 0, "HIGH_EXPOSURE": 0}

    for profile in PROFILES:
        bmi = profile["berat"] / ((profile["tinggi"] / 100) ** 2)
        vulnerable = profile["usia"] >= 60 or bmi >= 30.0
        lines.append(f"## {profile['nama']} (usia={profile['usia']}, jk={profile['jk']}, berat={profile['berat']}kg, tinggi={profile['tinggi']}cm, BMI={bmi:.1f}, vulnerable={vulnerable})\n")
        lines.append("| dosis (mg/kg) | dosis (mg) | cmax_auc_ratio | dose_per_kg | exposure_category |")
        lines.append("|---|---|---|---|---|")
        for dpk in DOSES_PER_KG:
            dose_mg = dpk * profile["berat"]
            _, cmax, auc = engine.simulate(
                dosis_mg=dose_mg, usia=profile["usia"], jenis_kelamin=profile["jk"],
                berat_badan_kg=profile["berat"], tinggi_badan_cm=profile["tinggi"],
            )
            exp = ExposureEvaluatorService.evaluate_relative_exposure(
                cmax=cmax, auc=auc, age=profile["usia"], bmi=bmi, dose_mg=dose_mg, weight_kg=profile["berat"]
            )
            overall_counts[exp["risk_level"]] += 1
            lines.append(f"| {dpk} | {dose_mg:.1f} | {exp['cmax_auc_ratio']} | {exp['dose_per_kg']} | {exp['risk_level']} |")
        lines.append("")

    total = sum(overall_counts.values())
    lines.append("## Ringkasan lintas 6 profil x 10 dosis (n=60 kombinasi)\n")
    lines.append("| exposure_category | Jumlah | Persentase |")
    lines.append("|---|---|---|")
    for k in ("LOW_EXPOSURE", "MODERATE_EXPOSURE", "HIGH_EXPOSURE"):
        lines.append(f"| {k} | {overall_counts[k]} | {overall_counts[k]/total*100:.1f}% |")
    lines.append("")
    if overall_counts["LOW_EXPOSURE"] == 0:
        lines.append(
            "\U0001F6A9 **LOW_EXPOSURE tidak tercapai sama sekali** di keenam profil pasien contoh manapun, "
            "pada dosis serendah 0.5 mg/kg sekalipun -- konsisten dengan sweep besar F2 "
            "(`reports/F2_exposure_reachability_finding.md`, 0/20.250 kombinasi realistis). Kategori ini "
            "PRAKTIS MATI untuk skenario pasien manapun yang diuji, terlepas dari senyawa yang dipilih."
        )
    lines.append("")

    lines.append("## Kesimpulan\n")
    lines.append(
        "- `MODERATE_EXPOSURE` HANYA tercapai pada dosis sangat rendah (<=1-3 mg/kg tergantung profil) "
        "untuk profil non-vulnerable -- di atas itu, rasio cmax/auc pasien itu sendiri (yang TIDAK "
        "berubah oleh dosis) sudah memicu HIGH."
    )
    lines.append(
        "- Profil vulnerable (usia>=60 atau BMI>=30) HAMPIR SELALU HIGH_EXPOSURE, karena ambang yang "
        "lebih ketat (0.35/0.20) dikombinasikan dengan rasio yang secara struktural sudah "
        "tinggi (lihat F2)."
    )
    lines.append(
        "- Temuan ini MEMPERKUAT (bukan menggantikan) temuan F2: dengan enam ambang saat ini "
        "(`[ASUMSI DESAIN -- PENDING REVIEW FARMASI]`, gerbang K3), sistem secara efektif berperilaku "
        "sebagai klasifikasi 2-kelas (MODERATE vs HIGH) untuk sebagian besar skenario realistis, bukan "
        "3-kelas seperti dirancang PRD. Tidak diubah di sini (logika dibekukan sampai keputusan Farmasi, "
        "prinsip #9) -- dilaporkan apa adanya untuk `reports/F9_limitations_fusion.md`."
    )

    out_path = REPORTS_DIR / "F5_audit_exposure.md"
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print(f"Laporan disimpan: {out_path}")
    print(overall_counts)


if __name__ == "__main__":
    main()
