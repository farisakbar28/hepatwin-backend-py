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
    AI_MODEL_PATH: str = "models/model.pt"
    DEBUG: bool = False
    
    # [ASUMSI DESAIN -- PENDING K3] 30/10 & 0.40/0.35/0.30/0.20
    DOSE_HIGH_THRESHOLD: float = 30.0
    DOSE_MODERATE_THRESHOLD: float = 10.0
    RATIO_HIGH_MODIFIER: float = 0.35
    RATIO_HIGH_NORMAL: float = 0.40
    RATIO_MODERATE_MODIFIER: float = 0.20
    RATIO_MODERATE_NORMAL: float = 0.30

    # [ASUMSI DESAIN -- PENDING FARMASI]
    base_cl_metabolism_l_hr: float = 15.0  

    # [ASUMSI DESAIN minor -- PENDING FARMASI] Basis alometrik (ekuivalen 81 L/h, bukan 90 absolut)
    Q_L_baseline: float = 1.35

    # [ASUMSI DESAIN minor]
    V_L_frac: float = 0.025  

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