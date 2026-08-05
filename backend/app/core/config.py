"""Application settings and environment configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="DecisionTwin AI Backend", validation_alias="APP_NAME")
    app_description: str = Field(
        default="Backend foundation for DecisionTwin AI",
        validation_alias="APP_DESCRIPTION",
    )
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        validation_alias="CORS_ORIGINS",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, value: Any) -> list[str]:
        if value is None:
            return ["http://localhost:3000", "http://localhost:5173"]
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        raise TypeError("allowed_origins must be provided as a string or list")

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return a SQLAlchemy-compatible database URL."""
        if not self.database_url:
            raise ValueError("DATABASE_URL is not configured")

        url = make_url(self.database_url)

        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")

        return url.render_as_string(hide_password=False)

    @property
    def masked_database_url(self) -> str:
        """Return the configured database URL with the password masked."""
        if not self.database_url:
            return "<not configured>"

        return make_url(self.database_url).render_as_string(hide_password=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()