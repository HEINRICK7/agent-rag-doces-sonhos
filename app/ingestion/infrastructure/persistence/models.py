"""SQLAlchemy models for catalog synchronization executions and item failures."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.database.base import Base


class CatalogSyncExecutionModel(Base):
    __tablename__ = "catalog_sync_executions"
    __table_args__ = (
        Index("ix_catalog_sync_executions_status", "status"),
        Index("ix_catalog_sync_executions_started_at", "started_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    reprocess_of: Mapped[str | None] = mapped_column(
        ForeignKey("catalog_sync_executions.id"),
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    active_slot: Mapped[bool | None] = mapped_column(Boolean, unique=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_message: Mapped[str | None] = mapped_column(Text)

    failures: Mapped[list[CatalogSyncErrorModel]] = relationship(
        back_populates="execution",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CatalogSyncErrorModel.position",
    )
    changes: Mapped[list[CatalogSyncChangeModel]] = relationship(
        back_populates="execution",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CatalogSyncChangeModel.position",
    )


class CatalogSyncErrorModel(Base):
    __tablename__ = "catalog_sync_errors"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        ForeignKey("catalog_sync_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    item_reference: Mapped[str] = mapped_column(String(250), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    execution: Mapped[CatalogSyncExecutionModel] = relationship(back_populates="failures")


class CatalogSyncChangeModel(Base):
    __tablename__ = "catalog_sync_changes"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        ForeignKey("catalog_sync_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    item_reference: Mapped[str] = mapped_column(String(250), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_fingerprint: Mapped[str | None] = mapped_column(String(64))
    current_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    execution: Mapped[CatalogSyncExecutionModel] = relationship(back_populates="changes")
