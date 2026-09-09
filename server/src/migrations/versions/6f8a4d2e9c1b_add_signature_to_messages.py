"""Add signature column to dialog_messages and group_messages

Revision ID: 6f8a4d2e9c1b
Revises: e390370c9223
Create Date: 2026-09-09 13:00:00.000000

Adds the `signature` BYTEA column to both message tables. Nullable so
pre-existing rows (written before the column existed) round-trip
cleanly as `signature: null`.

The column is set on the abstract `basic_messages` SQLAlchemy model
and inherits down to `dialog_messages` and `group_messages`. We
issue one ALTER per concrete table here.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6f8a4d2e9c1b"
down_revision: str | None = "e390370c9223"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add `signature` BYTEA column to both message tables."""
    op.add_column(
        "dialog_messages",
        sa.Column("signature", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "group_messages",
        sa.Column("signature", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    """Drop `signature` column from both message tables."""
    op.drop_column("group_messages", "signature")
    op.drop_column("dialog_messages", "signature")
