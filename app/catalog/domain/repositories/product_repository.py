"""Persistence contract owned by the catalog domain."""

from typing import Protocol
from uuid import UUID

from app.catalog.domain.entities.product import Product
from app.catalog.domain.entities.product_sync import ProductUpsertResult


class ProductRepository(Protocol):
    """Persist and retrieve catalog products without exposing SQLAlchemy."""

    async def upsert(self, product: Product) -> Product: ...

    async def upsert_incremental(self, product: Product) -> ProductUpsertResult: ...

    async def get_by_id(self, product_id: UUID) -> Product | None: ...

    async def get_by_external_id(self, external_id: str) -> Product | None: ...

    async def list(self, limit: int, offset: int) -> list[Product]: ...
