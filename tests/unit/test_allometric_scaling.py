import pytest
from app.services.allometric_service import AllometricService

def test_liver_volume_brown_1997():
    params_70 = AllometricService.calculate_physiological_parameters(30, "L", 70.0, 175.0)
    assert params_70["V_L"] == 1.75
    
    params_60 = AllometricService.calculate_physiological_parameters(30, "L", 60.0, 175.0)
    assert params_60["V_L"] == 1.50

def test_body_fat_deurenberg_1991():
    params_male = AllometricService.calculate_physiological_parameters(30, "MALE", 70.0, 175.0)
    params_female = AllometricService.calculate_physiological_parameters(30, "FEMALE", 70.0, 175.0)
    
    assert params_female["body_fat_pct"] - params_male["body_fat_pct"] == 10.8

def test_hepatic_blood_flow_age_reduction_soejima_2022():
    params_25 = AllometricService.calculate_physiological_parameters(25, "L", 70.0, 175.0)
    params_65 = AllometricService.calculate_physiological_parameters(65, "L", 70.0, 175.0)
    
    assert round(params_65["Q_L"], 2) == round(params_25["Q_L"] * 0.8, 2)

def test_masld_obesity_clearance_reduction_ghabril_2025():
    params_normal = AllometricService.calculate_physiological_parameters(30, "L", 70.0, 170.7)
    assert params_normal["bmi"] < 30.0
    
    params_obese = AllometricService.calculate_physiological_parameters(30, "L", 70.0, 150.0)
    assert params_obese["bmi"] >= 30.0
    assert round(params_obese["Cl_metabolism"], 2) == round(params_normal["Cl_metabolism"] * 0.8, 2)

def test_no_negative_or_zero_volumes():
    import random
    for _ in range(100):
        age = random.randint(0, 100)
        weight = random.uniform(10.0, 250.0)
        height = random.uniform(50.0, 220.0)
        gender = random.choice(["MALE", "FEMALE", "L", "P"])
        
        params = AllometricService.calculate_physiological_parameters(age, gender, weight, height)
        
        assert params["V_P"] > 0
        assert params["V_L"] > 0
        assert params["V_K"] > 0
        assert params["V_R"] > 0
        assert params["Q_L"] > 0
        assert params["Cl_metabolism"] > 0

def test_invalid_physical_parameters_raise_error():
    with pytest.raises(ValueError, match="Parameter berat dan tinggi badan harus lebih besar dari 0."):
        AllometricService.calculate_physiological_parameters(30, "MALE", -5.0, 175.0)
        
    with pytest.raises(ValueError, match="Parameter berat dan tinggi badan harus lebih besar dari 0."):
        AllometricService.calculate_physiological_parameters(30, "MALE", 70.0, 0.0)

def test_invalid_gender_raises_error():
    with pytest.raises(ValueError, match="Format jenis kelamin tidak valid."):
        AllometricService.calculate_physiological_parameters(30, "HACKER", 70.0, 175.0)

def test_premature_baby_body_fat_is_zero():
    params = AllometricService.calculate_physiological_parameters(0, "M", 2.0, 45.0)
    assert params["body_fat_pct"] == 0.0
