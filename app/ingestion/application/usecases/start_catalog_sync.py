"""Orchestrate a complete, observable catalog synchronization."""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from uuid import uuid4

from app.ingestion.application.dto.catalog_sync import CatalogSyncResult, StartCatalogSyncCommand
from app.ingestion.application.exceptions import (
    CatalogSyncAlreadyRunningError,
    CatalogSyncExecutionNotFoundError,
    CatalogSyncFailedError,
)
from app.ingestion.application.ports.catalog_item_processor import CatalogItemProcessor
from app.ingestion.application.ports.catalog_sync_repository import (
    CatalogSyncExecutionRepository,
)
from app.ingestion.application.ports.product_source import ProductSource
from app.ingestion.domain.entities.catalog_sync_execution import (
    CatalogSyncExecution,
    CatalogSyncItemFailure,
)

Clock = Callable[[], datetime]
IdFactory = Callable[[], str]


class StartCatalogSyncUseCase:
    """Traverse all pages while isolating failures to their individual products."""

    def __init__(
        self,
        source: ProductSource,
        processor: CatalogItemProcessor,
        executions: CatalogSyncExecutionRepository,
        *,
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._source = source
        self._processor = processor
        self._executions = executions
        self._clock = clock or _utc_now
        self._id_factory = id_factory or _new_id

    async def execute(self, command: StartCatalogSyncCommand) -> CatalogSyncResult:
        if command.reprocess_execution_id is not None:
            previous = await self._executions.get(command.reprocess_execution_id)
            if previous is None:
                raise CatalogSyncExecutionNotFoundError(command.reprocess_execution_id)

        execution_id = self._id_factory()
        correlation_id = command.correlation_id or execution_id
        execution = CatalogSyncExecution(
            id=execution_id,
            correlation_id=correlation_id,
            started_at=self._clock(),
            reprocess_of=command.reprocess_execution_id,
        )
        if not await self._executions.acquire(execution):
            raise CatalogSyncAlreadyRunningError()

        try:
            async for page in self._source.iter_pages(command.filters, correlation_id):
                execution.register_received(len(page.items))
                for payload in page.items:
                    await self._process_item(execution, payload)
                await self._executions.save(execution)
        except Exception as error:
            execution.fail(self._clock(), str(error))
            await self._executions.save(execution)
            raise CatalogSyncFailedError(execution.id) from error

        execution.complete(self._clock())
        await self._executions.save(execution)
        return CatalogSyncResult.from_execution(execution)

    async def _process_item(
        self,
        execution: CatalogSyncExecution,
        payload: Mapping[str, object],
    ) -> None:
        try:
            await self._processor.process(payload, execution.correlation_id)
        except Exception as error:
            code = getattr(error, "code", type(error).__name__)
            execution.register_item_failure(
                CatalogSyncItemFailure(
                    item_reference=_item_reference(payload, execution.received_count),
                    code=str(code),
                    message=str(error),
                )
            )
        else:
            execution.register_processed()


def _item_reference(payload: Mapping[str, object], fallback_index: int) -> str:
    for field in ("id", "external_id", "slug", "name"):
        value = payload.get(field)
        if value not in (None, ""):
            return str(value)
    return f"item-{fallback_index}"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid4().hex
