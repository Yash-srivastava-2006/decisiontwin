"""create datasets table

Revision ID: 20260805_01_create_datasets_table
Revises: 
Create Date: 2026-08-05 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260805_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the datasets table."""
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("total_columns", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False, unique=True),
        sa.Column("columns", sa.JSON(), nullable=False),
        sa.Column("dtypes", sa.JSON(), nullable=False),
        sa.Column("missing_values", sa.JSON(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop the datasets table."""
    op.drop_table("datasets")