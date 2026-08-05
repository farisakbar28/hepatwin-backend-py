"""C8 -- test laporan benchmark/kelayakan kimiawi (butuh ml/reports/C8_shap.md
dari ml/scripts/run_explain_report.py, di-skip otomatis bila belum dijalankan)."""
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = _REPO_ROOT / "ml" / "reports" / "C8_shap.md"

pytestmark = pytest.mark.skipif(
    not REPORT_PATH.exists(),
    reason="Jalankan ml/scripts/run_explain_report.py dulu",
)


@pytest.fixture(scope="module")
def report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def test_report_declares_masking_not_shap(report_text):
    assert "masking_attribution" in report_text
    assert '"SHAP"' in report_text  # disebut eksplisit sebagai kontras, bukan diklaim jadi method


def test_report_includes_both_test_compounds(report_text):
    assert "Parasetamol" in report_text
    assert "Ibuprofen" in report_text


def test_report_includes_latency_benchmark_section(report_text):
    assert "p95" in report_text
    assert "LULUS" in report_text or "GAGAL" in report_text


def test_report_mentions_g4_pending_review(report_text):
    assert "G4" in report_text
    assert "PENDING REVIEW FARMASI" in report_text
