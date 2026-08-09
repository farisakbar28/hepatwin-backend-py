"""F2 (temuan tambahan) -- Verifikasi keterjangkauan LOW_EXPOSURE.

Ditemukan saat membangun uji senyawa acuan F2: kandidat vNo skor terendah
katalog (Calcitonin salmon, AI_LOW di ketiga kandidat T_low/T_high) TETAP
MERAH pada skenario dosis wajar, karena `exposure_category` = HIGH_EXPOSURE
-- BUKAN karena AI band, tapi karena `cmax_auc_ratio` dari PBPKEngine SELALU
lebih tinggi dari `moderate_threshold` (0.30 non-vulnerable / 0.20 vulnerable)
untuk kovariat pasien manapun yang realistis.

Akar sebab: PBPK 4-kompartemen di sini adalah sistem ODE LINEAR (tidak ada
kinetika saturasi) -- dosis menskalakan cmax & auc secara linear dengan
FAKTOR YANG SAMA, sehingga `cmax_auc_ratio` sepenuhnya TIDAK bergantung pada
dosis, hanya pada kovariat pasien (usia, jenis kelamin, berat, tinggi) lewat
parameter alometrik. `dose_per_kg` yang dipakai exposure_evaluator sebagai
kondisi OR TIDAK PERNAH menyelamatkan kasus dosis rendah, karena kondisi rasio
sendiri sudah cukup untuk memicu HIGH/MODERATE terlepas dari dosis.

Skrip ini men-sweep seluruh rentang kovariat pasien valid (`PatientCovariates`,
app/models/schemas.py: usia 0-120, berat 1-350kg, tinggi 30-250cm) dengan BMI
realistis (12-40) dan berbagai dosis relatif (mg/kg), untuk mengukur berapa
persen kombinasi yang benar-benar mencapai LOW_EXPOSURE.

TIDAK mengubah app/services/exposure_evaluator.py -- murni pengukuran
(prinsip kerja #1: jangan mengarang angka, ukur
lewat eksekusi nyata).

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/probe_exposure_reachability.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.exposure_evaluator import ExposureEvaluatorService  # noqa: E402
from app.services.pbpk_engine import PBPKEngine  # noqa: E402

REPORTS_DIR = ROOT / "reports"


def main() -> None:
    engine = PBPKEngine()

    usias = range(18, 91, 3)
    tinggis = [150, 160, 170, 180, 190]
    bmis = [16, 18.5, 22, 25, 28, 30, 33, 37, 40]
    jks = ["L", "P"]
    doses_per_kg = [0.5, 1, 3, 5, 8, 10, 15, 30, 50]

    counts = {"LOW_EXPOSURE": 0, "MODERATE_EXPOSURE": 0, "HIGH_EXPOSURE": 0}
    total = 0
    min_ratio = (999.0, None)
    max_ratio = (-999.0, None)
    low_examples = []

    for usia in usias:
        for tinggi in tinggis:
            for bmi in bmis:
                berat = bmi * (tinggi / 100) ** 2
                if not (30 <= berat <= 250):
                    continue
                for jk in jks:
                    for dpk in doses_per_kg:
                        dose = dpk * berat
                        _, cmax, auc = engine.simulate(
                            dosis_mg=dose, usia=usia, jenis_kelamin=jk,
                            berat_badan_kg=berat, tinggi_badan_cm=tinggi,
                        )
                        exp = ExposureEvaluatorService.evaluate_relative_exposure(
                            cmax=cmax, auc=auc, age=usia, bmi=bmi, dose_mg=dose, weight_kg=berat
                        )
                        total += 1
                        counts[exp["risk_level"]] += 1
                        ratio = exp["cmax_auc_ratio"]
                        if ratio < min_ratio[0]:
                            min_ratio = (ratio, (usia, tinggi, bmi, round(berat, 1), jk, dpk))
                        if ratio > max_ratio[0]:
                            max_ratio = (ratio, (usia, tinggi, bmi, round(berat, 1), jk, dpk))
                        if exp["risk_level"] == "LOW_EXPOSURE":
                            low_examples.append((usia, tinggi, bmi, round(berat, 1), jk, dpk))

    lines = []
    lines.append("# F2 -- Temuan Tambahan: Keterjangkauan LOW_EXPOSURE\n")
    lines.append(
        "Ditemukan saat menjalankan uji senyawa acuan F2 (`scripts/derive_thresholds.py`): "
        "senyawa `vNo-DILI-concern` dengan skor AI terendah katalog (AI_LOW di ketiga kandidat "
        "T_low/T_high) tetap **MERAH** pada skenario dosis wajar -- bukan karena band AI, "
        "melainkan karena `exposure_category` selalu HIGH_EXPOSURE.\n"
    )
    lines.append(f"## Sweep kovariat pasien realistis (n={total})\n")
    lines.append(
        f"Rentang: usia 18-90 (step 3), tinggi 150-190cm, BMI 16-40 (berat diturunkan dari BMI x tinggi², "
        f"dibatasi 30-250kg), kedua jenis kelamin, dosis relatif 0.5-50 mg/kg.\n"
    )
    lines.append("| exposure_category | Jumlah | Persentase |")
    lines.append("|---|---|---|")
    for k in ("LOW_EXPOSURE", "MODERATE_EXPOSURE", "HIGH_EXPOSURE"):
        lines.append(f"| {k} | {counts[k]} | {counts[k]/total*100:.2f}% |")
    lines.append("")
    lines.append(f"- `cmax_auc_ratio` minimum yang tercapai di seluruh sweep: **{min_ratio[0]:.4f}** pada (usia,tinggi,BMI,berat,jk,dosis/kg) = {min_ratio[1]}")
    lines.append(f"- `cmax_auc_ratio` maksimum: **{max_ratio[0]:.4f}** pada {max_ratio[1]}")
    lines.append(
        "- Ambang `moderate_threshold` yang harus dilewati agar LOW: **0.30** (non-vulnerable) / **0.20** (vulnerable, usia>=60 atau BMI>=30)\n"
    )

    lines.append("## Akar sebab (diverifikasi lewat kode, bukan dugaan)\n")
    lines.append(
        "`app/services/pbpk_engine.py` `_simulate_base()` menyelesaikan ODE linear untuk **dosis basis "
        "1.0 mg**, lalu `simulate()` mengalikan seluruh kurva konsentrasi (`sol_y_base * dosis_mg`) secara "
        "linear. Karena `cmax_hati = max(C_L(t))` dan `auc_hati = trapz(C_L(t))` SAMA-SAMA diskalakan "
        "linear oleh `dosis_mg` yang sama, rasio `cmax/auc` **matematis tidak bergantung pada dosis sama "
        "sekali** -- hanya pada parameter alometrik pasien (usia, jenis kelamin, berat, tinggi). Ini "
        "diverifikasi langsung: rasio untuk satu profil pasien tetap **persis sama** (0.441640) pada dosis "
        "50mg, 200mg, 500mg, 1000mg, dan 4000mg.\n"
    )
    lines.append(
        "Konsekuensinya: kondisi `cmax_auc_ratio > moderate_threshold` pada `exposure_evaluator.py` "
        "TIDAK PERNAH bisa diselamatkan oleh dosis rendah (`dose_per_kg < 10`) selama rasio pasien itu "
        "sendiri sudah di atas ambang -- dan dari sweep 20.250 kombinasi realistis di atas, **rasio "
        "SELALU di atas 0.30** (minimum terukur 0.3132, jauh di atas ambang non-vulnerable). Pola ini "
        "**identik secara struktural** dengan temuan SS3.1 (rantai `or` yang membuat "
        "satu kondisi selalu menang) -- hanya saja terjadi di `exposure_evaluator.py`, bukan "
        "`fusion_service.py`, dan bukan pada `dili_score` tapi pada `cmax_auc_ratio`.\n"
    )

    lines.append("## Implikasi untuk cakupan branch `fusion`\n")
    lines.append(
        "- Matriks 3x3 (F3) memetakan `(AI_LOW, EXP_LOW) -> HIJAU`. Bila "
        "`EXP_LOW` PRAKTIS TIDAK TERJANGKAU untuk kovariat pasien realistis manapun (terlepas dari "
        "kandidat T_low/T_high AI mana yang dipilih di F2), maka **HIJAU akan tetap kode mati** setelah "
        "F3 -- DoD proyek \"Hijau terbukti bisa muncul\" TIDAK akan terpenuhi lewat skenario pasien "
        "realistis, walau AI band-nya sendiri sudah benar (AI_LOW tercapai untuk banyak senyawa vNo)."
    )
    lines.append(
        "- Ini BUKAN sesuatu yang bisa diperbaiki di lapisan fusi (F3) -- akar masalahnya ada di "
        "`exposure_evaluator.py` (enam ambang `30.0/10.0/0.40/0.35/0.30/0.20`), yang menurut "
        "SS5 & gerbang K3 **berada di luar wewenang agen untuk diubah** tanpa "
        "keputusan Farmasi eksplisit. F5 (audit exposure_evaluator) SUDAH mencakup analisis sensitivitas "
        "serupa (langkah 4) -- temuan ini MENDAHULUI F5 secara organik karena ditemukan saat membangun uji "
        "acuan F2, dan sebaiknya jadi INPUT UTAMA diskusi K3 dengan Farmasi, bukan ditunda sampai F5/F9."
    )
    lines.append(
        "- Mitigasi yang TERSEDIA tanpa mengubah `exposure_evaluator.py`: matriks F3 tetap diimplementasikan "
        "sesuai rancangan (PRD-setia, K1 disetujui default), dan HIJAU dibuktikan LULUS lewat **unit test "
        "AI-axis-only** (AI_LOW x EXP_LOW disuntik langsung sebagai sel matriks, TIDAK lewat pipeline PBPK "
        "penuh) -- ini membuktikan matriksnya BENAR secara struktural (§3.1/§3.2 AI-axis sudah diperbaiki), "
        "tapi HARUS dinyatakan eksplisit di F9 bahwa HIJAU end-to-end lewat skenario pasien nyata belum "
        "tercapai selama enam ambang exposure belum direvisi Farmasi. Kejujuran ini WAJIB masuk "
        "`reports/F9_limitations_fusion.md`."
    )
    lines.append("")

    if low_examples:
        lines.append(f"## Contoh kombinasi yang MENCAPAI LOW_EXPOSURE (n={len(low_examples)})\n")
        lines.append("| usia | tinggi | BMI | berat(kg) | jk | dosis(mg/kg) |")
        lines.append("|---|---|---|---|---|---|")
        for ex in low_examples[:20]:
            lines.append(f"| {ex[0]} | {ex[1]} | {ex[2]} | {ex[3]} | {ex[4]} | {ex[5]} |")
    else:
        lines.append("## Contoh kombinasi yang mencapai LOW_EXPOSURE\n")
        lines.append("**TIDAK ADA** -- nol dari {} kombinasi realistis yang diuji mencapai LOW_EXPOSURE.\n".format(total))

    out_path = REPORTS_DIR / "F2_exposure_reachability_finding.md"
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print(f"Laporan disimpan: {out_path}")
    print(f"LOW={counts['LOW_EXPOSURE']} MODERATE={counts['MODERATE_EXPOSURE']} HIGH={counts['HIGH_EXPOSURE']} (total={total})")
    print(f"min_ratio={min_ratio}")


if __name__ == "__main__":
    main()
