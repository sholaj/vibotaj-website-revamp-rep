"""Change notifications.user_id from String to UUID FK.

Sprint 11 - SCHEMA-001: Migrate user_id from email string to UUID FK.

This migration:
1. Adds a new UUID column (user_id_uuid)
2. Populates it by looking up user UUIDs from email addresses
3. Drops the old string column
4. Renames the new column
5. Adds FK constraint
6. Adds timezone to datetime columns

Note: Existing notifications with user_id not matching any user email
will have user_id_uuid set to NULL and will be deleted (orphaned data).

Revision ID: 20260111_0004
Revises: 20260111_0003
Create Date: 2026-01-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260111_0004'
down_revision = '20260111_0003'
branch_labels = None
depends_on = None


def upgrade():
    """Change notifications.user_id from String(100) to UUID with FK constraint."""
    # Check if column is already UUID (idempotency)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = {col['name']: col for col in inspector.get_columns('notifications')}

    if 'user_id' in columns:
        col_type = str(columns['user_id']['type'])
        if 'UUID' in col_type.upper():
            # Already migrated
            return

    # 1. Add new UUID column
    op.add_column(
        'notifications',
        sa.Column('user_id_uuid', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # 2. Populate from users table by matching email
    # user_id currently stores email address
    op.execute("""
        UPDATE notifications n
        SET user_id_uuid = u.id
        FROM users u
        WHERE LOWER(n.user_id) = LOWER(u.email)
    """)

    # 3. Delete orphaned notifications (where user email doesn't exist)
    op.execute("""
        DELETE FROM notifications
        WHERE user_id_uuid IS NULL
    """)

    # 4. Drop indexes that reference old column
    op.drop_index('ix_notifications_user_read', table_name='notifications')
    op.drop_index('ix_notifications_user_created', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')

    # 5. Drop old string column
    op.drop_column('notifications', 'user_id')

    # 6. Rename new column to user_id
    op.alter_column('notifications', 'user_id_uuid', new_column_name='user_id')

    # 7. Set NOT NULL constraint
    op.alter_column('notifications', 'user_id', nullable=False)

    # 8. Add FK constraint
    op.create_foreign_key(
        'fk_notifications_user',
        'notifications',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # 9. Recreate indexes
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'read'])
    op.create_index('ix_notifications_user_created', 'notifications', ['user_id', 'created_at'])

    # 10. Add timezone to datetime columns
    op.alter_column(
        'notifications',
        'read_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True
    )
    op.alter_column(
        'notifications',
        'created_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False
    )


def downgrade():
    """Revert user_id back to String type."""
    # Drop FK constraint
    op.drop_constraint('fk_notifications_user', 'notifications', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_notifications_user_created', table_name='notifications')
    op.drop_index('ix_notifications_user_read', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')

    # Add new string column
    op.add_column(
        'notifications',
        sa.Column('user_id_str', sa.String(100), nullable=True)
    )

    # Copy UUID values as email strings from users table
    op.execute("""
        UPDATE notifications n
        SET user_id_str = u.email
        FROM users u
        WHERE n.user_id = u.id
    """)

    # Drop UUID column
    op.drop_column('notifications', 'user_id')

    # Rename string column
    op.alter_column('notifications', 'user_id_str', new_column_name='user_id')

    # Set NOT NULL
    op.alter_column('notifications', 'user_id', nullable=False)

    # Recreate indexes
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'read'])
    op.create_index('ix_notifications_user_created', 'notifications', ['user_id', 'created_at'])

    # Revert datetime columns
    op.alter_column(
        'notifications',
        'read_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True
    )
    op.alter_column(
        'notifications',
        'created_at',
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False
    )
