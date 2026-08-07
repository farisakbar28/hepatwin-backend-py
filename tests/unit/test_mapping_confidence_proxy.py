"""R6 -- Proksi mapping_confidence dari livertox_match_method (gerbang G3).
Kolom mapping_confidence yang diminta PRD v2.3 SS8.3.1 belum ada di database
(kurasi Farmasi berjalan paralel) -- proksi ini murni turunan aplikasi,
ditandai eksplisit lewat mapping_confidence_source, BUKAN kolom kurasi asli.
"""
import pytest

from app.services.simulation_orchestrator import MAPPING_CONFIDENCE_PROXY

CASES = [
    ("exact_name", "high"),
    ("salt_ester_normalized", "medium"),
    ("leading_salt_normalized", "medium"),
    ("spelling_variant_normalized", "medium"),
    ("no_match", "none"),
]


@pytest.mark.parametrize("livertox_match_method,expected", CASES, ids=[c[0] for c in CASES])
def test_mapping_confidence_proxy_five_values(livertox_match_method, expected):
    assert MAPPING_CONFIDENCE_PROXY[livertox_match_method] == expected


def test_mapping_confidence_proxy_covers_exactly_five_methods():
    assert len(MAPPING_CONFIDENCE_PROXY) == 5


def test_unknown_or_null_livertox_match_method_defaults_to_none():
    # .get(x, "none") -- perilaku yang dipakai orchestrator utk None/nilai baru tak dikenal
    assert MAPPING_CONFIDENCE_PROXY.get(None, "none") == "none"
    assert MAPPING_CONFIDENCE_PROXY.get("some_future_method", "none") == "none"
