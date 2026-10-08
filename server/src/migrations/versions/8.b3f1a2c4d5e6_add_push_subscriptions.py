"""Add push_subscriptions table for Web Push

Revision ID: b3f1a2c4d5e6
Revises: 7a1b2c3d4e5f
Create Date: 2026-10-08 00:00:00.000000

Stores browser Web Push subscription credentials (endpoint +
encryption keys) per user. The endpoint is globally unique: one
browser subscription belongs to exactly one user. Subscriptions are
removed automatically with the user (CASCADE) and cleaned up when
the push service reports them as gone (HTTP 410/404).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from fastapi_users_db_sqlalchemy.generics import GUID

# revision identifiers, used by Alembic.
revision: str = "b3f1a2c4d5e6"
down_revision: str | None = "7a1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the push_subscriptions table."""
    op.create_table(
        "push_subscriptions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint"),
    )


def downgrade() -> None:
    """Drop the push_subscriptions table."""
    op.drop_table("push_subscriptions")
