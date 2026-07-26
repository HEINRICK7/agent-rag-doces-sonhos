"""Input and output contracts for catalog synchronization."""

from dataclasses import dataclass
from datetime import datetime

from app.ingestion.application.dto.external_product_page import ProductFilters
from app.ingestion.domain.entities.catalog_sync_execution import (
    CatalogSyncChange,
    CatalogSyncExecution,
    CatalogSyncItemFailure,
    CatalogSyncStatus,
)


@dataclass(frozen=True, slots=True)
class StartCatalogSyncCommand:
    """Parameters accepted when starting or repeating a synchronization."""

    filters: ProductFilters = ProductFilters()
    correlation_id: str | None = None
    reprocess_execution_id: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogSyncResult:
    """Stable application output detached from the mutable execution entity."""

    execution_id: str
    correlation_id: str
    status: CatalogSyncStatus
    started_at: datetime
    finished_at: datetime | None
    received_count: int
    processed_count: int
    failed_count: int
    reprocess_of: str | None
    failure_message: str | None
    failures: tuple[CatalogSyncItemFailure, ...]
    created_count: int
    updated_count: int
    unchanged_count: int
    changes: tuple[CatalogSyncChange, ...]

    @classmethod
    def from_execution(cls, execution: CatalogSyncExecution) -> "CatalogSyncResult":
        return cls(
            execution_id=execution.id,
            correlation_id=execution.correlation_id,
            status=execution.status,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            received_count=execution.received_count,
            processed_count=execution.processed_count,
            failed_count=execution.failed_count,
            reprocess_of=execution.reprocess_of,
            failure_message=execution.failure_message,
            failures=tuple(execution.failures),
            created_count=execution.created_count,
            updated_count=execution.updated_count,
            unchanged_count=execution.unchanged_count,
            changes=tuple(execution.changes),
        )
