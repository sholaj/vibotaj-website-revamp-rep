"""Fix document_contents.validated_by type from String to UUID FK.

Sprint 11 - SCHEMA-002: Change validated_by from String(100) to UUID FK.

This migration:
1. Adds a new UUID column (validated_by_uuid)
2. Attempts to migrate existing string data (if valid UUIDs)
3. Drops the old string column
4. Renames the new column
5. Adds FK constraint

Revision ID: 20260111_0003
Revises: 20260111_0002
Create Date: 2026-01-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260111_0003'
down_revision = '20260111_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Change validated_by from String to UUID with FK constraint."""
    # Check if the column type is already UUID (idempotency)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col['name']: col for col in inspector.get_columns('document_contents')}

    if 'validated_by' in columns:
        col_type = str(columns['validated_by']['type'])
        if 'UUID' in col_type.upper():
            # Already migrated
            return

    # 1. Add new UUID column
    op.add_column(
        'document_contents',
        sa.Column('validated_by_uuid', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # 2. Try to migrate existing string data to UUID
    # Only migrates if the string is a valid UUID format
    op.execute("""
        UPDATE document_contents
        SET validated_by_uuid = CASE
            WHEN validated_by IS NOT NULL
                 AND validated_by ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            THEN validated_by::uuid
            ELSE NULL
        END
    """)

    # 3. Drop old string column
    op.drop_column('document_contents', 'validated_by')

    # 4. Rename new column to validated_by
    op.alter_column('document_contents', 'validated_by_uuid', new_column_name='validated_by')

    # 5. Add FK constraint
    op.create_foreign_key(
        'fk_doc_content_validated_by_user',
        'document_contents',
        'users',
        ['validated_by'],
        ['id'],
        ondelete='SET NULL'
    )

    # 6. Also add timezone to validated_at if not already present
    # This is a best-effort migration - PostgreSQL handles this gracefully
    try:
        op.alter_column(
            'document_contents',
            'validated_at',
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=True
        )
    except Exception:
        pass  # Column might already have timezone


def downgrade():
    """Revert validated_by back to String type."""
    # Drop FK constraint
    op.drop_constraint('fk_doc_content_validated_by_user', 'document_contents', type_='foreignkey')

    # Add new string column
    op.add_column(
        'document_contents',
        sa.Column('validated_by_str', sa.String(100), nullable=True)
    )

    # Copy UUID values as strings
    op.execute("""
        UPDATE document_contents
        SET validated_by_str = validated_by::text
        WHERE validated_by IS NOT NULL
    """)

    # Drop UUID column
    op.drop_column('document_contents', 'validated_by')

    # Rename string column
    op.alter_column('document_contents', 'validated_by_str', new_column_name='validated_by')

    # Revert validated_at timezone
    op.alter_column(
        'document_contents',
        'validated_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True
    )
