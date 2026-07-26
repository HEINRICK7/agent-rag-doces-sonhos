"""Transport-independent representation of an external catalog page."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductFilters:
    """Filters confirmed by the external products endpoint."""

    search: str | None = None
    category_id: str | None = None
    subcategory_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProductPageRequest:
    """Position and size of a page requested from the product source."""

    page: int = 1
    offset: int = 0
    limit: int = 100
    cursor: str | None = None
    next_url: str | None = None
    filters: ProductFilters = ProductFilters()

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page deve ser maior ou igual a 1")
        if self.offset < 0:
            raise ValueError("offset não pode ser negativo")
        if not 1 <= self.limit <= 500:
            raise ValueError("limit deve estar entre 1 e 500")


@dataclass(frozen=True, slots=True)
class ExternalProductPage:
    """Raw products and continuation data without business normalization."""

    items: tuple[dict[str, object], ...]
    request: ProductPageRequest
    has_more: bool
    next_request: ProductPageRequest | None
    total: int | None = None
