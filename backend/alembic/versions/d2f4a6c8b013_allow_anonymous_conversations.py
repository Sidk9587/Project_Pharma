"""Allow conversations before authentication is implemented.

Revision ID: d2f4a6c8b013
Revises: b7a14d9c2e31
"""

from alembic import op
import sqlalchemy as sa


revision = "d2f4a6c8b013"
down_revision = "b7a14d9c2e31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "conversations",
        "user_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    connection = op.get_bind()
    null_owner_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM conversations WHERE user_id IS NULL")
    ).scalar_one()
    if null_owner_count:
        raise RuntimeError(
            "Cannot restore conversations.user_id NOT NULL while anonymous "
            f"conversations exist ({null_owner_count}); assign owners first."
        )
    op.alter_column(
        "conversations",
        "user_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
