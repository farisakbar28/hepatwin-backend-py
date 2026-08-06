import math
import json
from pathlib import Path

import pytest

from app.services import pbpk_calibration
from app.services.exposure_evaluator import ExposureEvaluatorService, ExposureRiskLevel


def test_shape_ratio_and_exposure_index_have_prd_v23_meaning():
    result = ExposureEvaluatorService.evaluate_relative_exposure(cmax=9.0, auc=99.0)

    assert result["shape_ratio_h_inv"] == pytest.approx(9.0 / 99.0)
    assert result["cmax_auc_ratio"] == result["shape_ratio_h_inv"]
    assert result["exposure_index"] == pytest.approx(math.log1p(9.0) + math.log1p(99.0))
    assert result["risk_level"] == ExposureRiskLevel.LOW.value
    assert result["exposure_category_source"] == "INTERNAL_DISTRIBUTIONAL_CALIBRATION"


def test_quantile_boundaries_define_categories(monkeypatch):
    monkeypatch.setattr(pbpk_calibration, "P33_EXPOSURE_INDEX", 0.0)
    monkeypatch.setattr(pbpk_calibration, "P66_EXPOSURE_INDEX", 0.0)
    assert ExposureEvaluatorService.evaluate_relative_exposure(0.0, 0.0)["risk_level"] == "MODERATE_EXPOSURE"

    monkeypatch.setattr(pbpk_calibration, "P33_EXPOSURE_INDEX", 1.0)
    monkeypatch.setattr(pbpk_calibration, "P66_EXPOSURE_INDEX", 2.0)
    assert ExposureEvaluatorService.evaluate_relative_exposure(0.0, 0.0)["risk_level"] == "LOW_EXPOSURE"
    assert ExposureEvaluatorService.evaluate_relative_exposure(10.0, 100.0)["risk_level"] == "HIGH_EXPOSURE"


def test_unfrozen_or_invalid_calibration_fails_explicitly(monkeypatch):
    monkeypatch.setattr(pbpk_calibration, "P33_EXPOSURE_INDEX", None)
    monkeypatch.setattr(pbpk_calibration, "P66_EXPOSURE_INDEX", None)
    with pytest.raises(RuntimeError, match="belum dibekukan"):
        ExposureEvaluatorService.evaluate_relative_exposure(1.0, 1.0)


def test_frozen_runtime_calibration_matches_the_hashed_report():
    report_path = Path(__file__).parents[2] / "reports" / "pbpk_exposure_calibration_v2_3.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert pbpk_calibration.CATALOG_SNAPSHOT_SHA256 == report["catalog_snapshot_sha256"]
    assert pbpk_calibration.CALIBRATION_VERSION == report["version"]
    assert pbpk_calibration.PBPK_CONFIG_SHA256 == report["pbpk_config_sha256"]
    assert pbpk_calibration.runtime_pbpk_config_snapshot() == report["pbpk_config"]
    assert pbpk_calibration.P33_EXPOSURE_INDEX == pytest.approx(report["p33_exposure_index"])
    assert pbpk_calibration.P66_EXPOSURE_INDEX == pytest.approx(report["p66_exposure_index"])
    pbpk_calibration.ensure_runtime_config_matches_calibration()


def test_runtime_configuration_drift_is_rejected(monkeypatch):
    monkeypatch.setattr(pbpk_calibration, "PBPK_CONFIG_SHA256", "invalid")
    with pytest.raises(RuntimeError, match="runtime configuration"):
        ExposureEvaluatorService.evaluate_relative_exposure(1.0, 1.0)


def test_sweep_runtime_writer_preserves_calibration_guard(tmp_path):
    from scripts.run_sweep_histogram import _write_runtime_calibration

    source_path = Path(__file__).parents[2] / "app" / "services" / "pbpk_calibration.py"
    generated_path = tmp_path / "pbpk_calibration.py"
    generated_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")

    _write_runtime_calibration(generated_path, 1.25, 2.5, "catalog-hash", "config-hash", "2026-08-06T00:00:00+00:00")
    generated = generated_path.read_text(encoding="utf-8")

    assert "def ensure_runtime_config_matches_calibration" in generated
    assert "CATALOG_SNAPSHOT_SHA256 = 'catalog-hash'" in generated
    assert "PBPK_CONFIG_SHA256 = 'config-hash'" in generated
    assert "P33_EXPOSURE_INDEX = 1.25" in generated
    assert "P66_EXPOSURE_INDEX = 2.5" in generated


@pytest.mark.parametrize("cmax,auc", [(math.nan, 1.0), (1.0, math.inf), (-1.0, 1.0)])
def test_invalid_exposure_inputs_are_rejected(cmax, auc):
    with pytest.raises(ValueError, match="finite"):
        ExposureEvaluatorService.evaluate_relative_exposure(cmax, auc)
