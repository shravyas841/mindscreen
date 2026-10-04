import os
from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent
_ENV_PATH = _BACKEND_DIR / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./mental_health.db"
    SECRET_KEY: str = "mindscreen-default-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    HF_TOKEN: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    CRISIS_HELPLINE_1: str = "Tele-MANAS: 14416 or 1-800-891-4416 (free, 24/7)"
    CRISIS_HELPLINE_2: str = "iCall (TISS): 9152987821"

    ALLOWED_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=(str(_ENV_PATH), ".env"),
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.ENVIRONMENT.lower() == "production":
            insecure_values = {
                "",
                "mindscreen-default-secret-change-in-production",
                "your-super-secret-key-here-change-this",
            }
            if self.SECRET_KEY.strip() in insecure_values or len(self.SECRET_KEY.strip()) < 32:
                raise ValueError("SECRET_KEY must be configured in production with at least 32 characters")
            allowed_origins = {
                origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()
            }
            if "*" in allowed_origins:
                raise ValueError("ALLOWED_ORIGINS cannot contain a wildcard in production")
        return self

settings = Settings()


def crisis_helplines() -> list[str]:
    return [settings.CRISIS_HELPLINE_1, settings.CRISIS_HELPLINE_2]
