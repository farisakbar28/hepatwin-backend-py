"""F2 -- Penurunan ambang T_low/T_high dari data (gerbang K2).

Menghitung TIGA kandidat ambang warna atas distribusi nyata `dili_score`
(reports/F1_scores_catalogue.csv, 1.231 senyawa is_simulatable=TRUE):

  (a) Tersier      -- T_low = persentil-33, T_high = persentil-67
  (b) Pemetaan-balik -- skor kalibrator utk raw=0.30 & raw=0.70
  (c) Biaya klinis  -- T_low pada persentil-5 gabungan {vMost,vLess} (FNR<=5%);
                       T_high pada persentil-95 vNo (perpanjangan simetris utk
                       false-positive-rate rendah pada label MERAH -- dokumen
                       hanya menspesifikasikan kriteria utk T_low, T_high di sini
                       adalah interpretasi AI, ditandai eksplisit di laporan)

Untuk tiap kandidat: distribusi warna (AI-band murni, 3 bin dari dili_score
saja -- KONSISTEN dengan metodologi F1, exposure_category tidak dimasukkan di
sini karena bergantung pasien, bukan senyawa), distribusi per dili_concern,
sensitivity/specificity pada T_low sbg ambang biner, dan uji dua senyawa acuan
via pipeline PBPK + exposure + matriks kandidat (BUKAN via FusionService lama
-- matriks 3x3 baru diimplementasikan di F3, di sini kita EVALUASI kandidat
sebelum matriks final ditulis).

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/derive_thresholds.py
"""
import csv
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.services.exposure_evaluator import ExposureEvaluatorService  # noqa: E402
from app.services.pbpk_engine import PBPKEngine  # noqa: E402

REPORTS_DIR = ROOT / "reports"
CSV_PATH = REPORTS_DIR / "F1_scores_catalogue.csv"


def load_scores():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as fp:
        for r in csv.DictReader(fp):
            rows.append({"hepatwin_id": r["hepatwin_id"], "compound_name": r["compound_name"],
                         "dili_concern": r["dili_concern"], "dili_score": float(r["dili_score"])})
    return rows


def method_a(scores: np.ndarray) -> tuple[float, float]:
    return float(np.percentile(scores, 33)), float(np.percentile(scores, 67))


def method_b() -> tuple[float, float]:
    calibrator_file = Path(settings.AI_MODEL_PATH).with_name("calibrator_gatnn_dnn.pkl")
    with open(calibrator_file, "rb") as f:
        calibrator = pickle.load(f)
    t_low = float(calibrator.predict([0.30])[0])
    t_high = float(calibrator.predict([0.70])[0])
    return t_low, t_high


def method_c(rows: list[dict]) -> tuple[float, float]:
    concern_scores = {}
    for r in rows:
        concern_scores.setdefault(r["dili_concern"], []).append(r["dili_score"])
    most_less = np.array(concern_scores.get("vMost-DILI-concern", []) + concern_scores.get("vLess-DILI-concern", []))
    no_concern = np.array(concern_scores.get("vNo-DILI-concern", []))
    t_low = float(np.percentile(most_less, 5))
    t_high = float(np.percentile(no_concern, 95))
    return t_low, t_high


def color_of(score: float, t_low: float, t_high: float) -> str:
    if score < t_low:
        return "HIJAU"
    if score > t_high:
        return "MERAH"
    return "KUNING"


def color_distribution(rows: list[dict], t_low: float, t_high: float) -> dict:
    counts = {"HIJAU": 0, "KUNING": 0, "MERAH": 0}
    for r in rows:
        counts[color_of(r["dili_score"], t_low, t_high)] += 1
    return counts


def per_concern_distribution(rows: list[dict], t_low: float, t_high: float) -> dict:
    out: dict[str, dict] = {}
    for r in rows:
        c = out.setdefault(r["dili_concern"], {"HIJAU": 0, "KUNING": 0, "MERAH": 0})
        c[color_of(r["dili_score"], t_low, t_high)] += 1
    return out


def sensitivity_specificity(rows: list[dict], t_low: float) -> tuple[float, float, int, int]:
    """Ambang biner pada T_low: positif = punya kekhawatiran DILI (vMost/vLess),
    diprediksi positif bila dili_score >= T_low (TIDAK masuk zona hijau).
    Ambiguous-DILI-concern DIKECUALIKAN (ground truth tidak jelas)."""
    tp = fn = tn = fp = 0
    n_ambiguous = 0
    for r in rows:
        concern = r["dili_concern"]
        if concern == "Ambiguous-DILI-concern":
            n_ambiguous += 1
            continue
        actual_positive = concern in ("vMost-DILI-concern", "vLess-DILI-concern")
        predicted_positive = r["dili_score"] >= t_low
        if actual_positive and predicted_positive:
            tp += 1
        elif actual_positive and not predicted_positive:
            fn += 1
        elif not actual_positive and not predicted_positive:
            tn += 1
        else:
            fp += 1
    sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    return sensitivity, specificity, tp + fn + tn + fp, n_ambiguous


def reference_compound_tests(rows: list[dict], t_low: float, t_high: float) -> list[str]:
    by_id = {r["hepatwin_id"]: r for r in rows}
    out = []

    # -- Acetaminophen, Skenario A PRD UC-02: overdosis 4000mg, 40yo L, 70kg, 168cm --
    aceto = by_id["HT0012"]
    ai_band = "AI_LOW" if aceto["dili_score"] < t_low else ("AI_HIGH" if aceto["dili_score"] > t_high else "AI_MID")
    ts, cmax, auc = PBPKEngine().simulate(dosis_mg=4000.0, usia=40, jenis_kelamin="L", berat_badan_kg=70.0, tinggi_badan_cm=168.0)
    bmi = 70.0 / ((168.0 / 100) ** 2)
    exp = ExposureEvaluatorService.evaluate_relative_exposure(cmax=cmax, auc=auc, age=40, bmi=bmi, dose_mg=4000.0, weight_kg=70.0)
    exp_band = exp["risk_level"]
    final = "MERAH" if (ai_band == "AI_HIGH" or exp_band == "HIGH_EXPOSURE") else ("HIJAU" if (ai_band == "AI_LOW" and exp_band == "LOW_EXPOSURE") else "KUNING")
    out.append(
        f"Acetaminophen (HT0012, dili_score={aceto['dili_score']:.4f}, {ai_band}) x overdosis 4000mg/70kg/40th "
        f"({exp_band}, dose_per_kg={exp['dose_per_kg']}, cmax_auc_ratio={exp['cmax_auc_ratio']}) -> **{final}** "
        f"(harapan: MERAH -- {'LULUS' if final == 'MERAH' else 'GAGAL'})"
    )

    # -- Calcitonin salmon (vNo, skor terendah katalog), dosis rendah terapeutik wajar --
    safe = by_id["HT0178"]
    ai_band2 = "AI_LOW" if safe["dili_score"] < t_low else ("AI_HIGH" if safe["dili_score"] > t_high else "AI_MID")
    ts2, cmax2, auc2 = PBPKEngine().simulate(dosis_mg=200.0, usia=30, jenis_kelamin="P", berat_badan_kg=65.0, tinggi_badan_cm=165.0)
    bmi2 = 65.0 / ((165.0 / 100) ** 2)
    exp2 = ExposureEvaluatorService.evaluate_relative_exposure(cmax=cmax2, auc=auc2, age=30, bmi=bmi2, dose_mg=200.0, weight_kg=65.0)
    exp_band2 = exp2["risk_level"]
    final2 = "MERAH" if (ai_band2 == "AI_HIGH" or exp_band2 == "HIGH_EXPOSURE") else ("HIJAU" if (ai_band2 == "AI_LOW" and exp_band2 == "LOW_EXPOSURE") else "KUNING")
    out.append(
        f"Calcitonin salmon (HT0178, vNo, dili_score={safe['dili_score']:.4f}, {ai_band2}) x dosis wajar 200mg/65kg/30th "
        f"({exp_band2}, dose_per_kg={exp2['dose_per_kg']}, cmax_auc_ratio={exp2['cmax_auc_ratio']}) -> **{final2}** "
        f"(harapan: HIJAU tercapai -- {'LULUS' if final2 == 'HIJAU' else 'GAGAL'})"
    )
    return out


def main() -> None:
    rows = load_scores()
    scores = np.array([r["dili_score"] for r in rows], dtype=float)

    candidates = {
        "(a) Tersier": method_a(scores),
        "(b) Pemetaan-balik": method_b(),
        "(c) Biaya klinis": method_c(rows),
    }

    lines: list[str] = []
    lines.append("# F2 -- Penurunan Ambang T_low / T_high dari Data\n")
    lines.append(f"Berbasis `reports/F1_scores_catalogue.csv` (n={len(rows)}).\n")

    lines.append("## Ringkasan tiga kandidat\n")
    lines.append("| Metode | T_low | T_high |")
    lines.append("|---|---|---|")
    for name, (tl, th) in candidates.items():
        lines.append(f"| {name} | {tl:.4f} | {th:.4f} |")
    lines.append("")
    lines.append(
        "**Catatan metode (c):** dokumen F2 hanya menspesifikasikan kriteria "
        "T_low (persentil-5 gabungan vMost+vLess, false negative rate <=5%). T_high metode (c) di atas "
        "adalah **interpretasi AI** -- persentil-95 distribusi vNo, kriteria simetris (false positive rate "
        "<=5% utk label MERAH pada senyawa vNo). `[KEPUTUSAN AI -- PENDING REVIEW FARMASI]`\n"
    )

    for name, (t_low, t_high) in candidates.items():
        lines.append(f"## Kandidat {name} (T_low={t_low:.4f}, T_high={t_high:.4f})\n")

        dist = color_distribution(rows, t_low, t_high)
        total = len(rows)
        lines.append("**Distribusi warna (AI-band murni, seluruh katalog):**\n")
        lines.append("| Warna | Jumlah | Persentase |")
        lines.append("|---|---|---|")
        for color in ("HIJAU", "KUNING", "MERAH"):
            lines.append(f"| {color} | {dist[color]} | {dist[color]/total*100:.2f}% |")
        lines.append("")

        per_concern = per_concern_distribution(rows, t_low, t_high)
        lines.append("**Distribusi warna per dili_concern:**\n")
        lines.append("| dili_concern | HIJAU | KUNING | MERAH | n |")
        lines.append("|---|---|---|---|---|")
        for concern, c in sorted(per_concern.items()):
            n = sum(c.values())
            lines.append(f"| {concern} | {c['HIJAU']} ({c['HIJAU']/n*100:.1f}%) | {c['KUNING']} ({c['KUNING']/n*100:.1f}%) | {c['MERAH']} ({c['MERAH']/n*100:.1f}%) | {n} |")
        lines.append("")

        sens, spec, n_eval, n_amb = sensitivity_specificity(rows, t_low)
        lines.append(
            f"**Sensitivity/specificity pada T_low={t_low:.4f}** (biner: positif=vMost+vLess, "
            f"negatif=vNo, {n_amb} senyawa Ambiguous-DILI-concern dikecualikan, n={n_eval}):\n"
        )
        lines.append(f"- Sensitivity (recall vMost+vLess): **{sens*100:.2f}%**")
        lines.append(f"- Specificity (recall vNo): **{spec*100:.2f}%**\n")

        lines.append("**Uji senyawa acuan (pipeline PBPK + exposure + matriks kandidat):**\n")
        for line in reference_compound_tests(rows, t_low, t_high):
            lines.append(f"- {line}")
        lines.append("")

    with open(REPORTS_DIR / "F2_penurunan_ambang.md", "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print("[F2] Laporan disimpan: reports/F2_penurunan_ambang.md")
    for name, (tl, th) in candidates.items():
        print(f"  {name}: T_low={tl:.4f} T_high={th:.4f}")


if __name__ == "__main__":
    main()
