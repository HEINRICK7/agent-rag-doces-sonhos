"""Permissive transport schemas used before business mapping is known."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExternalSchema(BaseModel):
    """Base schema that tolerates additions while retaining unknown fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ExternalPriceOptionSchema(ExternalSchema):
    id: str | None = None
    label: str | None = None
    quantity: Decimal = Field(gt=0)
    unit: str = Field(min_length=1)
    price: Decimal = Field(ge=0)
    is_default: bool = Field(default=False, alias="isDefault")


class ExternalProductSchema(ExternalSchema):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    image: str | None = None
    category_id: str | None = Field(default=None, alias="categoryId")
    subcategory_id: str | None = Field(default=None, alias="subcategoryId")
    is_active: bool = Field(alias="isActive")
    price_options: list[ExternalPriceOptionSchema] = Field(
        alias="priceOptions",
        min_length=1,
    )
    currency: str | None = None
    stock_quantity: Decimal | None = Field(default=None, alias="stockQuantity", ge=0)
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")


class ExternalCategorySchema(ExternalSchema):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    icon: str | None = None
    image: str | None = None
    is_active: bool = Field(alias="isActive")
    position: int | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")


class ExternalSubcategorySchema(ExternalSchema):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category_id: str = Field(alias="categoryId", min_length=1)
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")


class ExternalProductPageEnvelope(ExternalSchema):
    """Validated envelope assembled from configurable external field names."""

    items: list[dict[str, Any]] = Field(default_factory=list)
    has_more: bool = False
    next_cursor: str | None = None
    total: int | None = None
