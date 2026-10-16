"""Persist source citations with completed assistant messages.

Revision ID: f7c2a19d6e40
Revises: d2f4a6c8b013
"""

from alembic import op
import sqlalchemy as sa

revision = "f7c2a19d6e40"
down_revision = "d2f4a6c8b013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("sources", sa.JSON(), nullable=True))
    op.execute("UPDATE messages SET sources = '[]'::json WHERE sources IS NULL")
    op.alter_column("messages", "sources", nullable=False)


def downgrade() -> None:
    op.drop_column("messages", "sources")
