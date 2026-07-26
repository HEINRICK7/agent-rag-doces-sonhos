"""Normalize a mapped external product into the single ingestion format."""

import unicodedata
from dataclasses import replace
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.parse import SplitResult, urlsplit, urlunsplit

from app.ingestion.application.dto.product_input import (
    PriceOptionInput,
    ProductAvailability,
    ProductImageInput,
    ProductImportInput,
)
from app.ingestion.application.exceptions import ProductNormalizationError

DESCRIPTION_FALLBACK = "Descrição não informada."
PRICE_PRECISION = Decimal("0.01")


class NormalizeProductUseCase:
    """Apply deterministic validation and normalization without infrastructure rules."""

    def execute(self, product: ProductImportInput) -> ProductImportInput:
        external_id = _required_identifier(product.external_id, "external_id")
        name = _required_text(product.name, "name")
        description = _optional_text(product.description) or DESCRIPTION_FALLBACK
        category_external_id = _optional_identifier(
            product.category_external_id,
            "category_external_id",
        )
        subcategory_external_id = _optional_identifier(
            product.subcategory_external_id,
            "subcategory_external_id",
        )
        stock_quantity = _normalize_stock(product.stock_quantity)
        availability = _normalize_availability(product.is_active, stock_quantity)
        currency = _normalize_currency(product.currency)
        prices = tuple(
            _normalize_price(option, index) for index, option in enumerate(product.price_options)
        )
        if not prices:
            raise ProductNormalizationError("price_options", "ao menos um preço é obrigatório.")
        prices = _select_default_price(prices)

        return replace(
            product,
            external_id=external_id,
            name=name,
            description=description,
            category_external_id=category_external_id,
            subcategory_external_id=subcategory_external_id,
            availability=availability,
            currency=currency,
            stock_quantity=stock_quantity,
            price_options=prices,
            images=_normalize_images(product.images),
            ignored_fields=tuple(sorted(set(product.ignored_fields))),
        )


def _required_identifier(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ProductNormalizationError(field, "identificador obrigatório.")
    if any(character.isspace() for character in normalized):
        raise ProductNormalizationError(field, "identificador não pode conter espaços.")
    return normalized


def _optional_identifier(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if any(character.isspace() for character in normalized):
        raise ProductNormalizationError(
            field,
            "identificador não pode conter espaços.",
        )
    return normalized


def _required_text(value: str, field: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        raise ProductNormalizationError(field, "texto obrigatório.")
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    return _normalize_text(value) or None


def _normalize_text(value: str) -> str:
    compatible = unicodedata.normalize("NFKC", value)
    return " ".join(compatible.split())


def _normalize_stock(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if not value.is_finite() or value < 0:
        raise ProductNormalizationError(
            "stock_quantity",
            "estoque deve ser finito e não negativo.",
        )
    return value.normalize()


def _normalize_availability(
    is_active: bool,
    stock_quantity: Decimal | None,
) -> ProductAvailability:
    if not is_active:
        return "unavailable"
    if stock_quantity == 0:
        return "out_of_stock"
    if stock_quantity is not None:
        return "available"
    return "unknown"


def _normalize_currency(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if not normalized:
        return None
    if len(normalized) != 3 or not normalized.isalpha():
        raise ProductNormalizationError(
            "currency",
            "moeda deve usar um código alfabético de três letras.",
        )
    return normalized


def _normalize_price(option: PriceOptionInput, index: int) -> PriceOptionInput:
    field = f"price_options[{index}]"
    if not option.amount.is_finite() or option.amount < 0:
        raise ProductNormalizationError(field, "preço deve ser finito e não negativo.")
    if not option.quantity.is_finite() or option.quantity <= 0:
        raise ProductNormalizationError(field, "quantidade deve ser finita e positiva.")
    unit = _required_text(option.unit, field).upper()
    try:
        amount = option.amount.quantize(PRICE_PRECISION, rounding=ROUND_HALF_UP)
    except InvalidOperation as error:
        raise ProductNormalizationError(field, "preço excede a precisão suportada.") from error
    return replace(
        option,
        external_id=_optional_identifier(option.external_id, f"{field}.external_id"),
        label=_optional_text(option.label),
        quantity=option.quantity.normalize(),
        unit=unit,
        amount=amount,
    )


def _select_default_price(
    prices: tuple[PriceOptionInput, ...],
) -> tuple[PriceOptionInput, ...]:
    default_index = next(
        (index for index, price in enumerate(prices) if price.is_default),
        0,
    )
    return tuple(
        replace(price, is_default=index == default_index) for index, price in enumerate(prices)
    )


def _normalize_images(images: tuple[ProductImageInput, ...]) -> tuple[ProductImageInput, ...]:
    normalized: list[ProductImageInput] = []
    seen: set[str] = set()
    for index, image in enumerate(images):
        source_url = _normalize_url(image.source_url, index)
        if source_url in seen:
            continue
        seen.add(source_url)
        normalized.append(ProductImageInput(source_url=source_url, is_primary=False))

    if not normalized:
        return ()
    return tuple(replace(image, is_primary=index == 0) for index, image in enumerate(normalized))


def _normalize_url(value: str, index: int) -> str:
    normalized = value.strip()
    try:
        parts = urlsplit(normalized)
    except ValueError as error:
        raise ProductNormalizationError(
            f"images[{index}].source_url",
            "imagem possui uma URL inválida.",
        ) from error
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise ProductNormalizationError(
            f"images[{index}].source_url",
            "imagem deve possuir uma URL HTTP(S) absoluta.",
        )
    clean_parts = SplitResult(
        scheme=parts.scheme.lower(),
        netloc=parts.netloc.lower(),
        path=parts.path,
        query=parts.query,
        fragment="",
    )
    return urlunsplit(clean_parts)
