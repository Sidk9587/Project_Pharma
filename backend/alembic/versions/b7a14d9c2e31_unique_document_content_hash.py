"""Enforce unique document content hashes.

Revision ID: b7a14d9c2e31
Revises: 8c59da422fab
"""

from alembic import op
import sqlalchemy as sa


revision = "b7a14d9c2e31"
down_revision = "8c59da422fab"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    duplicates = connection.execute(
        sa.text(
            "SELECT content_hash, COUNT(*) AS row_count "
            "FROM documents WHERE content_hash IS NOT NULL "
            "GROUP BY content_hash HAVING COUNT(*) > 1"
        )
    ).all()
    if duplicates:
        details = ", ".join(
            f"{content_hash} ({count} rows)"
            for content_hash, count in duplicates
        )
        raise RuntimeError(
            "Cannot enforce unique document hashes; resolve these duplicate "
            f"content_hash values while preserving required records: {details}"
        )

    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.create_index(
        "ix_documents_content_hash",
        "documents",
        ["content_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.create_index(
        "ix_documents_content_hash",
        "documents",
        ["content_hash"],
        unique=False,
    )
