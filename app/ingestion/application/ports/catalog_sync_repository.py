"""Persistence boundary for synchronization executions."""

from typing import Protocol

from app.ingestion.domain.entities.catalog_sync_execution import CatalogSyncExecution


class CatalogSyncExecutionRepository(Protocol):
    """Store executions and acquire the single active synchronization slot."""

    async def acquire(self, execution: CatalogSyncExecution) -> bool: ...

    async def save(self, execution: CatalogSyncExecution) -> None: ...

    async def get(self, execution_id: str) -> CatalogSyncExecution | None: ...
