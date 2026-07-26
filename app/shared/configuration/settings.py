"""Validated application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables and optional .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "agent-rag-doces-sonhos"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_debug: bool = True
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minio"
    minio_secret_key: str = "minio-secret"
    minio_secure: bool = False
    minio_bucket: str = "products"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=list)
    docs_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("API_PREFIX deve começar com '/'")
        return value.rstrip("/")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL inválido")
        return normalized

    @field_validator("database_url", "redis_url")
    @classmethod
    def validate_connection_url(cls, value: str) -> str:
        if "://" not in value or not value.split("://", 1)[1]:
            raise ValueError("URL de conexão inválida")
        return value

    @field_validator("minio_endpoint", "minio_access_key", "minio_secret_key", "minio_bucket")
    @classmethod
    def validate_required_infrastructure_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Configuração de infraestrutura obrigatória")
        return normalized

    @field_validator("app_debug")
    @classmethod
    def validate_debug_in_production(cls, value: bool, info: ValidationInfo) -> bool:
        data = info.data
        if data.get("app_env") == "production" and value:
            raise ValueError("APP_DEBUG não pode ser true em produção")
        return value

    @field_validator("docs_enabled")
    @classmethod
    def validate_docs_in_production(cls, value: bool, info: ValidationInfo) -> bool:
        data = info.data
        if data.get("app_env") == "production" and value:
            raise ValueError("DOCS_ENABLED deve ser false em produção")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-level settings instance."""

    return Settings()
