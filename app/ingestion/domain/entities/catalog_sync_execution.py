"""Lifecycle and counters for one catalog synchronization execution."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class CatalogSyncStatus(StrEnum):
    """Possible terminal and non-terminal states of a synchronization."""

    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CatalogSyncItemFailure:
    """Failure of a single item that must not abort the remaining batch."""

    item_reference: str
    code: str
    message: str


@dataclass(slots=True)
class CatalogSyncExecution:
    """Aggregate that records the observable result of a catalog synchronization."""

    id: str
    correlation_id: str
    started_at: datetime
    reprocess_of: str | None = None
    status: CatalogSyncStatus = CatalogSyncStatus.RUNNING
    finished_at: datetime | None = None
    received_count: int = 0
    processed_count: int = 0
    failed_count: int = 0
    failure_message: str | None = None
    failures: list[CatalogSyncItemFailure] = field(default_factory=list)

    @property
    def is_running(self) -> bool:
        return self.status is CatalogSyncStatus.RUNNING

    def register_received(self, count: int) -> None:
        self._ensure_running()
        if count < 0:
            raise ValueError("A quantidade recebida não pode ser negativa.")
        self.received_count += count

    def register_processed(self) -> None:
        self._ensure_running()
        self.processed_count += 1

    def register_item_failure(self, failure: CatalogSyncItemFailure) -> None:
        self._ensure_running()
        self.failed_count += 1
        self.failures.append(failure)

    def complete(self, finished_at: datetime) -> None:
        self._ensure_running()
        self.finished_at = finished_at
        self.status = (
            CatalogSyncStatus.COMPLETED_WITH_FAILURES
            if self.failed_count
            else CatalogSyncStatus.COMPLETED
        )

    def fail(self, finished_at: datetime, message: str) -> None:
        self._ensure_running()
        self.finished_at = finished_at
        self.failure_message = message
        self.status = CatalogSyncStatus.FAILED

    def _ensure_running(self) -> None:
        if not self.is_running:
            raise RuntimeError("A execução de sincronização já foi finalizada.")
