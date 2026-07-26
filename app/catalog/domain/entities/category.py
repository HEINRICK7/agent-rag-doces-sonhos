"""Product category aggregate."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.catalog.domain.exceptions import InvalidCatalogValueError


@dataclass(slots=True)
class Category:
    """Category synchronized from the source while retaining local identity."""

    id: UUID
    external_id: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime
    icon: str | None = None
    image_url: str | None = None
    position: int | None = None
    source_created_at: datetime | None = None
    source_updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.external_id = _required(self.external_id, "category.external_id")
        self.name = _required(self.name, "category.name")
        self.icon = _optional(self.icon)
        self.image_url = _optional(self.image_url)
        if self.position is not None and self.position < 0:
            raise InvalidCatalogValueError(
                "category.position",
                "posição não pode ser negativa.",
            )

    def activate(self, at: datetime) -> None:
        self.is_active = True
        self.updated_at = at

    def deactivate(self, at: datetime) -> None:
        self.is_active = False
        self.updated_at = at

    def record_sync(self, at: datetime, source_updated_at: datetime | None) -> None:
        self.last_synced_at = at
        self.source_updated_at = source_updated_at
        self.updated_at = at


def _required(value: str, field: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise InvalidCatalogValueError(field, "valor obrigatório.")
    return normalized


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.split()) or None
