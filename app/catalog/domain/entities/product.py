"""Product aggregate and external synchronization policy."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.catalog.domain.entities.product_image import ProductImage
from app.catalog.domain.entities.product_price_option import ProductPriceOption
from app.catalog.domain.exceptions import (
    ExternalProductIdentityMismatchError,
    InvalidCatalogValueError,
)
from app.catalog.domain.value_objects.product_availability import ProductAvailability


class ProductProtectedField(StrEnum):
    """Local product fields that may opt out of external overwrites."""

    NAME = "name"
    DESCRIPTION = "description"
    CATEGORY = "category"


@dataclass(slots=True)
class Product:
    """Catalog product with local identity and controlled external updates."""

    id: UUID
    external_id: str
    name: str
    description: str
    category_external_id: str | None
    subcategory_external_id: str | None
    is_active: bool
    availability: ProductAvailability
    price_options: tuple[ProductPriceOption, ...]
    images: tuple[ProductImage, ...]
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime
    source_created_at: datetime | None = None
    source_updated_at: datetime | None = None
    protected_fields: frozenset[ProductProtectedField] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        self.external_id = _required_identifier(self.external_id)
        self.name = _required_text(self.name, "product.name")
        self.description = _required_text(self.description, "product.description")
        self.category_external_id = _optional_identifier(self.category_external_id)
        self.subcategory_external_id = _optional_identifier(self.subcategory_external_id)
        _validate_prices(self.price_options)
        _validate_images(self.images)
        if not self.is_active and self.availability is not ProductAvailability.UNAVAILABLE:
            raise InvalidCatalogValueError(
                "product.availability",
                "produto inativo deve estar indisponível.",
            )

    def protect(self, protected_field: ProductProtectedField) -> None:
        self.protected_fields = self.protected_fields | {protected_field}

    def unprotect(self, protected_field: ProductProtectedField) -> None:
        self.protected_fields = self.protected_fields - {protected_field}

    def activate(
        self,
        at: datetime,
        availability: ProductAvailability = ProductAvailability.UNKNOWN,
    ) -> None:
        if availability is ProductAvailability.UNAVAILABLE:
            raise InvalidCatalogValueError(
                "product.availability",
                "produto ativo precisa de disponibilidade ativa ou desconhecida.",
            )
        self.is_active = True
        self.availability = availability
        self.updated_at = at

    def deactivate(self, at: datetime) -> None:
        self.is_active = False
        self.availability = ProductAvailability.UNAVAILABLE
        self.updated_at = at

    def record_sync(self, at: datetime, source_updated_at: datetime | None) -> None:
        self.last_synced_at = at
        self.source_updated_at = source_updated_at
        self.updated_at = at

    def apply_external_snapshot(self, snapshot: "Product", at: datetime) -> None:
        """Apply source-owned fields while honoring local field protection."""

        if snapshot.external_id != self.external_id:
            raise ExternalProductIdentityMismatchError(
                expected=self.external_id,
                received=snapshot.external_id,
            )
        if ProductProtectedField.NAME not in self.protected_fields:
            self.name = snapshot.name
        if ProductProtectedField.DESCRIPTION not in self.protected_fields:
            self.description = snapshot.description
        if ProductProtectedField.CATEGORY not in self.protected_fields:
            self.category_external_id = snapshot.category_external_id
            self.subcategory_external_id = snapshot.subcategory_external_id

        self.is_active = snapshot.is_active
        self.availability = snapshot.availability
        self.price_options = snapshot.price_options
        self.images = snapshot.images
        self.source_created_at = snapshot.source_created_at
        self.source_updated_at = snapshot.source_updated_at
        self.last_synced_at = at
        self.updated_at = at


def _required_identifier(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidCatalogValueError(
            "product.external_id",
            "identificador obrigatório.",
        )
    if any(character.isspace() for character in normalized):
        raise InvalidCatalogValueError(
            "product.external_id",
            "identificador não pode conter espaços.",
        )
    return normalized


def _optional_identifier(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None


def _required_text(value: str, field: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise InvalidCatalogValueError(field, "texto obrigatório.")
    return normalized


def _validate_prices(prices: tuple[ProductPriceOption, ...]) -> None:
    if not prices:
        raise InvalidCatalogValueError(
            "product.price_options",
            "ao menos uma opção de preço é obrigatória.",
        )
    if sum(option.is_default for option in prices) != 1:
        raise InvalidCatalogValueError(
            "product.price_options",
            "exatamente uma opção de preço deve ser padrão.",
        )


def _validate_images(images: tuple[ProductImage, ...]) -> None:
    if images and sum(image.is_primary for image in images) != 1:
        raise InvalidCatalogValueError(
            "product.images",
            "exatamente uma imagem deve ser principal.",
        )
    positions = [image.position for image in images]
    if len(positions) != len(set(positions)):
        raise InvalidCatalogValueError(
            "product.images",
            "posições de imagem não podem se repetir.",
        )
