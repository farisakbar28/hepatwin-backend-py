import pandas as pd
import pytest

from hepatwin_ml.data.load_supabase import (
    COLUMNS,
    EXPECTED_SIMULATABLE_COUNT,
    fetch_compounds_snapshot,
    filter_simulatable,
)


def _fake_df(n_true: int, n_false: int) -> pd.DataFrame:
    rows = [
        {c: (True if c == "is_simulatable" else f"v{i}") for c in COLUMNS}
        for i in range(n_true)
    ] + [
        {c: (False if c == "is_simulatable" else f"v{i}") for c in COLUMNS}
        for i in range(n_false)
    ]
    return pd.DataFrame(rows, columns=COLUMNS)


def test_filter_simulatable_returns_only_true_rows_when_count_matches():
    df = _fake_df(n_true=EXPECTED_SIMULATABLE_COUNT, n_false=5)
    result = filter_simulatable(df)
    assert len(result) == EXPECTED_SIMULATABLE_COUNT
    assert result["is_simulatable"].all()


def test_filter_simulatable_hard_stops_on_count_mismatch():
    df = _fake_df(n_true=EXPECTED_SIMULATABLE_COUNT - 1, n_false=5)
    with pytest.raises(AssertionError, match="ekspektasi"):
        filter_simulatable(df)


def test_fetch_compounds_snapshot_uses_cache_without_network(tmp_path):
    cache_path = tmp_path / "compounds_snapshot.parquet"
    expected = _fake_df(n_true=3, n_false=1)
    expected.to_parquet(cache_path, index=False)

    result = fetch_compounds_snapshot(use_cache=True, cache_path=cache_path)

    pd.testing.assert_frame_equal(result, expected)
