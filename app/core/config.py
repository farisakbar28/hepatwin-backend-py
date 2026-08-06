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
    
    # PBPK Phase 1 v2.3. The renal fallback remains a transparent design
    # parameter until compound-specific renal data are curated.
    PBPK_BASE_CL_METABOLISM_70_L_H: float = 15.0
    PBPK_BASE_CL_RENAL_70_L_H: float = 2.0
    PBPK_CARDIAC_FLOW_70_L_H: float = 360.0
    PBPK_PLASMA_VOLUME_FRACTION: float = 0.043
    PBPK_LIVER_VOLUME_FRACTION: float = 0.0257
    PBPK_KIDNEY_VOLUME_FRACTION: float = 0.0044

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
