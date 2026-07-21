from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal

class SimulationRequest(BaseModel):
    mode: Literal["edukasi_mendalam", "triase_umum"] = Field(
        ..., 
        description="Jalur komputasi simulasi: 'edukasi_mendalam' atau 'triase_umum'.", 
        json_schema_extra={"example": "edukasi_mendalam"}
    )
    compound_id: Optional[Literal["paracetamol", "amox_clav"]] = Field(
        None, 
        description="Identifier senyawa ('paracetamol' atau 'amox_clav'). Dipakai mode edukasi_mendalam.", 
        json_schema_extra={"example": "paracetamol"}
    )
    dose_mg_kg: Optional[float] = Field(
        None, 
        ge=0.0,
        description="Dosis obat dalam mg/kg.", 
        json_schema_extra={"example": 15.0}
    )
    smiles_string: Optional[str] = Field(
        None,
        min_length=1, 
        description="Representasi struktur kimia (SMILES). Dipakai mode triase_umum.", 
        json_schema_extra={"example": "CC(=O)NC1=CC=C(O)C=C1"}
    )

class SimulationResponse(BaseModel):
    mode: str = Field(..., description="Jalur komputasi yang dieksekusi.")
    compound_name: Optional[str] = Field(None, description="Nama senyawa (jika tersedia).")
    input_smiles: Optional[str] = Field(None, description="Notasi SMILES.")
    dose_mg_kg: Optional[float] = Field(None, description="Dosis yang digunakan (mg/kg).")
    DILI_score: float = Field(..., ge=0.0, le=1.0, description="Skor probabilitas risiko DILI.")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Tingkat risiko berdasarkan skor DILI.")
    damage_severity: float = Field(..., ge=0.0, le=1.0, description="Tingkat keparahan visual (0-1).")
    compound_class: Literal["dose_dependent", "idiosyncratic", "unknown_general"] = Field(..., description="Pola mekanisme: dose_dependent, idiosyncratic, unknown_general.")
    model_confidence_note: str = Field(..., description="Teks batas klaim general.")
    disclaimer_permanent: Optional[str] = Field(None, description="Disclaimer WAJIB untuk triase umum.")
    disclaimer_hideable: bool = Field(..., description="Apakah disclaimer dapat disembunyikan oleh pengguna.")
    affected_zone: Optional[str] = Field(None, description="Lokasi spesifik anatomis.")
    supports_micro_zoom: bool = Field(..., description="Menandakan apakah senyawa mendukung zoom mikroskopis.")
    explainability: List[str] = Field(..., description="Daftar gugus fungsi kimia/farmakologis.")
    visual_pattern: str = Field(..., description="Pola visual 3D.")
    time_series_pkpd: Optional[List[Dict[str, Any]]] = Field(None, description="Data plot grafik NAPQI/GSH.")
    nomogram_data: Optional[List[Dict[str, Any]]] = Field(None, description="Data plot klinis Rumack-Matthew.")