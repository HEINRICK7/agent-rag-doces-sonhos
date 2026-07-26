"""Persist product fingerprints and incremental synchronization evidence."""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_incremental_sync_evidence"
down_revision: str | None = "0003_create_catalog"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "source_fingerprint",
            sa.String(length=64),
            nullable=False,
            server_default="legacy",
        ),
    )
    op.add_column(
        "catalog_sync_executions",
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "catalog_sync_executions",
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "catalog_sync_executions",
        sa.Column("unchanged_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "catalog_sync_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("execution_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("item_reference", sa.String(length=250), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("previous_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("current_fingerprint", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["catalog_sync_executions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("catalog_sync_changes")
    op.drop_column("catalog_sync_executions", "unchanged_count")
    op.drop_column("catalog_sync_executions", "updated_count")
    op.drop_column("catalog_sync_executions", "created_count")
    op.drop_column("products", "source_fingerprint")
