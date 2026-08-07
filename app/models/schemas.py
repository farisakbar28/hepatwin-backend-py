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

class FusionThresholds(BaseModel):
    t_low: float = Field(..., description="Ambang dili_score band AI_LOW/AI_MID (F2, gerbang K2)")
    t_high: float = Field(..., description="Ambang dili_score band AI_MID/AI_HIGH (F2, gerbang K2)")

class SimulationResponse(BaseModel):
    hepatwin_id: str = Field(..., description="Identifier senyawa")
    compound_name: str = Field(..., description="Nama resmi senyawa (INN)")
    dili_score: float = Field(..., ge=0.0, le=1.0, description="Probabilitas DILI dari GATNN-DNN")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Tingkat risiko: low, medium, high (enum teknis utk logika, TIDAK diubah -- lihat risk_label_id utk teks tampilan)")
    # --- R7 (gerbang G5, PRD v2.3 SS8.3.3): "Aman/Berbahaya/Kritis" tidak boleh
    # berdiri sendiri -- label siap-tampil wajib disediakan backend, bukan
    # diterjemahkan sendiri oleh frontend dari risk_level.
    risk_label_id: Literal["Prioritas rendah (in-silico)", "Prioritas sedang (in-silico)", "Prioritas tinggi (in-silico)"] = Field(
        ..., description="Label siap-tampil sesuai PRD v2.3 SS8.3.3 -- gunakan ini di UI, JANGAN terjemahkan risk_level sendiri"
    )
    risk_label_disclaimer: str = Field(
        ...,
        description="Disclaimer wajib menyertai risk_label_id -- warna/label bukan keputusan terapi",
    )
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
    # --- F4 (PROJECT_FUSION.md SS4.3): intensitas & mode hotspot dari lookup DB,
    # TERPISAH dari warna/kedip (yang murni hasil fusi AI+PBPK). "dim" berarti
    # bukti lokasi lemah, BUKAN risiko rendah -- lihat evidence_note.
    hotspot_intensity: str = Field(..., description="Intensitas visual hotspot dari monograf LiverTox: high, low, atau dim")
    hotspot_display_mode: str = Field(..., description="Mode tampilan hotspot: focal (segmen spesifik) atau diffuse (seluruh 8 segmen)")
    evidence_note: Optional[str] = Field(
        None,
        description="Catatan netral bila pola cedera spesifik tidak tersedia di data kurasi (fallback difus redup); null bila ada monograf spesifik",
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

    # --- R5 (gerbang G1/G2, PROJECT_FUSION_V23.md SS3.2): dua sinyal PRD v2.3
    # SS8.3.3 diekspos sbg field INFORMATIF SAJA, TIDAK memengaruhi warna --
    # G1/G2 belum diputuskan Ketua Tim/Farmasi. Mengaktifkannya sbg pengubah
    # warna mentah-mentah berisiko mengulang pola kegagalan SS3.1/SS3.2 (lihat
    # reports/R4_dampak_eskalasi.md: 44% pengguna BMI>=30 akan kehilangan
    # HIJAU permanen bila diaktifkan tanpa syarat).
    metabolic_risk_flag: bool = Field(..., description="BMI pasien >= 30 (indikator risiko metabolik) -- [PENDING G1] belum memengaruhi warna")
    metabolic_risk_note: Optional[str] = Field(None, description="Catatan naratif bila metabolic_risk_flag=True; null bila False")
    evidence_strength: Literal["specific", "none"] = Field(..., description="'specific' bila injury_pattern bukti spesifik tersedia -- [PENDING G2] definisi 'strong evidence' belum diputuskan Farmasi, belum memengaruhi warna")
    evidence_strength_note: Optional[str] = Field(None, description="Catatan naratif bila evidence_strength='specific'; null bila 'none'")

    # --- R6 (gerbang G3, PROJECT_FUSION_V23.md SS3.3): PRD v2.3 SS8.3.1 meminta
    # mapping_confidence di kueri lookup, tapi kolom itu TIDAK ADA di database
    # (kurasi Farmasi masih berjalan). Opsi default G3: turunkan PROKSI dari
    # livertox_match_method (kolom yang memang ada), ditandai eksplisit sbg
    # turunan sementara -- BUKAN kolom kurasi asli.
    livertox_match_method: Optional[str] = Field(None, description="Metode pencocokan LiverTox dari kurasi internal (exact_name, salt_ester_normalized, dst); null bila no_match/tidak ada monograf")
    mapping_confidence: Literal["high", "medium", "none"] = Field(..., description="Proksi kepercayaan pemetaan, diturunkan dari livertox_match_method -- lihat mapping_confidence_source")
    mapping_confidence_source: Literal["DERIVED_PROXY_PENDING_G3"] = Field(
        "DERIVED_PROXY_PENDING_G3",
        description="Menegaskan mapping_confidence adalah proksi turunan aplikasi, BUKAN kolom kurasi asli (kolom itu belum ada di DB, gerbang G3)",
    )

    time_series_pbpk: List[TimeSeriesPBPKPoint] = Field(..., description="Kurva konsentrasi C_hati(t) & C_plasma(t) 24 jam")
    disclaimer_permanent: str = Field(..., description="Medical Disclaimer resmi HepaTwin (ASME V&V 40)")

    # --- C10 gerbang G6: perluasan kontrak API untuk SHAP tingkat atom ---
    # [KEPUTUSAN AI -- PENDING REVIEW KETUA TIM + FARIS] Optional dengan
    # default None -- backward-compatible, tidak memecah konsumen lama yang
    # belum tahu field ini. Usulan skema di EXECUTION_PLAN_FIX_MODEL.md C10
    # langkah 3.
    shap_detail: Optional[Dict[str, Any]] = Field(
        None,
        description="Struktur lengkap C8: {method, groups:[{name,value,atom_indices}], atoms:[{idx,value}], smiles_used}",
    )
    model_version: Optional[str] = Field(None, description='Versi model AI, mis. "gatnn-dnn-fixmodel-v1"')
    model_status: Optional[Literal["trained", "unavailable"]] = Field(
        None, description="Status model AI -- mencegah kebingungan model asli vs tidak ada"
    )
    score_is_calibrated: Optional[bool] = Field(None, description="True bila dili_score sudah melalui kalibrator (C7)")

    # --- F7 (gerbang K4, PROJECT_FUSION.md): perluasan kontrak backward-compatible ---
    fusion_reason: str = Field(..., description="Sel matriks fusi yang terpakai, mis. 'AI_MID x LOW_EXPOSURE' (F3)")
    thresholds_used: FusionThresholds = Field(..., description="Ambang T_low/T_high yang dipakai band AI pada simulasi ini (F2), utk transparansi/audit")
    timing_ms: Optional[Dict[str, float]] = Field(
        None,
        description="Durasi per-tahap (ms) -- HANYA terisi bila settings.DEBUG aktif (F6); null di produksi",
    )


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
