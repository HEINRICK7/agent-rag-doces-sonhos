"""Deterministic product source used by ingestion tests."""

from collections.abc import AsyncIterator

from app.ingestion.application.dto.external_product_page import (
    ExternalProductPage,
    ProductFilters,
    ProductPageRequest,
)
from app.ingestion.application.ports.product_source import ProductSource


class FakeProductSource(ProductSource):
    def __init__(self, pages: list[ExternalProductPage]) -> None:
        self.pages = pages
        self.requests: list[ProductPageRequest] = []
        self.correlation_ids: list[str | None] = []

    async def fetch_page(
        self,
        request: ProductPageRequest,
        correlation_id: str | None = None,
    ) -> ExternalProductPage:
        self.requests.append(request)
        self.correlation_ids.append(correlation_id)
        index = min(request.page - 1, len(self.pages) - 1)
        return self.pages[index]

    async def iter_pages(
        self,
        filters: ProductFilters | None = None,
        correlation_id: str | None = None,
    ) -> AsyncIterator[ExternalProductPage]:
        del filters
        self.correlation_ids.append(correlation_id)
        for page in self.pages:
            yield page
