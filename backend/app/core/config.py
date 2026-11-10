from pathlib import Path
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ArogyaMitra API"
    environment: str = "development"
    database_url: str
    frontend_origin: str = "http://localhost:5173"
    jwt_secret_key: str = "change-this-development-secret-key-32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    supabase_url: Optional[str] = None
    supabase_service_role_key: Optional[str] = Field(default=None, repr=False)
    storage_bucket: str = "medical-documents"
    max_upload_size: int = 10 * 1024 * 1024
    openai_api_key: Optional[str] = Field(default=None, repr=False)
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime_secrets(self) -> "Settings":
        if self.environment.lower() not in {"development", "test"} and (
            self.jwt_secret_key == "change-this-development-secret-key-32"
            or len(self.jwt_secret_key) < 32
        ):
            raise ValueError("JWT_SECRET_KEY must be a unique secret of at least 32 characters outside development")
        return self


settings = Settings()
