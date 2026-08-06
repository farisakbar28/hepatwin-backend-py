from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
import json

class Settings(BaseSettings):
    PROJECT_NAME: str = "HepaTwin Backend API"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000"]
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    AI_MODEL_PATH: str = "app/models/model_gatnn_dnn.pt"
    DEBUG: bool = False

    # F2 (gerbang K2, PROJECT_FUSION.md SS4.2) -- ambang band AI dili_score
    # utk matriks fusi 3x3 (F3). Default = metode (b) pemetaan-balik (skor
    # kalibrator utk raw=0.30/0.70), diturunkan dari reports/F2_penurunan_ambang.md.
    # [KEPUTUSAN AI -- PENDING REVIEW FARMASI + KETUA TIM, gerbang K2]
    FUSION_AI_T_LOW: float = 0.5458
    FUSION_AI_T_HIGH: float = 0.6866

    # F5 (gerbang K3, PROJECT_FUSION.md SS3.5) -- enam ambang exposure_evaluator.
    # [ASUMSI DESAIN -- PENDING REVIEW FARMASI, gerbang K3] Soejima et al. (2022)
    # & Ghabril et al. (2025) mendukung KEBERADAAN modifikator usia>=60/BMI>=30;
    # KEENAM NILAI di bawah TIDAK bersitasi -- dipertahankan apa adanya per
    # keputusan default K3 (PROJECT_FUSION.md SS6), dipindah ke config supaya
    # Farmasi bisa merevisi tanpa menyentuh logika exposure_evaluator.py.
    EXPOSURE_DOSE_HIGH_MG_PER_KG: float = 30.0
    EXPOSURE_DOSE_MODERATE_MG_PER_KG: float = 10.0
    EXPOSURE_RATIO_HIGH_THRESHOLD: float = 0.40
    EXPOSURE_RATIO_HIGH_THRESHOLD_VULNERABLE: float = 0.35
    EXPOSURE_RATIO_MODERATE_THRESHOLD: float = 0.30
    EXPOSURE_RATIO_MODERATE_THRESHOLD_VULNERABLE: float = 0.20
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()