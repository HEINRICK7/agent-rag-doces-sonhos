"""Create catalog and synchronization persistence tables."""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_create_catalog"
down_revision: str | None = "0002_enable_pgvector"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=250), nullable=False),
        sa.Column("icon", sa.String(length=128), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_categories_external_id",
        "categories",
        ["external_id"],
        unique=True,
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category_external_id", sa.String(length=128), nullable=True),
        sa.Column("subcategory_external_id", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("availability", sa.String(length=32), nullable=False),
        sa.Column("protected_fields", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_products_external_id",
        "products",
        ["external_id"],
        unique=True,
    )
    op.create_index(
        "ix_products_category_external_id",
        "products",
        ["category_external_id"],
    )
    op.create_index("ix_products_last_synced_at", "products", ["last_synced_at"])

    op.create_table(
        "product_price_options",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("label", sa.String(length=250), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id", "position"),
    )
    op.create_table(
        "product_images",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id", "position"),
    )
    op.create_table(
        "catalog_sync_executions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("reprocess_of", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("active_slot", sa.Boolean(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_count", sa.Integer(), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["reprocess_of"], ["catalog_sync_executions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("active_slot"),
    )
    op.create_index(
        "ix_catalog_sync_executions_status",
        "catalog_sync_executions",
        ["status"],
    )
    op.create_index(
        "ix_catalog_sync_executions_started_at",
        "catalog_sync_executions",
        ["started_at"],
    )
    op.create_table(
        "catalog_sync_errors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("execution_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("item_reference", sa.String(length=250), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["catalog_sync_executions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("catalog_sync_errors")
    op.drop_index(
        "ix_catalog_sync_executions_started_at",
        table_name="catalog_sync_executions",
    )
    op.drop_index(
        "ix_catalog_sync_executions_status",
        table_name="catalog_sync_executions",
    )
    op.drop_table("catalog_sync_executions")
    op.drop_table("product_images")
    op.drop_table("product_price_options")
    op.drop_index("ix_products_last_synced_at", table_name="products")
    op.drop_index("ix_products_category_external_id", table_name="products")
    op.drop_index("ix_products_external_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_external_id", table_name="categories")
    op.drop_table("categories")
