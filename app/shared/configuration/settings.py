"""Validated application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, ValidationInfo, field_validator
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
    external_api_base_url: str | None = None
    external_api_products_path: str = "/products"
    external_api_auth_mode: Literal["none", "bearer", "api_key"] = "none"
    external_api_token: SecretStr | None = None
    external_api_api_key_header: str = "X-API-Key"
    external_api_timeout_seconds: float = 10.0
    external_api_retry_attempts: int = 3
    external_api_retry_backoff_seconds: float = 0.25
    external_api_max_retry_delay: float = 5.0
    external_api_pagination_mode: Literal["none", "page", "offset", "cursor", "link"] = "none"
    external_api_page_size: int = 100
    external_api_max_pages: int = 1000
    external_api_page_param: str = "page"
    external_api_offset_param: str = "offset"
    external_api_limit_param: str = "limit"
    external_api_cursor_param: str = "cursor"
    external_api_items_key: str = "items"
    external_api_has_more_key: str = "has_more"
    external_api_next_cursor_key: str = "next_cursor"
    external_api_total_key: str = "total"
    external_api_infer_has_more_from_page_size: bool = False
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

    @field_validator("external_api_base_url", "external_api_token", mode="before")
    @classmethod
    def normalize_optional_external_value(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("external_api_base_url")
    @classmethod
    def validate_external_api_base_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("EXTERNAL_API_BASE_URL deve usar http ou https")
        return value.rstrip("/") if value else None

    @field_validator("external_api_products_path")
    @classmethod
    def validate_external_api_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("EXTERNAL_API_PRODUCTS_PATH não pode ser vazio")
        return f"/{normalized.lstrip('/')}"

    @field_validator(
        "external_api_api_key_header",
        "external_api_page_param",
        "external_api_offset_param",
        "external_api_limit_param",
        "external_api_cursor_param",
        "external_api_items_key",
        "external_api_has_more_key",
        "external_api_next_cursor_key",
        "external_api_total_key",
    )
    @classmethod
    def validate_external_api_field_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Nome de campo da API externa não pode ser vazio")
        return normalized

    @field_validator(
        "external_api_timeout_seconds",
        "external_api_retry_backoff_seconds",
        "external_api_max_retry_delay",
    )
    @classmethod
    def validate_positive_external_duration(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Duração da API externa deve ser positiva")
        return value

    @field_validator(
        "external_api_retry_attempts", "external_api_page_size", "external_api_max_pages"
    )
    @classmethod
    def validate_positive_external_count(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Contagem da API externa deve ser positiva")
        return value

    @field_validator("external_api_page_size")
    @classmethod
    def validate_external_page_size(cls, value: int) -> int:
        if value > 500:
            raise ValueError("EXTERNAL_API_PAGE_SIZE não pode exceder 500")
        return value

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
