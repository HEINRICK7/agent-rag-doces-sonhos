"""Durable synchronization execution repository with an atomic active slot."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.ingestion.application.ports.catalog_sync_repository import (
    CatalogSyncExecutionRepository,
)
from app.ingestion.domain.entities.catalog_sync_execution import (
    CatalogSyncChange,
    CatalogSyncExecution,
    CatalogSyncItemFailure,
    CatalogSyncStatus,
)
from app.ingestion.infrastructure.persistence.models import (
    CatalogSyncChangeModel,
    CatalogSyncErrorModel,
    CatalogSyncExecutionModel,
)


class SqlAlchemyCatalogSyncExecutionRepository(CatalogSyncExecutionRepository):
    """Persist executions while a unique nullable slot prevents concurrency."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def acquire(self, execution: CatalogSyncExecution) -> bool:
        try:
            async with self._session_factory() as session, session.begin():
                session.add(_to_model(execution))
                await session.flush()
            return True
        except IntegrityError:
            return False

    async def save(self, execution: CatalogSyncExecution) -> None:
        async with self._session_factory() as session, session.begin():
            model = await session.get(
                CatalogSyncExecutionModel,
                execution.id,
                options=(
                    selectinload(CatalogSyncExecutionModel.failures),
                    selectinload(CatalogSyncExecutionModel.changes),
                ),
            )
            if model is None:
                session.add(_to_model(execution))
                return
            _update_model(model, execution)
            await session.flush()

    async def get(self, execution_id: str) -> CatalogSyncExecution | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(CatalogSyncExecutionModel)
                .options(
                    selectinload(CatalogSyncExecutionModel.failures),
                    selectinload(CatalogSyncExecutionModel.changes),
                )
                .where(CatalogSyncExecutionModel.id == execution_id)
            )
            model = result.scalar_one_or_none()
            return _to_domain(model) if model is not None else None


def _to_model(execution: CatalogSyncExecution) -> CatalogSyncExecutionModel:
    model = CatalogSyncExecutionModel(id=execution.id)
    _update_model(model, execution)
    return model


def _update_model(
    model: CatalogSyncExecutionModel,
    execution: CatalogSyncExecution,
) -> None:
    model.correlation_id = execution.correlation_id
    model.reprocess_of = execution.reprocess_of
    model.status = execution.status.value
    model.active_slot = True if execution.is_running else None
    model.started_at = execution.started_at
    model.finished_at = execution.finished_at
    model.received_count = execution.received_count
    model.processed_count = execution.processed_count
    model.failed_count = execution.failed_count
    model.created_count = execution.created_count
    model.updated_count = execution.updated_count
    model.unchanged_count = execution.unchanged_count
    model.failure_message = execution.failure_message
    model.failures = [
        CatalogSyncErrorModel(
            id=uuid4(),
            execution_id=execution.id,
            position=position,
            item_reference=failure.item_reference,
            code=failure.code,
            message=failure.message,
        )
        for position, failure in enumerate(execution.failures)
    ]
    model.changes = [
        CatalogSyncChangeModel(
            id=uuid4(),
            execution_id=execution.id,
            position=position,
            item_reference=change.item_reference,
            kind=change.kind,
            previous_fingerprint=change.previous_fingerprint,
            current_fingerprint=change.current_fingerprint,
        )
        for position, change in enumerate(execution.changes)
    ]


def _to_domain(model: CatalogSyncExecutionModel) -> CatalogSyncExecution:
    return CatalogSyncExecution(
        id=model.id,
        correlation_id=model.correlation_id,
        started_at=_as_utc(model.started_at),
        reprocess_of=model.reprocess_of,
        status=CatalogSyncStatus(model.status),
        finished_at=_as_optional_utc(model.finished_at),
        received_count=model.received_count,
        processed_count=model.processed_count,
        failed_count=model.failed_count,
        created_count=model.created_count,
        updated_count=model.updated_count,
        unchanged_count=model.unchanged_count,
        failure_message=model.failure_message,
        failures=[
            CatalogSyncItemFailure(
                item_reference=failure.item_reference,
                code=failure.code,
                message=failure.message,
            )
            for failure in model.failures
        ],
        changes=[
            CatalogSyncChange(
                item_reference=change.item_reference,
                kind=change.kind,
                previous_fingerprint=change.previous_fingerprint,
                current_fingerprint=change.current_fingerprint,
            )
            for change in model.changes
        ],
    )


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return _as_utc(value) if value is not None else None
