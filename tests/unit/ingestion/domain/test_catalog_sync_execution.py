"""Tests for the synchronization execution lifecycle."""

import unittest
from datetime import UTC, datetime, timedelta

from app.ingestion.domain.entities.catalog_sync_execution import (
    CatalogSyncExecution,
    CatalogSyncItemFailure,
    CatalogSyncStatus,
)


class CatalogSyncExecutionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.started_at = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)
        self.execution = CatalogSyncExecution(
            id="sync-1",
            correlation_id="correlation-1",
            started_at=self.started_at,
        )

    def test_completes_with_counters(self) -> None:
        self.execution.register_received(2)
        self.execution.register_processed()
        self.execution.register_processed()
        finished_at = self.started_at + timedelta(seconds=3)

        self.execution.complete(finished_at)

        self.assertEqual(self.execution.status, CatalogSyncStatus.COMPLETED)
        self.assertEqual(self.execution.received_count, 2)
        self.assertEqual(self.execution.processed_count, 2)
        self.assertEqual(self.execution.finished_at, finished_at)

    def test_completes_batch_even_when_one_item_fails(self) -> None:
        self.execution.register_received(2)
        self.execution.register_processed()
        self.execution.register_item_failure(
            CatalogSyncItemFailure("product-2", "INVALID", "Produto inválido.")
        )

        self.execution.complete(self.started_at + timedelta(seconds=1))

        self.assertEqual(self.execution.status, CatalogSyncStatus.COMPLETED_WITH_FAILURES)
        self.assertEqual(self.execution.failed_count, 1)
        self.assertEqual(self.execution.failures[0].item_reference, "product-2")

    def test_rejects_changes_after_finishing(self) -> None:
        self.execution.complete(self.started_at)

        with self.assertRaises(RuntimeError):
            self.execution.register_processed()
