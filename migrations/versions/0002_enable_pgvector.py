"""Enable the pgvector extension."""

from typing import Sequence

from alembic import op

revision: str = "0002_enable_pgvector"
down_revision: str | None = "0001_create_users"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
