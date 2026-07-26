"""Mappers between catalog domain aggregates and SQLAlchemy models."""

from datetime import UTC, datetime

from app.catalog.domain.entities.category import Category
from app.catalog.domain.entities.product import Product, ProductProtectedField
from app.catalog.domain.entities.product_image import ProductImage
from app.catalog.domain.entities.product_price_option import ProductPriceOption
from app.catalog.domain.value_objects.money import Money
from app.catalog.domain.value_objects.product_availability import ProductAvailability
from app.catalog.infrastructure.persistence.models import (
    CategoryModel,
    ProductImageModel,
    ProductModel,
    ProductPriceOptionModel,
)


def product_to_model(product: Product) -> ProductModel:
    model = ProductModel()
    update_product_model(model, product)
    return model


def update_product_model(model: ProductModel, product: Product) -> None:
    model.id = product.id
    model.external_id = product.external_id
    model.name = product.name
    model.description = product.description
    model.category_external_id = product.category_external_id
    model.subcategory_external_id = product.subcategory_external_id
    model.is_active = product.is_active
    model.availability = product.availability.value
    model.protected_fields = sorted(field.value for field in product.protected_fields)
    model.created_at = product.created_at
    model.updated_at = product.updated_at
    model.last_synced_at = product.last_synced_at
    model.source_created_at = product.source_created_at
    model.source_updated_at = product.source_updated_at
    model.price_options = [
        ProductPriceOptionModel(
            product_id=product.id,
            position=position,
            external_id=option.external_id,
            label=option.label,
            quantity=option.quantity,
            unit=option.unit,
            amount=option.price.amount,
            currency=option.price.currency,
            is_default=option.is_default,
        )
        for position, option in enumerate(product.price_options)
    ]
    model.images = [
        ProductImageModel(
            product_id=product.id,
            position=image.position,
            source_url=image.source_url,
            storage_key=image.storage_key,
            is_primary=image.is_primary,
        )
        for image in product.images
    ]


def product_to_domain(model: ProductModel) -> Product:
    return Product(
        id=model.id,
        external_id=model.external_id,
        name=model.name,
        description=model.description,
        category_external_id=model.category_external_id,
        subcategory_external_id=model.subcategory_external_id,
        is_active=model.is_active,
        availability=ProductAvailability(model.availability),
        price_options=tuple(
            ProductPriceOption(
                external_id=option.external_id,
                label=option.label,
                quantity=option.quantity,
                unit=option.unit,
                price=Money(option.amount, option.currency),
                is_default=option.is_default,
            )
            for option in model.price_options
        ),
        images=tuple(
            ProductImage(
                source_url=image.source_url,
                position=image.position,
                is_primary=image.is_primary,
                storage_key=image.storage_key,
            )
            for image in model.images
        ),
        created_at=_as_utc(model.created_at),
        updated_at=_as_utc(model.updated_at),
        last_synced_at=_as_utc(model.last_synced_at),
        source_created_at=_as_optional_utc(model.source_created_at),
        source_updated_at=_as_optional_utc(model.source_updated_at),
        protected_fields=frozenset(
            ProductProtectedField(field) for field in model.protected_fields
        ),
    )


def category_to_model(category: Category) -> CategoryModel:
    return CategoryModel(
        id=category.id,
        external_id=category.external_id,
        name=category.name,
        icon=category.icon,
        image_url=category.image_url,
        position=category.position,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
        last_synced_at=category.last_synced_at,
        source_created_at=category.source_created_at,
        source_updated_at=category.source_updated_at,
    )


def category_to_domain(model: CategoryModel) -> Category:
    return Category(
        id=model.id,
        external_id=model.external_id,
        name=model.name,
        icon=model.icon,
        image_url=model.image_url,
        position=model.position,
        is_active=model.is_active,
        created_at=_as_utc(model.created_at),
        updated_at=_as_utc(model.updated_at),
        last_synced_at=_as_utc(model.last_synced_at),
        source_created_at=_as_optional_utc(model.source_created_at),
        source_updated_at=_as_optional_utc(model.source_updated_at),
    )


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return _as_utc(value) if value is not None else None
