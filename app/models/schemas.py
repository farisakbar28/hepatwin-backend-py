from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SimulationRequest(BaseModel):
    mode: str = Field(
        ..., 
        description="Jalur komputasi simulasi: 'edukasi_mendalam' (model mekanistik) atau 'triase_umum' (model AI murni).", 
        example="edukasi_mendalam"
    )
    compound_id: Optional[str] = Field(
        None, 
        description="Identifier senyawa flagship ('paracetamol' atau 'amox_clav'). Hanya dipakai jika mode='edukasi_mendalam'.", 
        example="paracetamol"
    )
    dose_mg_kg: Optional[float] = Field(
        None, 
        description="Dosis obat dalam mg/kg berat badan. Diperlukan untuk komputasi PK/PD pada Mode Edukasi Mendalam.", 
        example=15.0
    )
    smiles_string: Optional[str] = Field(
        None, 
        description="Representasi struktur kimia (notasi SMILES) dari senyawa. Wajib diisi jika mode='triase_umum'.", 
        example="CC(=O)NC1=CC=C(O)C=C1"
    )

class SimulationResponse(BaseModel):
    mode: str = Field(
        ..., 
        description="Jalur komputasi yang dieksekusi.", 
        example="edukasi_mendalam"
    )
    compound_name: Optional[str] = Field(
        None, 
        description="Nama generik senyawa yang disimulasikan (jika tersedia).", 
        example="Paracetamol"
    )
    input_smiles: Optional[str] = Field(
        None, 
        description="Notasi SMILES dari senyawa yang diproses AI Engine.", 
        example="CC(=O)NC1=CC=C(O)C=C1"
    )
    DILI_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Skor probabilitas risiko Drug-Induced Liver Injury (DILI) hasil prediksi model AI hybrid (0.0 = Aman, 1.0 = Sangat Toksik).", 
        example=0.85
    )
    model_confidence_note: str = Field(
        ..., 
        description="Teks peringatan batas klaim (disclaimer) klinis wajib sesuai protokol etika penelitian.", 
        example="Estimasi awal berbasis model riset, bukan hasil uji klinis"
    )
    affected_zone: Optional[str] = Field(
        None, 
        description="Lokasi spesifik kerusakan anatomis pada lobulus hati. Bernilai None pada Mode Triase Umum.", 
        example="Zone_3"
    )
    explainability: List[str] = Field(
        ..., 
        description="Daftar gugus fungsi kimia (notasi SMARTS RDKit) atau parameter farmakologis yang paling berkontribusi terhadap skor kerusakan.", 
        example=["Phenol group", "Acetamide group"]
    )
    visual_pattern: str = Field(
        ..., 
        description="Identifier pola visual rendering 3D untuk Frontend (misal: 'sentrilobuler', 'portal_periportal', 'heatmap_generik').", 
        example="sentrilobuler"
    )
    time_series_pkpd: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Data time-series (konsentrasi obat dan rasio metabolit toksik terhadap waktu) hasil integrasi numerik untuk keperluan plot grafik.", 
        example=[{"time": 0, "NAPQI_ratio": 0.1}, {"time": 4, "NAPQI_ratio": 0.5}]
    )