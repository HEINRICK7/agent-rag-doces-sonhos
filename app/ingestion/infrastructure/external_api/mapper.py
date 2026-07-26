"""Anti-corruption mapping from Doces Sonhos payloads to internal DTOs."""

from collections.abc import Mapping

from pydantic import ValidationError

from app.ingestion.application.dto.product_input import (
    CategoryImportInput,
    PriceOptionInput,
    ProductAvailability,
    ProductImageInput,
    ProductImportInput,
    SubcategoryImportInput,
)
from app.ingestion.application.exceptions import ExternalProductMappingError
from app.ingestion.infrastructure.external_api.schemas import (
    ExternalCategorySchema,
    ExternalProductSchema,
    ExternalSubcategorySchema,
)


def map_external_product(payload: Mapping[str, object]) -> ProductImportInput:
    try:
        product = ExternalProductSchema.model_validate(payload)
    except ValidationError as exc:
        raise ExternalProductMappingError("Produto externo inválido.", exc.errors()) from exc

    availability: ProductAvailability
    if not product.is_active:
        availability = "unavailable"
    elif product.stock_quantity == 0:
        availability = "out_of_stock"
    elif product.stock_quantity is not None and product.stock_quantity > 0:
        availability = "available"
    else:
        availability = "unknown"

    image = product.image.strip() if product.image else ""
    currency = product.currency.strip().upper() if product.currency else None
    return ProductImportInput(
        external_id=product.id,
        name=product.name,
        description=product.description,
        category_external_id=product.category_id,
        subcategory_external_id=product.subcategory_id,
        is_active=product.is_active,
        availability=availability,
        currency=currency or None,
        stock_quantity=product.stock_quantity,
        price_options=tuple(
            PriceOptionInput(
                external_id=option.id,
                label=option.label,
                quantity=option.quantity,
                unit=option.unit,
                amount=option.price,
                is_default=option.is_default,
            )
            for option in product.price_options
        ),
        images=(ProductImageInput(source_url=image, is_primary=True),) if image else (),
        source_created_at=product.created_at,
        source_updated_at=product.updated_at,
        ignored_fields=_ignored_fields(product.model_extra),
    )


def map_external_category(payload: Mapping[str, object]) -> CategoryImportInput:
    try:
        category = ExternalCategorySchema.model_validate(payload)
    except ValidationError as exc:
        raise ExternalProductMappingError("Categoria externa inválida.", exc.errors()) from exc
    return CategoryImportInput(
        external_id=category.id,
        name=category.name,
        icon=category.icon,
        image_url=category.image,
        is_active=category.is_active,
        position=category.position,
        source_created_at=category.created_at,
        source_updated_at=category.updated_at,
        ignored_fields=_ignored_fields(category.model_extra),
    )


def map_external_subcategory(payload: Mapping[str, object]) -> SubcategoryImportInput:
    try:
        subcategory = ExternalSubcategorySchema.model_validate(payload)
    except ValidationError as exc:
        raise ExternalProductMappingError("Subcategoria externa inválida.", exc.errors()) from exc
    return SubcategoryImportInput(
        external_id=subcategory.id,
        category_external_id=subcategory.category_id,
        name=subcategory.name,
        source_created_at=subcategory.created_at,
        source_updated_at=subcategory.updated_at,
        ignored_fields=_ignored_fields(subcategory.model_extra),
    )


def _ignored_fields(extra: dict[str, object] | None) -> tuple[str, ...]:
    return tuple(sorted(extra or {}))
