from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_name: str = "Marksheet System"
    secret_key: str = "development-only-secret-key-change-me"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/marksheets"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    demo_default_password: str = ""
    require_password_change_in_production: bool = True
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    document_storage_path: str = "./storage"
    document_storage_backend: str = "local"
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_s3_bucket: str | None = None
    aws_s3_endpoint: str | None = None
    aws_s3_force_path_style: bool = False
    handwriting_model_path: str | None = None
    ocr_mark_column_indices: str = "2,-1"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        return [item.strip() for item in value.split(",")] if isinstance(value, str) else value

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def uses_s3(self) -> bool:
        return self.document_storage_backend.lower() == "s3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
