"""Utilitas bersama untuk skrip pipeline ml/ (path repo, laporan).

Menyisipkan root repo ke sys.path supaya skrip di ml/scripts/ bisa
`from app.chem... import ...` — menegakkan aturan sumber tunggal featurizer
(AGENTS.md §4): pipeline mengimpor dari app/, tidak menyalin.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATA_RAW = REPO_ROOT / "ml" / "data" / "raw"
DATA_INTERIM = REPO_ROOT / "ml" / "data" / "interim"
DATA_PROCESSED = REPO_ROOT / "ml" / "data" / "processed"
REPORTS = REPO_ROOT / "ml" / "reports"


def write_report(name: str, lines: list[str]) -> Path:
    """Tulis laporan markdown ke ml/reports/<name>. Kembalikan path-nya."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
