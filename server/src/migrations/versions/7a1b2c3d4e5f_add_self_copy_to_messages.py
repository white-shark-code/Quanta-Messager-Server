"""Add sender self-copy columns to dialog_messages and group_messages

Revision ID: 7a1b2c3d4e5f
Revises: 6f8a4d2e9c1b
Create Date: 2026-09-29 00:00:00.000000

Adds `encrypted_message_self` BYTEA and `signature_self` BYTEA to
both message tables. The self-copy holds the same plaintext encrypted
to the sender's own key so the sender (and their other devices
sharing the keypair) can decrypt what they sent — the main
`encrypted_message` is readable only by the peer.

Both columns are NOT NULL: there is no production yet, so no
backfill for pre-existing rows is provided. Recreate dev/test
databases instead of upgrading through this revision when old
message rows exist (the ALTER will fail on them by design).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a1b2c3d4e5f"
down_revision: str | None = "6f8a4d2e9c1b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add self-copy BYTEA columns to both message tables."""
    op.add_column(
        "dialog_messages",
        sa.Column("encrypted_message_self", sa.LargeBinary(), nullable=False),
    )
    op.add_column(
        "dialog_messages",
        sa.Column("signature_self", sa.LargeBinary(), nullable=False),
    )
    op.add_column(
        "group_messages",
        sa.Column("encrypted_message_self", sa.LargeBinary(), nullable=False),
    )
    op.add_column(
        "group_messages",
        sa.Column("signature_self", sa.LargeBinary(), nullable=False),
    )


def downgrade() -> None:
    """Drop self-copy columns from both message tables."""
    op.drop_column("group_messages", "signature_self")
    op.drop_column("group_messages", "encrypted_message_self")
    op.drop_column("dialog_messages", "signature_self")
    op.drop_column("dialog_messages", "encrypted_message_self")
