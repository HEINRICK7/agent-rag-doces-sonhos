"""Boundary for the per-product stages of the ingestion pipeline."""

from collections.abc import Mapping
from typing import Protocol

from app.catalog.domain.entities.product_sync import ProductUpsertResult


class CatalogItemProcessor(Protocol):
    """Process one external product without controlling pagination or execution state."""

    async def process(
        self,
        payload: Mapping[str, object],
        correlation_id: str,
    ) -> ProductUpsertResult: ...
