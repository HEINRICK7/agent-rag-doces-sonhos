"""End-to-end application pipeline from external page to durable catalog."""

import unittest
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.catalog.application.usecases.build_product_from_import import (
    BuildProductFromImportUseCase,
)
from app.catalog.infrastructure.persistence.models import ProductModel  # noqa: F401
from app.catalog.infrastructure.persistence.sqlalchemy_product_repository import (
    SqlAlchemyProductRepository,
)
from app.ingestion.application.dto.catalog_sync import StartCatalogSyncCommand
from app.ingestion.application.dto.external_product_page import (
    ExternalProductPage,
    ProductPageRequest,
)
from app.ingestion.application.usecases.normalize_product import NormalizeProductUseCase
from app.ingestion.application.usecases.start_catalog_sync import StartCatalogSyncUseCase
from app.ingestion.domain.entities.catalog_sync_execution import CatalogSyncStatus
from app.ingestion.infrastructure.persistence.sqlalchemy_catalog_sync_repository import (
    SqlAlchemyCatalogSyncExecutionRepository,
)
from app.ingestion.infrastructure.pipeline.product_pipeline_processor import (
    ProductPipelineProcessor,
)
from app.shared.infrastructure.database.base import Base
from app.shared.infrastructure.database.session import create_session_factory
from sqlalchemy.ext.asyncio import create_async_engine

from tests.fixtures.fake_product_source import FakeProductSource


class DurableCatalogPipelineTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.session_factory = create_session_factory(self.engine)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_external_product_reaches_product_and_execution_tables(self) -> None:
        started_at = datetime(2026, 7, 26, 16, 0, tzinfo=UTC)
        finished_at = started_at + timedelta(seconds=2)
        times = iter((started_at, finished_at))
        page = ExternalProductPage(
            items=(
                {
                    "id": "external-product-1",
                    "name": "Bolo artesanal",
                    "description": None,
                    "image": "https://cdn.example.com/product.png",
                    "categoryId": "category-1",
                    "subcategoryId": None,
                    "isActive": True,
                    "priceOptions": [
                        {
                            "id": "price-1",
                            "label": "1 unidade",
                            "quantity": 1,
                            "unit": "UN",
                            "price": 10,
                            "isDefault": True,
                        }
                    ],
                },
            ),
            request=ProductPageRequest(page=1),
            has_more=False,
            next_request=None,
            total=1,
        )
        products = SqlAlchemyProductRepository(self.session_factory)
        executions = SqlAlchemyCatalogSyncExecutionRepository(self.session_factory)
        processor = ProductPipelineProcessor(
            NormalizeProductUseCase(),
            BuildProductFromImportUseCase(
                clock=lambda: started_at,
                id_factory=lambda: UUID("00000000-0000-0000-0000-000000000001"),
            ),
            products,
        )
        use_case = StartCatalogSyncUseCase(
            FakeProductSource([page]),
            processor,
            executions,
            clock=lambda: next(times),
            id_factory=lambda: "sync-1",
        )

        result = await use_case.execute(StartCatalogSyncCommand())
        stored_product = await products.get_by_external_id("external-product-1")
        stored_execution = await executions.get("sync-1")

        self.assertEqual(result.status, CatalogSyncStatus.COMPLETED)
        self.assertIsNotNone(stored_product)
        self.assertIsNotNone(stored_execution)
        assert stored_product is not None
        assert stored_execution is not None
        self.assertEqual(stored_product.name, "Bolo artesanal")
        self.assertEqual(stored_product.description, "Descrição não informada.")
        self.assertEqual(stored_execution.processed_count, 1)
