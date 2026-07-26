"""Synchronization execution persistence and concurrency tests."""

import unittest
from datetime import UTC, datetime, timedelta

from app.catalog.infrastructure.persistence.models import ProductModel  # noqa: F401
from app.ingestion.domain.entities.catalog_sync_execution import (
    CatalogSyncExecution,
    CatalogSyncItemFailure,
    CatalogSyncStatus,
)
from app.ingestion.infrastructure.persistence.sqlalchemy_catalog_sync_repository import (
    SqlAlchemyCatalogSyncExecutionRepository,
)
from app.shared.infrastructure.database.base import Base
from app.shared.infrastructure.database.session import create_session_factory
from sqlalchemy.ext.asyncio import create_async_engine


class SqlAlchemyCatalogSyncRepositoryTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = create_session_factory(self.engine)
        self.repository = SqlAlchemyCatalogSyncExecutionRepository(factory)
        self.competing_repository = SqlAlchemyCatalogSyncExecutionRepository(factory)
        self.now = datetime(2026, 7, 26, 16, 0, tzinfo=UTC)

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    def execution(self, execution_id: str) -> CatalogSyncExecution:
        return CatalogSyncExecution(
            id=execution_id,
            correlation_id=f"correlation-{execution_id}",
            started_at=self.now,
        )

    async def test_persists_complete_execution_and_item_failures(self) -> None:
        execution = self.execution("sync-1")
        self.assertTrue(await self.repository.acquire(execution))
        execution.register_received(2)
        execution.register_processed()
        execution.register_item_failure(
            CatalogSyncItemFailure("product-2", "INVALID", "Produto inválido.")
        )
        execution.complete(self.now + timedelta(seconds=2))

        await self.repository.save(execution)
        stored = await self.repository.get(execution.id)

        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.status, CatalogSyncStatus.COMPLETED_WITH_FAILURES)
        self.assertEqual(stored.received_count, 2)
        self.assertEqual(stored.failed_count, 1)
        self.assertEqual(stored.failures[0].item_reference, "product-2")
        self.assertEqual(stored.finished_at, self.now + timedelta(seconds=2))

    async def test_active_slot_is_atomic_and_released_on_completion(self) -> None:
        first = self.execution("sync-1")
        second = self.execution("sync-2")

        self.assertTrue(await self.repository.acquire(first))
        self.assertFalse(await self.competing_repository.acquire(second))
        first.complete(self.now + timedelta(seconds=1))
        await self.repository.save(first)

        self.assertTrue(await self.competing_repository.acquire(second))
