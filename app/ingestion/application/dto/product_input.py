"""Internal ingestion DTOs independent from the external API schema."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

ProductAvailability = Literal["available", "unavailable", "out_of_stock", "unknown"]


@dataclass(frozen=True, slots=True)
class PriceOptionInput:
    external_id: str | None
    label: str | None
    quantity: Decimal
    unit: str
    amount: Decimal
    is_default: bool


@dataclass(frozen=True, slots=True)
class ProductImageInput:
    source_url: str
    is_primary: bool


@dataclass(frozen=True, slots=True)
class ProductImportInput:
    external_id: str
    name: str
    description: str | None
    category_external_id: str | None
    subcategory_external_id: str | None
    is_active: bool
    availability: ProductAvailability
    currency: str | None
    stock_quantity: Decimal | None
    price_options: tuple[PriceOptionInput, ...]
    images: tuple[ProductImageInput, ...]
    source_created_at: datetime | None
    source_updated_at: datetime | None
    ignored_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CategoryImportInput:
    external_id: str
    name: str
    icon: str | None
    image_url: str | None
    is_active: bool
    position: int | None
    source_created_at: datetime | None
    source_updated_at: datetime | None
    ignored_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubcategoryImportInput:
    external_id: str
    category_external_id: str
    name: str
    source_created_at: datetime | None
    source_updated_at: datetime | None
    ignored_fields: tuple[str, ...]
