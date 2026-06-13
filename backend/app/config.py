from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Any


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./rh_ai_agent.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    HH_API_TOKEN: str = ""
    HH_API_URL: str = "https://api.hh.ru"

    SUPERJOB_API_KEY: str = ""
    SUPERJOB_API_URL: str = "https://api.superjob.ru/2.0"

    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "agent@procompetencies.ru"
    EMAIL_FROM_NAME: str = "ProCompetencies Agent"

    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""

    SECRET_KEY: str = "dev_secret_key_change_in_production_32chars"
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    FOLLOWUP_DELAY_DAYS: int = 7
    FOLLOWUP_MAX_ATTEMPTS: int = 2

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> List[str]:
        """Принимает JSON-массив, строку через запятую или пустое значение."""
        if not v:
            return ["http://localhost:3000", "http://localhost:5173"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
