"""Tests for the complete catalog synchronization orchestration."""

import asyncio
import unittest
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from app.catalog.application.usecases.build_product_from_import import (
    BuildProductFromImportUseCase,
)
from app.ingestion.application.dto.catalog_sync import StartCatalogSyncCommand
from app.ingestion.application.dto.external_product_page import (
    ExternalProductPage,
    ProductFilters,
    ProductPageRequest,
)
from app.ingestion.application.exceptions import (
    CatalogSyncAlreadyRunningError,
    CatalogSyncExecutionNotFoundError,
    CatalogSyncFailedError,
)
from app.ingestion.application.ports.product_source import ProductSource
from app.ingestion.application.usecases.normalize_product import NormalizeProductUseCase
from app.ingestion.application.usecases.start_catalog_sync import StartCatalogSyncUseCase
from app.ingestion.domain.entities.catalog_sync_execution import CatalogSyncStatus
from app.ingestion.infrastructure.persistence.in_memory_catalog_sync_repository import (
    InMemoryCatalogSyncExecutionRepository,
)
from app.ingestion.infrastructure.pipeline.product_pipeline_processor import (
    ProductPipelineProcessor,
)

from tests.fixtures.fake_product_source import FakeProductSource
from tests.fixtures.in_memory_product_repository import InMemoryProductRepository


def product_payload(product_id: str) -> dict[str, object]:
    return {
        "id": product_id,
        "name": f"Produto {product_id}",
        "description": None,
        "image": None,
        "categoryId": "category-1",
        "subcategoryId": None,
        "isActive": True,
        "priceOptions": [
            {
                "id": f"price-{product_id}",
                "label": "1 unid.",
                "quantity": 1,
                "unit": "UN",
                "price": 10,
                "isDefault": True,
            }
        ],
    }


def page(number: int, *items: dict[str, object]) -> ExternalProductPage:
    request = ProductPageRequest(page=number, limit=2)
    return ExternalProductPage(
        items=items,
        request=request,
        has_more=False,
        next_request=None,
        total=len(items),
    )


class FailingProductSource(ProductSource):
    async def fetch_page(
        self,
        request: ProductPageRequest,
        correlation_id: str | None = None,
    ) -> ExternalProductPage:
        del request, correlation_id
        raise ConnectionError("Fonte indisponível.")

    async def iter_pages(
        self,
        filters: ProductFilters | None = None,
        correlation_id: str | None = None,
    ) -> AsyncIterator[ExternalProductPage]:
        del filters, correlation_id
        raise ConnectionError("Fonte indisponível.")
        yield


class BlockingProductSource(ProductSource):
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def fetch_page(
        self,
        request: ProductPageRequest,
        correlation_id: str | None = None,
    ) -> ExternalProductPage:
        del request, correlation_id
        return page(1, product_payload("product-1"))

    async def iter_pages(
        self,
        filters: ProductFilters | None = None,
        correlation_id: str | None = None,
    ) -> AsyncIterator[ExternalProductPage]:
        del filters, correlation_id
        self.started.set()
        await self.release.wait()
        yield page(1, product_payload("product-1"))


class StartCatalogSyncUseCaseTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = InMemoryCatalogSyncExecutionRepository()
        self.times = iter(
            [
                datetime(2026, 7, 26, 12, 0, tzinfo=UTC),
                datetime(2026, 7, 26, 12, 0, tzinfo=UTC) + timedelta(seconds=1),
                datetime(2026, 7, 26, 12, 0, tzinfo=UTC) + timedelta(seconds=2),
            ]
        )

    def build_use_case(self, source: ProductSource) -> StartCatalogSyncUseCase:
        return StartCatalogSyncUseCase(
            source,
            ProductPipelineProcessor(
                NormalizeProductUseCase(),
                BuildProductFromImportUseCase(),
                InMemoryProductRepository(),
            ),
            self.repository,
            clock=lambda: next(self.times),
            id_factory=lambda: "sync-1",
        )

    async def test_processes_every_page_and_records_a_complete_execution(self) -> None:
        source = FakeProductSource(
            [
                page(1, product_payload("product-1"), product_payload("product-2")),
                page(2, product_payload("product-3")),
            ]
        )

        result = await self.build_use_case(source).execute(StartCatalogSyncCommand())

        self.assertEqual(result.status, CatalogSyncStatus.COMPLETED)
        self.assertEqual(result.received_count, 3)
        self.assertEqual(result.processed_count, 3)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(source.correlation_ids, ["sync-1"])

    async def test_isolates_invalid_product_and_keeps_the_remaining_batch(self) -> None:
        invalid = product_payload("product-invalid")
        invalid.pop("priceOptions")
        source = FakeProductSource(
            [page(1, product_payload("product-1"), invalid, product_payload("product-3"))]
        )

        result = await self.build_use_case(source).execute(StartCatalogSyncCommand())

        self.assertEqual(result.status, CatalogSyncStatus.COMPLETED_WITH_FAILURES)
        self.assertEqual(result.received_count, 3)
        self.assertEqual(result.processed_count, 2)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.failures[0].item_reference, "product-invalid")

    async def test_records_normalization_rejection_without_stopping_the_batch(self) -> None:
        blank_name = product_payload("product-blank")
        blank_name["name"] = " \n "
        source = FakeProductSource([page(1, blank_name, product_payload("product-valid"))])

        result = await self.build_use_case(source).execute(StartCatalogSyncCommand())

        self.assertEqual(result.processed_count, 1)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.failures[0].item_reference, "product-blank")
        self.assertEqual(result.failures[0].code, "PRODUCT_NORMALIZATION_ERROR")

    async def test_rejects_a_concurrent_execution(self) -> None:
        source = BlockingProductSource()
        use_case = self.build_use_case(source)
        first = asyncio.create_task(use_case.execute(StartCatalogSyncCommand()))
        await source.started.wait()

        with self.assertRaises(CatalogSyncAlreadyRunningError):
            await use_case.execute(StartCatalogSyncCommand())

        source.release.set()
        result = await first
        self.assertEqual(result.status, CatalogSyncStatus.COMPLETED)

    async def test_reprocesses_a_previous_execution_as_a_new_run(self) -> None:
        source = FakeProductSource([page(1, product_payload("product-1"))])
        ids = iter(["sync-1", "sync-2"])
        times = iter(
            [
                datetime(2026, 7, 26, 12, 0, tzinfo=UTC),
                datetime(2026, 7, 26, 12, 1, tzinfo=UTC),
                datetime(2026, 7, 26, 13, 0, tzinfo=UTC),
                datetime(2026, 7, 26, 13, 1, tzinfo=UTC),
            ]
        )
        use_case = StartCatalogSyncUseCase(
            source,
            ProductPipelineProcessor(
                NormalizeProductUseCase(),
                BuildProductFromImportUseCase(),
                InMemoryProductRepository(),
            ),
            self.repository,
            clock=lambda: next(times),
            id_factory=lambda: next(ids),
        )
        first = await use_case.execute(StartCatalogSyncCommand())

        repeated = await use_case.execute(
            StartCatalogSyncCommand(reprocess_execution_id=first.execution_id)
        )

        self.assertEqual(repeated.execution_id, "sync-2")
        self.assertEqual(repeated.reprocess_of, "sync-1")
        self.assertEqual(repeated.status, CatalogSyncStatus.COMPLETED)

    async def test_rejects_reprocessing_an_unknown_execution(self) -> None:
        source = FakeProductSource([])

        with self.assertRaises(CatalogSyncExecutionNotFoundError):
            await self.build_use_case(source).execute(
                StartCatalogSyncCommand(reprocess_execution_id="missing")
            )

    async def test_records_source_failure_before_raising(self) -> None:
        use_case = self.build_use_case(FailingProductSource())

        with self.assertRaises(CatalogSyncFailedError) as context:
            await use_case.execute(StartCatalogSyncCommand())

        execution = await self.repository.get(context.exception.execution_id)
        self.assertIsNotNone(execution)
        assert execution is not None
        self.assertEqual(execution.status, CatalogSyncStatus.FAILED)
        self.assertEqual(execution.failure_message, "Fonte indisponível.")
