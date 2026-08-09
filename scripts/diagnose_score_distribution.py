"""F1 -- Diagnostik distribusi `dili_score` atas seluruh katalog senyawa
`is_simulatable = TRUE`. Fondasi data untuk penurunan ambang T_low/T_high (F2).

Latar belakang (temuan SS3.1, lihat reports/F9_limitations_fusion.md §1): kalibrator produksi
(`calibrator_gatnn_dnn.pkl`, Platt scaling pada probabilitas) mengunci rentang
keluaran `dili_score` ke [~0.4337, ~0.7747] -- jauh di atas ambang hijau lama
(< 0.30). Skrip ini MENGUKUR rentang nyata via eksekusi, bukan mengandalkan
angka yang dikutip di dokumen.

Catatan privilese DB (relevan untuk instruksi "gunakan SUPABASE_ANON_KEY,
bukan service role key" di F1 langkah 1): repo ini
TIDAK memiliki jalur akses DB yang dibedakan oleh anon-key vs service-role key
-- `CompoundRepository` (dipakai ulang di sini) selalu terhubung lewat
`DATABASE_URL`, yaitu koneksi Postgres pooler Supabase langsung dengan role
`postgres.<project>` (bukan role `anon` PostgREST, dan tidak melalui
`SUPABASE_ANON_KEY`/`SUPABASE_SERVICE_ROLE_KEY` sama sekali -- kedua key itu
hanya relevan untuk klien Supabase REST/JS, yang di `app/core/database.py`
malah sudah dikonfigurasi dengan SERVICE_ROLE_KEY, bukan anon key). Karena itu
instruksi tersebut tidak bisa dipenuhi secara literal tanpa membangun jalur
DB terpisah di luar `CompoundRepository` -- yang berarti melanggar instruksi
"pakai ulang CompoundRepository" di baris yang sama. Mitigasi yang diambil:
skrip ini HANYA melakukan SELECT baca-saja (tidak ada INSERT/UPDATE/DELETE),
sehingga blast radius penggunaan koneksi berprivilese tinggi tetap terbatas
pada risiko baca, sama seperti seluruh endpoint produksi lain yang memakai
repository yang sama. Temuan ini dicatat apa adanya untuk ditinjau Ketua
Tim/Vedo (kontrak data), bukan disembunyikan.

Jalankan dari root repo:
    .venv/Scripts/python.exe scripts/diagnose_score_distribution.py
"""
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.repositories.compound_repository import CompoundRepository  # noqa: E402
from app.services.ai_engine import HybridAIEngine  # noqa: E402

REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

PERCENTILES = [1, 5, 10, 25, 33, 50, 67, 75, 90, 95, 99]
OLD_GREEN_MAX = 0.30
OLD_RED_MIN = 0.70


def _color_old(score: float) -> str:
    if score < OLD_GREEN_MAX:
        return "HIJAU"
    if score > OLD_RED_MIN:
        return "MERAH"
    return "KUNING"


def main() -> None:
    snapshot_at = datetime.now(timezone.utc).isoformat()
    print(f"[F1] snapshot_at = {snapshot_at}")

    db = SessionLocal()
    try:
        repo = CompoundRepository(db)
        compounds = repo.get_all_simulatable()
    finally:
        db.close()

    print(f"[F1] {len(compounds)} senyawa is_simulatable=TRUE dimuat dari Supabase.")

    engine = HybridAIEngine(model_path=settings.AI_MODEL_PATH)
    if not engine.ready:
        print("[F1] FATAL: HybridAIEngine tidak siap (model gagal dimuat). Berhenti.")
        sys.exit(1)

    rows: list[dict] = []
    failures: list[dict] = []

    t0 = time.perf_counter()
    for c in compounds:
        smiles = c.canonical_smiles or c.isomeric_smiles
        try:
            score = engine.predict_dili_risk(smiles)
            rows.append(
                {
                    "hepatwin_id": c.hepatwin_id,
                    "compound_name": c.compound_name,
                    "dili_concern": c.dili_concern or "Unknown",
                    "dili_score": score,
                    "snapshot_at": snapshot_at,
                }
            )
        except Exception as exc:  # noqa: BLE001 -- dicatat, TIDAK dibuang diam-diam
            failures.append(
                {
                    "hepatwin_id": c.hepatwin_id,
                    "compound_name": c.compound_name,
                    "smiles": smiles,
                    "error": str(exc),
                }
            )
    total_s = time.perf_counter() - t0
    per_compound_ms = (total_s / len(compounds) * 1000) if compounds else 0.0

    print(
        f"[F1] {len(rows)} skor berhasil, {len(failures)} gagal, "
        f"total {total_s:.2f}s ({per_compound_ms:.2f} ms/senyawa)"
    )
    if failures:
        print("[F1] SENYAWA GAGAL (dicatat, TIDAK dibuang diam-diam):")
        for f in failures:
            print(f"   - {f['hepatwin_id']} ({f['compound_name']}): {f['error']}")

    scores = np.array([r["dili_score"] for r in rows], dtype=float)

    # -- Simpan CSV mentah (dipakai ulang F2 & F8) --
    csv_path = REPORTS_DIR / "F1_scores_catalogue.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(
            fp, fieldnames=["hepatwin_id", "compound_name", "dili_concern", "dili_score", "snapshot_at"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"[F1] CSV disimpan: {csv_path}")

    # -- Statistik global --
    stats = {"min": float(np.min(scores)), "max": float(np.max(scores)), "median": float(np.median(scores))}
    for p in PERCENTILES:
        stats[f"p{p}"] = float(np.percentile(scores, p))

    n_below_030 = int(np.sum(scores < 0.30))
    n_green_old = int(np.sum(scores < OLD_GREEN_MAX))
    n_red_old = int(np.sum(scores > OLD_RED_MIN))
    n_yellow_old = len(scores) - n_green_old - n_red_old

    concern_groups: dict[str, list[float]] = {}
    for r in rows:
        concern_groups.setdefault(r["dili_concern"], []).append(r["dili_score"])

    # -- Tulis laporan markdown --
    md_path = REPORTS_DIR / "F1_diagnostik_distribusi.md"
    lines: list[str] = []
    lines.append("# F1 -- Diagnostik Distribusi Skor Katalog\n")
    lines.append(f"**snapshot_at:** {snapshot_at}  ")
    lines.append(f"**Total senyawa is_simulatable=TRUE:** {len(compounds)}  ")
    lines.append(f"**Skor berhasil:** {len(rows)}  |  **Gagal:** {len(failures)}  ")
    lines.append(f"**Waktu total inferensi (1231x forward pass, sekuensial):** {total_s:.2f} detik ({per_compound_ms:.2f} ms/senyawa rata-rata)\n")

    if failures:
        lines.append("## Senyawa gagal diberi skor\n")
        lines.append("| hepatwin_id | compound_name | smiles | error |")
        lines.append("|---|---|---|---|")
        for f in failures:
            lines.append(f"| {f['hepatwin_id']} | {f['compound_name']} | `{f['smiles']}` | {f['error']} |")
        lines.append("")

    lines.append("## Statistik global dili_score (n={})\n".format(len(rows)))
    lines.append("| Statistik | Nilai |")
    lines.append("|---|---|")
    lines.append(f"| min | {stats['min']:.4f} |")
    for p in PERCENTILES:
        lines.append(f"| p{p} | {stats[f'p{p}']:.4f} |")
    lines.append(f"| median (p50) | {stats['median']:.4f} |")
    lines.append(f"| max | {stats['max']:.4f} |")
    lines.append("")

    lines.append("## Verifikasi temuan SS3.1\n")
    lines.append(f"- Batas bawah aktual terukur: **{stats['min']:.4f}** (ekspektasi dokumen: ~0.4337)")
    lines.append(f"- Batas atas aktual terukur: **{stats['max']:.4f}** (ekspektasi dokumen: ~0.7747)")
    lines.append(f"- Jumlah senyawa dengan dili_score < 0.30: **{n_below_030}** (ekspektasi: 0)")
    if n_below_030 > 0:
        lines.append(
            "  - \U0001F6A9 **TEMUAN BERUBAH** -- ada senyawa di bawah 0.30. "
            "Asumsi dasar SS3.1 perlu ditinjau ulang sebelum F2 dilanjutkan."
        )
    lines.append("")

    lines.append("## Distribusi warna dengan ambang LAMA (0.30 / 0.70), murni dari dili_score\n")
    lines.append("| Warna | Jumlah | Persentase |")
    lines.append("|---|---|---|")
    lines.append(f"| HIJAU (< 0.30) | {n_green_old} | {n_green_old/len(scores)*100:.2f}% |")
    lines.append(f"| KUNING (0.30-0.70) | {n_yellow_old} | {n_yellow_old/len(scores)*100:.2f}% |")
    lines.append(f"| MERAH (> 0.70) | {n_red_old} | {n_red_old/len(scores)*100:.2f}% |")
    lines.append("")

    lines.append("## Distribusi per dili_concern\n")
    lines.append("| dili_concern | n | min | p25 | median | p75 | max |")
    lines.append("|---|---|---|---|---|---|---|")
    for concern, vals in sorted(concern_groups.items()):
        arr = np.array(vals, dtype=float)
        lines.append(
            f"| {concern} | {len(arr)} | {arr.min():.4f} | {np.percentile(arr,25):.4f} | "
            f"{np.median(arr):.4f} | {np.percentile(arr,75):.4f} | {arr.max():.4f} |"
        )
    lines.append("")

    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print(f"[F1] Laporan markdown disimpan: {md_path}")


if __name__ == "__main__":
    main()
