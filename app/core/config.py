import json
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "HepaTwin Backend API"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000"]
    AI_MODEL_PATH: str = "models/model.pt"
    CACHE_DB_PATH: str = "cache.db"
    DEBUG: bool = False
    # JANGAN aktifkan di produksi. Bila True, /simulate mengembalikan response
    # dummy berbentuk final tanpa menyentuh Mesin A/B — dipakai frontend saat
    # konstanta PD belum tervalidasi Farmasi (PRD §13 #1, audit TA.8).
    MOCK_MODE: bool = False
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