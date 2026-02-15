"""Delete user shola.jibodu@gmail.com from Hages organization.

This migration removes the user shola.jibodu@gmail.com from the Hages organization
in both production and staging environments. The user was created outside of the
seed data and needs to be removed.

Revision ID: 20260120_0002
Revises: 20260120_0001
Create Date: 2026-01-20
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260120_0002"
down_revision = "20260120_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Delete user shola.jibodu@gmail.com from Hages organization.
    
    This migration:
    1. Finds the user by email in the Hages organization
    2. Deletes organization memberships for this user
    3. Permanently deletes the user record
    
    The migration is idempotent - it will succeed even if the user doesn't exist.
    """
    # Get database connection
    conn = op.get_bind()
    
    # Find the Hages organization ID
    result = conn.execute(sa.text(
        "SELECT id FROM organizations WHERE slug = 'hages' LIMIT 1"
    ))
    hages_org = result.fetchone()
    
    if not hages_org:
        print("Hages organization not found - skipping user deletion")
        return
    
    hages_org_id = hages_org[0]
    
    # Find the user by email in Hages organization
    result = conn.execute(sa.text(
        "SELECT id FROM users WHERE email = :email AND organization_id = :org_id LIMIT 1"
    ), {"email": "shola.jibodu@gmail.com", "org_id": hages_org_id})
    user = result.fetchone()
    
    if not user:
        print("User shola.jibodu@gmail.com not found in Hages organization - skipping")
        return
    
    user_id = user[0]
    print(f"Found user shola.jibodu@gmail.com with ID: {user_id}")
    
    # Step 1: Nullify foreign key references in invitations table
    result = conn.execute(sa.text(
        "UPDATE invitations SET created_by = NULL WHERE created_by = :user_id"
    ), {"user_id": user_id})
    print(f"Nullified created_by in {result.rowcount} invitation(s)")
    
    result = conn.execute(sa.text(
        "UPDATE invitations SET accepted_by = NULL WHERE accepted_by = :user_id"
    ), {"user_id": user_id})
    print(f"Nullified accepted_by in {result.rowcount} invitation(s)")
    
    # Step 2: Nullify foreign key references in documents table
    result = conn.execute(sa.text(
        "UPDATE documents SET validated_by = NULL WHERE validated_by = :user_id"
    ), {"user_id": user_id})
    print(f"Nullified validated_by in {result.rowcount} document(s)")
    
    # Step 3: Nullify foreign key references in document_contents table
    result = conn.execute(sa.text(
        "UPDATE document_contents SET validated_by = NULL WHERE validated_by = :user_id"
    ), {"user_id": user_id})
    print(f"Nullified validated_by in {result.rowcount} document_content(s)")
    
    # Step 4: Nullify foreign key references in document_issues table
    result = conn.execute(sa.text(
        "UPDATE document_issues SET overridden_by = NULL WHERE overridden_by = :user_id"
    ), {"user_id": user_id})
    print(f"Nullified overridden_by in {result.rowcount} document_issue(s)")
    
    # Step 5: Nullify foreign key references in origins table
    result = conn.execute(sa.text(
        "UPDATE origins SET verified_by = NULL WHERE verified_by = :user_id"
    ), {"user_id": user_id})
    print(f"Nullified verified_by in {result.rowcount} origin(s)")
    
    # Step 6: Nullify foreign key references in users table (deleted_by)
    result = conn.execute(sa.text(
        "UPDATE users SET deleted_by = NULL WHERE deleted_by = :user_id"
    ), {"user_id": user_id})
    print(f"Nullified deleted_by in {result.rowcount} user(s)")
    
    # Step 7: Delete organization memberships for this user
    result = conn.execute(sa.text(
        "DELETE FROM organization_memberships WHERE user_id = :user_id"
    ), {"user_id": user_id})
    print(f"Deleted {result.rowcount} organization membership(s)")
    
    # Step 8: Delete notifications for this user (if any)
    result = conn.execute(sa.text(
        "DELETE FROM notifications WHERE user_id = :user_id"
    ), {"user_id": user_id})
    print(f"Deleted {result.rowcount} notification(s)")
    
    # Step 9: Anonymize audit log references to this user
    result = conn.execute(sa.text(
        "UPDATE audit_logs SET username = '[deleted]', user_id = NULL WHERE user_id = :user_id"
    ), {"user_id": user_id})
    print(f"Anonymized {result.rowcount} audit log(s)")
    
    # Step 10: Delete the user
    result = conn.execute(sa.text(
        "DELETE FROM users WHERE id = :user_id"
    ), {"user_id": user_id})
    print(f"Deleted user shola.jibodu@gmail.com")


def downgrade() -> None:
    """This migration cannot be reversed automatically.
    
    If you need to restore the user, you must manually create them through
    the application UI or seed data.
    """
    print("WARNING: This migration cannot be automatically reversed.")
    print("To restore the user, manually create them through the application.")
    pass
