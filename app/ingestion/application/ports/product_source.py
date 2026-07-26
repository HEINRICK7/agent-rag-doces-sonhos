"""Contract for reading products from an external source."""

from collections.abc import AsyncIterator
from typing import Protocol

from app.ingestion.application.dto.external_product_page import (
    ExternalProductPage,
    ProductFilters,
    ProductPageRequest,
)


class ProductSource(Protocol):
    """Substitutable source used by future catalog synchronization use cases."""

    async def fetch_page(
        self,
        request: ProductPageRequest,
        correlation_id: str | None = None,
    ) -> ExternalProductPage: ...

    def iter_pages(
        self,
        filters: ProductFilters | None = None,
        correlation_id: str | None = None,
    ) -> AsyncIterator[ExternalProductPage]: ...
