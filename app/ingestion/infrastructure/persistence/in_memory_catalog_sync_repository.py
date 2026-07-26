"""Process-local synchronization execution repository."""

import asyncio

from app.ingestion.application.ports.catalog_sync_repository import (
    CatalogSyncExecutionRepository,
)
from app.ingestion.domain.entities.catalog_sync_execution import CatalogSyncExecution


class InMemoryCatalogSyncExecutionRepository(CatalogSyncExecutionRepository):
    """Provide atomic concurrency control until durable storage is introduced."""

    def __init__(self) -> None:
        self._executions: dict[str, CatalogSyncExecution] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, execution: CatalogSyncExecution) -> bool:
        async with self._lock:
            if any(candidate.is_running for candidate in self._executions.values()):
                return False
            self._executions[execution.id] = execution
            return True

    async def save(self, execution: CatalogSyncExecution) -> None:
        async with self._lock:
            self._executions[execution.id] = execution

    async def get(self, execution_id: str) -> CatalogSyncExecution | None:
        async with self._lock:
            return self._executions.get(execution_id)
