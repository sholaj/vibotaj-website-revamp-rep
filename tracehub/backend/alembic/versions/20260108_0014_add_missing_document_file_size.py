"""Ensure documents.file_size column exists

Revision ID: 004
Revises: 003
Create Date: 2026-01-08
Revision ID: 014
Revises: 013
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
revision: str = '014'
down_revision: Union[str, None] = '013'


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
