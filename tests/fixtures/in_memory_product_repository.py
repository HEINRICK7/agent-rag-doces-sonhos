"""In-memory product repository used by application tests."""

from uuid import UUID

from app.catalog.domain.entities.product import Product
from app.catalog.domain.entities.product_sync import ProductChangeKind, ProductUpsertResult
from app.catalog.domain.repositories.product_repository import ProductRepository
from app.catalog.domain.services.product_fingerprint import fingerprint_product


class InMemoryProductRepository(ProductRepository):
    def __init__(self) -> None:
        self.products: dict[UUID, Product] = {}

    async def upsert(self, product: Product) -> Product:
        return (await self.upsert_incremental(product)).product

    async def upsert_incremental(self, product: Product) -> ProductUpsertResult:
        current_fingerprint = fingerprint_product(product)
        current = next(
            (
                candidate
                for candidate in self.products.values()
                if candidate.external_id == product.external_id
            ),
            None,
        )
        if current is None:
            product.source_fingerprint = current_fingerprint
            self.products[product.id] = product
            return ProductUpsertResult(
                product,
                ProductChangeKind.CREATED,
                None,
                current_fingerprint,
            )
        previous_fingerprint = current.source_fingerprint or fingerprint_product(current)
        if previous_fingerprint == current_fingerprint:
            current.last_synced_at = product.last_synced_at
            return ProductUpsertResult(
                current,
                ProductChangeKind.UNCHANGED,
                previous_fingerprint,
                current_fingerprint,
            )
        current.apply_external_snapshot(product, product.last_synced_at)
        current.source_fingerprint = current_fingerprint
        return ProductUpsertResult(
            current,
            ProductChangeKind.UPDATED,
            previous_fingerprint,
            current_fingerprint,
        )

    async def get_by_id(self, product_id: UUID) -> Product | None:
        return self.products.get(product_id)

    async def get_by_external_id(self, external_id: str) -> Product | None:
        return next(
            (product for product in self.products.values() if product.external_id == external_id),
            None,
        )

    async def list(self, limit: int, offset: int) -> list[Product]:
        products = list(self.products.values())
        return products[offset : offset + limit]
