import math

import pytest

from app.services.allometric_service import AllometricService


def test_prd_v23_volumes_and_flows_for_70kg_adult():
    params = AllometricService.calculate_physiological_parameters(40, "L", 70.0, 168.0, xlogp=0.0)

    assert params["V_P"] == pytest.approx(3.01)
    assert params["V_L"] == pytest.approx(1.799)
    assert params["V_K"] == pytest.approx(0.308)
    assert params["V_R"] == pytest.approx(64.883)
    assert params["Q_C"] == pytest.approx(360.0)
    assert params["Q_L"] == pytest.approx(90.0)
    assert params["Q_K"] == pytest.approx(72.0)
    assert params["Q_R"] == pytest.approx(198.0)


def test_age_factor_is_capped_at_90_with_floor_point_six():
    params_40 = AllometricService.calculate_physiological_parameters(40, "L", 70.0, 170.0)
    params_80 = AllometricService.calculate_physiological_parameters(80, "L", 70.0, 170.0)
    params_90 = AllometricService.calculate_physiological_parameters(90, "L", 70.0, 170.0)
    params_100 = AllometricService.calculate_physiological_parameters(100, "L", 70.0, 170.0)

    assert params_40["age_factor"] == pytest.approx(1.0)
    assert params_80["age_factor"] == pytest.approx(0.68)
    assert params_90["age_factor"] == pytest.approx(0.60)
    assert params_100["age_factor"] == pytest.approx(0.60)


def test_body_fat_uses_child_and_adult_deurenberg_branches():
    child = AllometricService.calculate_physiological_parameters(15, "L", 10.0, 100.0)
    adult = AllometricService.calculate_physiological_parameters(16, "L", 70.0, 175.0)

    assert child["body_fat_percent_raw"] == pytest.approx(2.4)
    assert child["body_fat_percent_clamped"] == pytest.approx(3.0)
    expected_adult = 1.20 * (70.0 / 1.75**2) + 0.23 * 16 - 10.8 - 5.4
    assert adult["body_fat_percent_raw"] == pytest.approx(expected_adult)


def test_body_fat_upper_clamp_and_warning(caplog):
    params = AllometricService.calculate_physiological_parameters(100, "P", 350.0, 100.0)

    assert params["body_fat_percent_raw"] > 60.0
    assert params["body_fat_percent_clamped"] == 60.0
    assert "PBPK BODY_FAT CLAMP" in caplog.text


def test_bmi_is_flag_only_and_never_penalizes_clearance():
    normal = AllometricService.calculate_physiological_parameters(30, "L", 70.0, 175.0)
    obese = AllometricService.calculate_physiological_parameters(30, "L", 70.0, 150.0)

    assert normal["metabolic_risk_flag"] is False
    assert obese["metabolic_risk_flag"] is True
    assert normal["clearance_multiplier_from_bmi"] == obese["clearance_multiplier_from_bmi"] == 1.0
    assert normal["Cl_metabolism"] == pytest.approx(obese["Cl_metabolism"])


def test_clearance_fallback_is_allometric_and_limited_by_flow():
    params = AllometricService.calculate_physiological_parameters(
        40, "L", 70.0, 170.0, base_cl_metabolism_l_hr=10_000.0
    )
    assert params["Cl_metabolism"] == pytest.approx(0.95 * params["Q_L"])
    assert params["Cl_renal"] == pytest.approx(2.0)
    assert params["Cl_renal_source"] == "DESIGN_FALLBACK_BASE_CL_RENAL_70"


@pytest.mark.parametrize("xlogp", [None, -2.0, -1.0, 0.0, 7.0, 100.0])
def test_kp_r_null_negative_and_extreme_values_are_controlled(xlogp):
    params = AllometricService.calculate_physiological_parameters(30, "L", 70.0, 175.0, xlogp=xlogp)
    assert -1.0 <= params["xlogp_eff"] <= 7.0
    assert 1.0 <= params["K_P_R"] <= 10.0


def test_nonfinite_xlogp_and_invalid_covariates_are_rejected():
    with pytest.raises(ValueError, match="XLogP"):
        AllometricService.calculate_physiological_parameters(30, "L", 70.0, 175.0, xlogp=math.nan)
    with pytest.raises(ValueError, match="Usia"):
        AllometricService.calculate_physiological_parameters(-1, "L", 70.0, 175.0)
    with pytest.raises(ValueError, match="finite"):
        AllometricService.calculate_physiological_parameters(30, "L", math.inf, 175.0)
