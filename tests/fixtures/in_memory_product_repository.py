"""In-memory product repository used by application tests."""

from uuid import UUID

from app.catalog.domain.entities.product import Product
from app.catalog.domain.repositories.product_repository import ProductRepository


class InMemoryProductRepository(ProductRepository):
    def __init__(self) -> None:
        self.products: dict[UUID, Product] = {}

    async def upsert(self, product: Product) -> Product:
        current = next(
            (
                candidate
                for candidate in self.products.values()
                if candidate.external_id == product.external_id
            ),
            None,
        )
        if current is None:
            self.products[product.id] = product
            return product
        current.apply_external_snapshot(product, product.last_synced_at)
        return current

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
