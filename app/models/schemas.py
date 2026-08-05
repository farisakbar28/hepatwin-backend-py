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

# --- DTO Request & Response Simulasi PRD v2.0 ---

class PatientCovariates(BaseModel):
    usia: int = Field(..., ge=1, le=120, description="Usia pasien dalam tahun")
    jenis_kelamin: Literal["L", "P"] = Field(..., description="Jenis kelamin pasien (L = Laki-laki, P = Perempuan)")
    berat_badan_kg: float = Field(..., ge=1.0, le=350.0, description="Berat badan pasien dalam kg")
    tinggi_badan_cm: float = Field(..., ge=30.0, le=250.0, description="Tinggi badan pasien dalam cm")

class SimulationRequest(BaseModel):
    hepatwin_id: str = Field(..., description="Identifier senyawa dari autocomplete database tertutup")
    dosis_mg: float = Field(..., gt=0.0, description="Dosis bolus obat dalam satuan mg")
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
    explainability_shap: List[str] = Field(..., description="Highlight gugus fungsi toxicophore kontributor DILI")
    cmax_hati: float = Field(..., description="Konsentrasi puncak obat di hati (mg/L)")
    auc_hati: float = Field(..., description="Area Under Curve konsentrasi obat di hati")
    time_series_pbpk: List[TimeSeriesPBPKPoint] = Field(..., description="Kurva konsentrasi C_hati(t) & C_plasma(t) 24 jam")
    disclaimer_permanent: str = Field(..., description="Medical Disclaimer resmi HepaTwin (ASME V&V 40)")
