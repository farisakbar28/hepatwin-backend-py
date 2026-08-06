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