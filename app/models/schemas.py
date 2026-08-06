from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal

# --- DTO Autocomplete & Lookup Senyawa ---

class CompoundItem(BaseModel):
    hepatwin_id: str = Field(..., description="ID unik senyawa pada database Hepatwin")
    compound_name: str = Field(..., description="Nama INN / umum senyawa")
    dili_concern: Optional[str] = Field(None, description="Kategori DILI (Most-DILI-Concern, Less-DILI-Concern, No-DILI-Concern)")
    is_simulatable: bool = Field(True, description="Status apakah senyawa dapat disimulasikan (is_simulatable = TRUE)")

class CompoundDetail(CompoundItem):
    ltkb_id: Optional[str] = Field(None)
    cid: Optional[int] = Field(None)
    canonical_smiles: Optional[str] = Field(None)
    isomeric_smiles: Optional[str] = Field(None)
    inchikey: Optional[str] = Field(None)
    molecular_formula: Optional[str] = Field(None)
    molecular_weight: Optional[float] = Field(None)
    tpsa: Optional[float] = Field(None)
    xlogp: Optional[float] = Field(None)


    injury_pattern: Optional[str] = Field(None)
    segment_list: Optional[str] = Field(None)
    hotspot_base_intensity: Optional[str] = Field(None)

class AutocompleteResponse(BaseModel):
    query: str
    total: int
    results: List[CompoundItem]

# --- DTO Request & Response Simulasi PBPK PRD v2.3 ---

class PatientCovariates(BaseModel):
    usia: int = Field(..., ge=0, le=100, description="Usia pasien dalam tahun (0-100)")
    jenis_kelamin: Literal["L", "P"] = Field(..., description="Jenis kelamin pasien (L = Laki-laki, P = Perempuan)")
    berat_badan_kg: float = Field(..., ge=1.0, le=350.0, allow_inf_nan=False, description="Berat badan pasien dalam kg")
    tinggi_badan_cm: float = Field(..., ge=30.0, le=250.0, allow_inf_nan=False, description="Tinggi badan pasien dalam cm")

class SimulationRequest(BaseModel):
    hepatwin_id: str = Field(..., description="Identifier senyawa dari autocomplete database tertutup")
    dosis_mg: float = Field(..., gt=0.0, allow_inf_nan=False, description="Dosis bolus obat dalam satuan mg")
    covariates: PatientCovariates = Field(..., description="4 Kovariat fisik pasien untuk penskalaan alometrik")

class TimeSeriesPBPKPoint(BaseModel):
    time: float = Field(..., description="Waktu simulasi (jam)")
    c_plasma: float = Field(..., description="Konsentrasi plasma (mg/L)")
    c_hati: float = Field(..., description="Konsentrasi hati (mg/L)")

class SimulationResponse(BaseModel):
    hepatwin_id: str = Field(..., description="Identifier senyawa")
    compound_name: str = Field(..., description="Nama resmi senyawa (INN)")
    dili_score: float = Field(..., ge=0.0, le=1.0, description="Probabilitas DILI dari GATNN-DNN")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Tingkat risiko: low, medium, high")
    visual_color: Literal["green", "yellow", "red"] = Field(..., description="Warna hotspot 3D WebGL")
    blinking_speed: Literal["none", "slow", "fast"] = Field(..., description="Kecepatan kedip hotspot WebGL")
    affected_segments: List[str] = Field(..., description="Daftar Segmen Couinaud terdampak (contoh: ['V', 'VI', 'VII', 'VIII'])")
    injury_pattern: str = Field(..., description="Pola cedera: Hepatocellular, Cholestatic, Mixed, atau Fallback/Diffuse")
    segment_mapping_type: Literal["PEDAGOGICAL_HEURISTIC"] = Field(
        ..., description="Mapping segmen adalah heuristik pedagogis, bukan lokalisasi klinis."
    )
    segment_mapping_not_clinical_localization: Literal[True] = Field(
        ..., description="Menegaskan mapping segmen bukan lokalisasi histologis klinis."
    )
    explainability_shap: List[str] = Field(..., description="Highlight gugus fungsi toxicophore kontributor DILI")
    cmax_hati: float = Field(..., description="Konsentrasi puncak obat di hati (mg/L)")
    auc_hati: float = Field(..., description="Area Under Curve konsentrasi obat di hati")
    cmax_auc_ratio: float = Field(..., description="Alias backward-compatible untuk shape_ratio_h_inv (h^-1), bukan magnitude exposure")
    shape_ratio_h_inv: float = Field(..., description="Rasio bentuk kurva Cmax/AUC dalam h^-1")
    exposure_index: float = Field(..., description="log1p(Cmax hati) + log1p(AUC hati)")
    exposure_category: Literal["LOW_EXPOSURE", "MODERATE_EXPOSURE", "HIGH_EXPOSURE"]
    exposure_category_source: Literal["INTERNAL_DISTRIBUTIONAL_CALIBRATION"]
    exposure_calibration_version: str
    time_series_pbpk: List[TimeSeriesPBPKPoint] = Field(..., description="Kurva konsentrasi C_hati(t) & C_plasma(t) 24 jam")
    disclaimer_permanent: str = Field(..., description="Medical Disclaimer resmi HepaTwin (ASME V&V 40)")


class PBPKDebugResponse(BaseModel):
    BMI: float
    metabolic_risk_flag: bool
    clearance_multiplier_from_bmi: float
    V_P_L: float
    V_L_L: float
    V_K_L: float
    V_R_L: float
    Q_C_L_h: float
    Q_L_L_h: float
    Q_K_L_h: float
    Q_R_L_h: float
    body_fat_percent_raw: float
    body_fat_percent_clamped: float
    xlogp_eff: float
    Kp_R: float
    Cl_met_L_h: float
    Cl_renal_L_h: float
    cmax_liver_mg_l: float
    auc_liver_mg_h_l: float
    cmax_auc_ratio: float
    shape_ratio_h_inv: float
    exposure_index: float
    exposure_category: Literal["LOW_EXPOSURE", "MODERATE_EXPOSURE", "HIGH_EXPOSURE"]
    exposure_category_source: Literal["INTERNAL_DISTRIBUTIONAL_CALIBRATION"]
    exposure_calibration_version: str
