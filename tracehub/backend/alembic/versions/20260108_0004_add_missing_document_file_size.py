"""Ensure documents.file_size column exists

Revision ID: 004
Revises: 003
Create Date: 2026-01-08

Adds documents.file_size if missing to reconcile schema drift observed on staging.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'documents' AND column_name = 'file_size'
            ) THEN
                ALTER TABLE documents ADD COLUMN file_size integer;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # Safe no-op: don't drop the column automatically
    pass
