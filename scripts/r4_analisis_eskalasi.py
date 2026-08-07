"""R4 -- Analisis dampak dua jalur eskalasi PRD v2.3 SS8.3.3 (UKUR, JANGAN IMPLEMENTASI).
(EXECUTION_PLAN_FUSION_V23.md R4, PROJECT_FUSION_V23.md SS3.2)

TIDAK mengubah fusion_service.py -- murni pengukuran offline, sesuai peringatan desain
PROJECT_FUSION_V23.md SS3.2: menambahkan "atau metabolic_risk_flag -> KUNING" berisiko
membunuh HIJAU utk semua pengguna BMI>=30 (pola kegagalan identik SS3.1/SS3.2 lama).

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/r4_analisis_eskalasi.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.domain import HepatwinCompound  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

REPORTS_DIR = ROOT / "reports"


def jalur_a_metabolic_risk_flag() -> dict:
    """Dari sweep R2 (20.250 kombinasi pasien x dosis realistis): berapa
    persen kombinasi BMI>=30 (metabolic_risk_flag), dan berapa persen dari
    KOMBINASI YANG SAAT INI LOW_EXPOSURE (berpotensi hijau) berasal dari
    pasien BMI>=30 -- itulah yang akan KEHILANGAN kemungkinan hijau bila
    aturan "metabolic_risk_flag -> minimal KUNING" diaktifkan."""
    csv_path = REPORTS_DIR / "R2_sweep_raw.csv"
    with open(csv_path, newline="", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))

    total = len(rows)
    bmi_ge_30 = [r for r in rows if float(r["bmi"]) >= 30.0]
    low_exposure_rows = [r for r in rows if r["exposure_category"] == "LOW_EXPOSURE"]
    low_exposure_bmi_ge_30 = [r for r in low_exposure_rows if float(r["bmi"]) >= 30.0]

    return {
        "total": total,
        "bmi_ge_30_count": len(bmi_ge_30),
        "bmi_ge_30_pct": len(bmi_ge_30) / total * 100,
        "low_exposure_count": len(low_exposure_rows),
        "low_exposure_bmi_ge_30_count": len(low_exposure_bmi_ge_30),
        "low_exposure_bmi_ge_30_pct_of_low_exposure": (
            len(low_exposure_bmi_ge_30) / len(low_exposure_rows) * 100 if low_exposure_rows else 0.0
        ),
    }


def jalur_b_strong_evidence() -> dict:
    """Tiga tafsiran 'LiverTox strong evidence' -- berapa senyawa terdampak
    (akan SELALU MERAH tanpa memandang skor AI/dosis) untuk tiap tafsiran."""
    db = SessionLocal()
    try:
        total_simulatable = db.scalar(
            select(func.count()).select_from(HepatwinCompound).where(HepatwinCompound.is_simulatable.is_(True))
        )

        specific_pattern = {"Hepatoseluler", "Kolestatik", "Campuran"}

        # (i) Punya injury_pattern spesifik
        n_i = db.scalar(
            select(func.count()).select_from(HepatwinCompound)
            .where(HepatwinCompound.is_simulatable.is_(True))
            .where(HepatwinCompound.injury_pattern.in_(specific_pattern))
        )

        # (ii) livertox_match_method = exact_name DAN injury_pattern spesifik
        n_ii = db.scalar(
            select(func.count()).select_from(HepatwinCompound)
            .where(HepatwinCompound.is_simulatable.is_(True))
            .where(HepatwinCompound.injury_pattern.in_(specific_pattern))
            .where(HepatwinCompound.livertox_match_method == "exact_name")
        )

        # (iii) injury_pattern spesifik DAN dili_concern = vMost
        n_iii = db.scalar(
            select(func.count()).select_from(HepatwinCompound)
            .where(HepatwinCompound.is_simulatable.is_(True))
            .where(HepatwinCompound.injury_pattern.in_(specific_pattern))
            .where(HepatwinCompound.dili_concern == "vMost-DILI-concern")
        )

        # Breakdown per injury_pattern (transparansi)
        pattern_counts = dict(db.execute(
            select(HepatwinCompound.injury_pattern, func.count())
            .where(HepatwinCompound.is_simulatable.is_(True))
            .group_by(HepatwinCompound.injury_pattern)
        ).all())

        return {
            "total_simulatable": total_simulatable,
            "n_i": n_i, "n_ii": n_ii, "n_iii": n_iii,
            "pattern_counts": pattern_counts,
        }
    finally:
        db.close()


def main() -> None:
    a = jalur_a_metabolic_risk_flag()
    b = jalur_b_strong_evidence()

    lines: list[str] = []
    lines.append("# R4 -- Analisis Dampak Dua Jalur Eskalasi PRD v2.3 (UKUR, TIDAK DIIMPLEMENTASI)\n")
    lines.append(
        "\U0001F6A8 **Task ini TIDAK mengubah `fusion_service.py`.** Sesuai peringatan desain "
        "`PROJECT_FUSION_V23.md` SS3.2: menambahkan eskalasi warna mentah-mentah berisiko mengulang "
        "pola kegagalan SS3.1/SS3.2 lama (satu kondisi `atau` yang selalu menang membunuh cabang lain). "
        "Diukur dulu di sini, keputusan implementasi ada di gerbang G1/G2.\n"
    )

    lines.append("## Jalur A -- `metabolic_risk_flag` (BMI >= 30) -> minimal KUNING\n")
    lines.append(f"Berbasis sweep R2 (`reports/R2_sweep_raw.csv`, n={a['total']}):\n")
    lines.append("| Metrik | Nilai |")
    lines.append("|---|---|")
    lines.append(f"| Kombinasi pasien+dosis dgn BMI >= 30 | {a['bmi_ge_30_count']} / {a['total']} ({a['bmi_ge_30_pct']:.2f}%) |")
    lines.append(f"| Kombinasi LOW_EXPOSURE (berpotensi hijau) | {a['low_exposure_count']} / {a['total']} |")
    lines.append(
        f"| Dari kombinasi LOW_EXPOSURE, yang BMI >= 30 (akan kehilangan hijau) | "
        f"{a['low_exposure_bmi_ge_30_count']} / {a['low_exposure_count']} "
        f"({a['low_exposure_bmi_ge_30_pct_of_low_exposure']:.2f}%) |"
    )
    lines.append("")
    lines.append(
        f"**Kesimpulan Jalur A:** bila aturan diaktifkan, **{a['bmi_ge_30_pct']:.1f}% dari seluruh "
        f"kombinasi pasien+dosis realistis** (bukan hanya yang low-exposure -- SELURUH interaksi "
        "pengguna BMI>=30, apa pun senyawa dan dosisnya) TIDAK AKAN PERNAH bisa melihat HIJAU lagi, "
        "karena `metabolic_risk_flag` dicek independen dari AI/exposure band. Ini SEBANDING dengan "
        "pola kegagalan SS3.1 lama (satu kondisi mendominasi). HIJAU masih terjangkau utk pengguna "
        f"BMI < 30 ({100 - a['bmi_ge_30_pct']:.1f}% populasi sweep).\n"
    )

    lines.append("## Jalur B -- \"LiverTox strong evidence\" -> MERAH\n")
    lines.append(f"Basis: {b['total_simulatable']} senyawa `is_simulatable=TRUE`. Breakdown `injury_pattern`:\n")
    lines.append("| injury_pattern | n |")
    lines.append("|---|---|")
    for pat, n in sorted(b["pattern_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"| {pat} | {n} |")
    lines.append("")
    lines.append("| Tafsiran | Kriteria | Senyawa terdampak (selalu MERAH) | % katalog |")
    lines.append("|---|---|---|---|")
    lines.append(f"| (i) | Punya `injury_pattern` spesifik | {b['n_i']} | {b['n_i']/b['total_simulatable']*100:.1f}% |")
    lines.append(f"| (ii) | (i) DAN `livertox_match_method=exact_name` | {b['n_ii']} | {b['n_ii']/b['total_simulatable']*100:.1f}% |")
    lines.append(f"| (iii) | (i) DAN `dili_concern=vMost-DILI-concern` | {b['n_iii']} | {b['n_iii']/b['total_simulatable']*100:.1f}% |")
    lines.append("")
    lines.append(
        f"**Kesimpulan Jalur B:** tafsiran (i) (paling longgar) memaksa **{b['n_i']} senyawa "
        f"({b['n_i']/b['total_simulatable']*100:.1f}% katalog)** SELALU MERAH tanpa memandang skor AI "
        "atau dosis -- matriks 3x3 jadi tidak relevan utk sepertiga katalog. Tafsiran (iii) (paling "
        f"ketat, mensyaratkan skor AI DAN bukti lokasi sejalan) jauh lebih sempit ({b['n_iii']} senyawa, "
        f"{b['n_iii']/b['total_simulatable']*100:.1f}%) -- tapi definisi final tetap keputusan Farmasi "
        "(gerbang G2), bukan agent.\n"
    )

    lines.append("## Sintesis & Usulan (BUKAN keputusan final)\n")
    lines.append(
        "`[KEPUTUSAN AI -- PENDING REVIEW]` Dua alternatif yang TIDAK membunuh cabang lain, konsisten "
        "dgn PRD v2.3 SS8.3.3 sendiri yang menyebut `metabolic_risk_flag` sbg *\"hanya flag naratif; "
        "tidak menurunkan clearance default\"*:\n"
    )
    lines.append(
        "- **Jalur A:** ekspos `metabolic_risk_flag` sbg field naratif terpisah (`metabolic_risk_note`), "
        "ditampilkan sbg peringatan teks di UI, TANPA mengubah warna. Memenuhi maksud PRD tanpa "
        f"mengorbankan HIJAU utk {a['bmi_ge_30_pct']:.0f}% populasi."
    )
    lines.append(
        "- **Jalur B:** \"strong evidence\" memengaruhi `hotspot_intensity`/confidence tampilan (sudah "
        "ada infrastrukturnya sejak F4), BUKAN warna -- bukti kuat terlihat lebih tegas secara visual "
        "tanpa memaksa MERAH pada sepertiga katalog."
    )
    lines.append("")
    lines.append(
        "\U0001F6A8 **Ambiguitas PRD wajib diangkat ke Ketua Tim (bukan diputuskan agent):** PRD v2.3 "
        "SS8.3.3 sendiri berkontradiksi -- teks naratif menyebut `metabolic_risk_flag` \"hanya flag "
        "naratif\", tapi tabel matriks eskalasi di baris yang sama menuliskannya sbg kondisi `atau` yang "
        "mengubah warna KUNING. Kedua tafsiran itu TIDAK bisa benar bersamaan. Perlu klarifikasi eksplisit "
        "sebelum R5 mengimplementasikan apa pun selain opsi default (field informatif tanpa pengaruh warna)."
    )

    with open(REPORTS_DIR / "R4_dampak_eskalasi.md", "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print("Laporan disimpan: reports/R4_dampak_eskalasi.md")
    print(f"Jalur A: BMI>=30 = {a['bmi_ge_30_pct']:.2f}% dari sweep")
    print(f"Jalur B: (i)={b['n_i']} (ii)={b['n_ii']} (iii)={b['n_iii']} dari {b['total_simulatable']}")


if __name__ == "__main__":
    main()
