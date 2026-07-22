"""01 — Sediakan dataset mentah + laporan + pengingat lisensi.

Dasar: PRD §7, §8.4 · PRD §13 item #3 · EXECUTION_PLAN.md T1.1.

Skrip ini TIDAK menghardcode URL (menghindari tebakan sumber). Ia menerima
lokasi dataset lewat argumen — path lokal atau URL — lalu menaruhnya di
ml/data/raw/, mencatat jumlah baris, dan mengingatkan pencatatan lisensi.

JANGAN mengunduh/memakai NCTR (PRD §8.4 — sumber historis DILIrank, risiko leakage).

Contoh (file lokal yang kamu temukan):
    python ml/scripts/01_download.py --dilirank-src "C:/unduhan/dilirank.xlsx"
    python ml/scripts/01_download.py --xu-src "C:/unduhan/xu2015.csv"
"""
import argparse
import logging
import shutil
from pathlib import Path

from _common import DATA_RAW, REPO_ROOT, write_report  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _place(src: str, dest: Path) -> bool:
    """Salin/unduh src → dest. Idempoten: lewati bila dest sudah ada."""
    if dest.exists():
        logger.info("Sudah ada, dilewati: %s", dest)
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.lower().startswith(("http://", "https://")):
        import requests  # impor lokal — hanya perlu bila mengunduh

        logger.info("Mengunduh %s → %s", src, dest)
        resp = requests.get(src, timeout=120)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
    else:
        logger.info("Menyalin %s → %s", src, dest)
        shutil.copy2(src, dest)
    return dest.exists()


def _count_rows(path: Path) -> str:
    try:
        import pandas as pd

        if path.suffix.lower() in {".xlsx", ".xls"}:
            return str(len(pd.read_excel(path)))
        return str(len(pd.read_csv(path)))
    except Exception as exc:  # noqa: BLE001
        return f"tidak terbaca ({exc})"


def main() -> None:
    ap = argparse.ArgumentParser(description="Sediakan dataset mentah ke ml/data/raw/")
    ap.add_argument("--dilirank-src", default=None, help="path/URL DILIrank")
    ap.add_argument("--dilirank-name", default="dilirank.xlsx")
    ap.add_argument("--xu-src", default=None, help="path/URL Xu et al. 2015")
    ap.add_argument("--xu-name", default="xu2015.csv")
    args = ap.parse_args()

    if not args.dilirank_src and not args.xu_src:
        raise SystemExit("Beri minimal satu: --dilirank-src atau --xu-src")

    placed = []
    if args.dilirank_src:
        dest = DATA_RAW / args.dilirank_name
        if _place(args.dilirank_src, dest):
            placed.append(("DILIrank (training)", dest))
    if args.xu_src:
        dest = DATA_RAW / args.xu_name
        if _place(args.xu_src, dest):
            placed.append(("Xu et al. 2015 (external test)", dest))

    lines = [
        "# 01 Download / Penyediaan Dataset Mentah",
        "",
        "| Dataset | File | Baris |",
        "|---|---|---|",
        *(
            f"| {label} | `{path.relative_to(REPO_ROOT)}` | {_count_rows(path)} |"
            for label, path in placed
        ),
        "",
        "## WAJIB ditindaklanjuti (PRD §13 item #3)",
        "",
        "- [ ] Catat lisensi/ketentuan penggunaan KEDUA dataset di `NOTICE.md`.",
        "- [ ] Pastikan BUKAN dataset NCTR (dikecualikan PRD §8.4).",
        "- [ ] Catat sumber URL + tanggal akses di `docs/DATA_PROVENANCE.md`.",
    ]
    write_report("01_download.md", lines)
    for label, path in placed:
        logger.info("%s → %s", label, path)


if __name__ == "__main__":
    main()
