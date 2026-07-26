"""Product repository integration tests using isolated async SQLite."""

import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID

from app.catalog.domain.entities.product import Product, ProductProtectedField
from app.catalog.domain.entities.product_image import ProductImage
from app.catalog.domain.entities.product_price_option import ProductPriceOption
from app.catalog.domain.entities.product_sync import ProductChangeKind
from app.catalog.domain.value_objects.money import Money
from app.catalog.domain.value_objects.product_availability import ProductAvailability
from app.catalog.infrastructure.persistence.models import CategoryModel  # noqa: F401
from app.catalog.infrastructure.persistence.sqlalchemy_product_repository import (
    SqlAlchemyProductRepository,
)
from app.ingestion.infrastructure.persistence.models import (  # noqa: F401
    CatalogSyncExecutionModel,
)
from app.shared.infrastructure.database.base import Base
from app.shared.infrastructure.database.session import create_session_factory
from sqlalchemy.ext.asyncio import create_async_engine


class SqlAlchemyProductRepositoryTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.repository = SqlAlchemyProductRepository(create_session_factory(self.engine))
        self.now = datetime(2026, 7, 26, 16, 0, tzinfo=UTC)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    def product(
        self,
        *,
        product_id: str = "00000000-0000-0000-0000-000000000001",
        name: str = "Bolo artesanal",
        amount: str = "10",
        synced_at: datetime | None = None,
    ) -> Product:
        at = synced_at or self.now
        return Product(
            id=UUID(product_id),
            external_id="external-product-1",
            name=name,
            description="Descrição",
            category_external_id="category-1",
            subcategory_external_id=None,
            is_active=True,
            availability=ProductAvailability.AVAILABLE,
            price_options=(
                ProductPriceOption(
                    external_id="price-1",
                    label="1 unidade",
                    quantity=Decimal("1"),
                    unit="UN",
                    price=Money(Decimal(amount), None),
                    is_default=True,
                ),
            ),
            images=(
                ProductImage(
                    source_url="https://cdn.example.com/product.png",
                    position=0,
                    is_primary=True,
                ),
            ),
            created_at=at,
            updated_at=at,
            last_synced_at=at,
        )

    async def test_round_trip_relations_and_list(self) -> None:
        product = self.product()

        await self.repository.upsert(product)
        stored = await self.repository.get_by_id(product.id)
        listed = await self.repository.list(limit=10, offset=0)

        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.external_id, product.external_id)
        self.assertEqual(stored.price_options[0].price.amount, Decimal("10.00"))
        self.assertEqual(stored.images[0].source_url, product.images[0].source_url)
        self.assertEqual([item.id for item in listed], [product.id])

    async def test_upsert_updates_without_duplicating_and_preserves_local_id(self) -> None:
        original = self.product()
        await self.repository.upsert(original)
        incoming = self.product(
            product_id="00000000-0000-0000-0000-000000000002",
            name="Bolo atualizado",
            amount="15",
            synced_at=self.now + timedelta(hours=1),
        )

        updated = await self.repository.upsert(incoming)
        listed = await self.repository.list(limit=10, offset=0)

        self.assertEqual(updated.id, original.id)
        self.assertEqual(updated.name, "Bolo atualizado")
        self.assertEqual(updated.price_options[0].price.amount, Decimal("15.00"))
        self.assertEqual(len(listed), 1)

    async def test_incremental_upsert_classifies_created_unchanged_and_updated(self) -> None:
        original = self.product()
        created = await self.repository.upsert_incremental(original)
        repeated = await self.repository.upsert_incremental(
            self.product(
                product_id="00000000-0000-0000-0000-000000000002",
                synced_at=self.now + timedelta(hours=1),
            )
        )
        changed = await self.repository.upsert_incremental(
            self.product(
                product_id="00000000-0000-0000-0000-000000000003",
                amount="15",
                synced_at=self.now + timedelta(hours=2),
            )
        )

        self.assertEqual(created.change, ProductChangeKind.CREATED)
        self.assertEqual(repeated.change, ProductChangeKind.UNCHANGED)
        self.assertEqual(changed.change, ProductChangeKind.UPDATED)
        self.assertEqual(changed.previous_fingerprint, repeated.current_fingerprint)
        self.assertNotEqual(changed.previous_fingerprint, changed.current_fingerprint)
        self.assertEqual(len(await self.repository.list(limit=10, offset=0)), 1)

    async def test_upsert_honors_persisted_field_protection(self) -> None:
        original = self.product()
        original.protect(ProductProtectedField.NAME)
        await self.repository.upsert(original)
        incoming = self.product(
            product_id="00000000-0000-0000-0000-000000000002",
            name="Nome vindo da origem",
            amount="20",
        )

        await self.repository.upsert(incoming)
        stored = await self.repository.get_by_external_id(original.external_id)

        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.name, "Bolo artesanal")
        self.assertEqual(stored.price_options[0].price.amount, Decimal("20.00"))
        self.assertIn(ProductProtectedField.NAME, stored.protected_fields)

    async def test_transaction_rolls_back_partial_update(self) -> None:
        original = self.product()
        await self.repository.upsert(original)
        incoming = self.product(
            product_id="00000000-0000-0000-0000-000000000002",
            name="Não deve persistir",
            amount="99",
        )

        def fail_after_partial_change(model, product) -> None:
            del product
            model.name = "alteração parcial"
            raise RuntimeError("falha simulada")

        with (
            patch(
                "app.catalog.infrastructure.persistence."
                "sqlalchemy_product_repository.update_product_model",
                side_effect=fail_after_partial_change,
            ),
            self.assertRaises(RuntimeError),
        ):
            await self.repository.upsert(incoming)

        stored = await self.repository.get_by_external_id(original.external_id)
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.name, "Bolo artesanal")
        self.assertEqual(stored.price_options[0].price.amount, Decimal("10.00"))
