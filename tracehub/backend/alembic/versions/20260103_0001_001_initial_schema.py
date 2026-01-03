"""Initial schema baseline

Revision ID: 001
Revises:
Create Date: 2026-01-03

This is the baseline migration that captures the existing schema.
Run `alembic stamp head` on existing databases to mark them as current.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for TraceHub initial schema."""

    # Create enum types
    op.execute("CREATE TYPE IF NOT EXISTS userrole AS ENUM ('admin', 'manager', 'operator', 'supplier', 'viewer')")
    op.execute("CREATE TYPE IF NOT EXISTS shipmentstatus AS ENUM ('DRAFT', 'DOCS_PENDING', 'DOCS_COMPLETE', 'IN_TRANSIT', 'ARRIVED', 'CUSTOMS', 'DELIVERED', 'ARCHIVED')")
    op.execute("CREATE TYPE IF NOT EXISTS documenttype AS ENUM ('BILL_OF_LADING', 'COMMERCIAL_INVOICE', 'PACKING_LIST', 'CERTIFICATE_OF_ORIGIN', 'PHYTOSANITARY_CERTIFICATE', 'FUMIGATION_CERTIFICATE', 'INSURANCE_CERTIFICATE', 'CONTRACT', 'CUSTOMS_DECLARATION', 'OTHER')")
    op.execute("CREATE TYPE IF NOT EXISTS documentstatus AS ENUM ('UPLOADED', 'PENDING_VALIDATION', 'VALIDATED', 'REJECTED', 'EXPIRED')")
    op.execute("CREATE TYPE IF NOT EXISTS partytype AS ENUM ('EXPORTER', 'IMPORTER', 'SUPPLIER', 'BUYER', 'SHIPPING_LINE', 'CUSTOMS_AGENT', 'OTHER')")
    op.execute("CREATE TYPE IF NOT EXISTS eventstatus AS ENUM ('BOOKED', 'GATE_IN', 'LOADED', 'DEPARTED', 'IN_TRANSIT', 'TRANSSHIPMENT', 'ARRIVED', 'DISCHARGED', 'GATE_OUT', 'DELIVERED', 'OTHER')")
    op.execute("CREATE TYPE IF NOT EXISTS risklevel AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")
    op.execute("CREATE TYPE IF NOT EXISTS notificationtype AS ENUM ('DOCUMENT_UPLOADED', 'DOCUMENT_VALIDATED', 'DOCUMENT_REJECTED', 'SHIPMENT_CREATED', 'SHIPMENT_STATUS_CHANGED', 'CONTAINER_UPDATE', 'COMPLIANCE_ALERT', 'DEADLINE_REMINDER', 'SYSTEM')")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'manager', 'operator', 'supplier', 'viewer', name='userrole', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create shipments table
    op.create_table(
        'shipments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference', sa.String(length=50), nullable=False),
        sa.Column('container_number', sa.String(length=20), nullable=True),
        sa.Column('bl_number', sa.String(length=50), nullable=True),
        sa.Column('booking_ref', sa.String(length=50), nullable=True),
        sa.Column('vessel_name', sa.String(length=100), nullable=True),
        sa.Column('voyage_number', sa.String(length=50), nullable=True),
        sa.Column('carrier_code', sa.String(length=20), nullable=True),
        sa.Column('carrier_name', sa.String(length=100), nullable=True),
        sa.Column('pol_code', sa.String(length=10), nullable=True),
        sa.Column('pol_name', sa.String(length=100), nullable=True),
        sa.Column('pod_code', sa.String(length=10), nullable=True),
        sa.Column('pod_name', sa.String(length=100), nullable=True),
        sa.Column('etd', sa.DateTime(timezone=True), nullable=True),
        sa.Column('eta', sa.DateTime(timezone=True), nullable=True),
        sa.Column('atd', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ata', sa.DateTime(timezone=True), nullable=True),
        sa.Column('incoterms', sa.String(length=10), nullable=True),
        sa.Column('status', postgresql.ENUM('DRAFT', 'DOCS_PENDING', 'DOCS_COMPLETE', 'IN_TRANSIT', 'ARRIVED', 'CUSTOMS', 'DELIVERED', 'ARCHIVED', name='shipmentstatus', create_type=False), nullable=False),
        sa.Column('exporter_name', sa.String(length=255), nullable=True),
        sa.Column('importer_name', sa.String(length=255), nullable=True),
        sa.Column('eudr_compliant', sa.Boolean(), nullable=True),
        sa.Column('eudr_statement_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference')
    )
    op.create_index('ix_shipments_reference', 'shipments', ['reference'], unique=True)
    op.create_index('ix_shipments_container_number', 'shipments', ['container_number'])

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('document_type', postgresql.ENUM('BILL_OF_LADING', 'COMMERCIAL_INVOICE', 'PACKING_LIST', 'CERTIFICATE_OF_ORIGIN', 'PHYTOSANITARY_CERTIFICATE', 'FUMIGATION_CERTIFICATE', 'INSURANCE_CERTIFICATE', 'CONTRACT', 'CUSTOMS_DECLARATION', 'OTHER', name='documenttype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('UPLOADED', 'PENDING_VALIDATION', 'VALIDATED', 'REJECTED', 'EXPIRED', name='documentstatus', create_type=False), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('document_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('issuer', sa.String(length=255), nullable=True),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('validation_notes', sa.Text(), nullable=True),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['validated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_shipment_id', 'documents', ['shipment_id'])

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hs_code', sa.String(length=20), nullable=True),
        sa.Column('quantity_net_kg', sa.Float(), nullable=True),
        sa.Column('quantity_gross_kg', sa.Float(), nullable=True),
        sa.Column('quantity_units', sa.Integer(), nullable=True),
        sa.Column('packaging', sa.String(length=100), nullable=True),
        sa.Column('batch_number', sa.String(length=100), nullable=True),
        sa.Column('lot_number', sa.String(length=100), nullable=True),
        sa.Column('moisture_content', sa.Float(), nullable=True),
        sa.Column('quality_grade', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_shipment_id', 'products', ['shipment_id'])

    # Create origins table
    op.create_table(
        'origins',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('farm_name', sa.String(length=255), nullable=True),
        sa.Column('plot_identifier', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('production_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('harvest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supplier_name', sa.String(length=255), nullable=True),
        sa.Column('supplier_id', sa.String(length=100), nullable=True),
        sa.Column('deforestation_free', sa.Boolean(), nullable=True),
        sa.Column('eudr_cutoff_compliant', sa.Boolean(), nullable=True),
        sa.Column('risk_level', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel', create_type=False), nullable=True),
        sa.Column('verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_origins_shipment_id', 'origins', ['shipment_id'])

    # Create parties table
    op.create_table(
        'parties',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('party_type', postgresql.ENUM('EXPORTER', 'IMPORTER', 'SUPPLIER', 'BUYER', 'SHIPPING_LINE', 'CUSTOMS_AGENT', 'OTHER', name='partytype', create_type=False), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('registration_number', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_parties_shipment_id', 'parties', ['shipment_id'])

    # Create container_events table
    op.create_table(
        'container_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_status', postgresql.ENUM('BOOKED', 'GATE_IN', 'LOADED', 'DEPARTED', 'IN_TRANSIT', 'TRANSSHIPMENT', 'ARRIVED', 'DISCHARGED', 'GATE_OUT', 'DELIVERED', 'OTHER', name='eventstatus', create_type=False), nullable=False),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location_code', sa.String(length=20), nullable=True),
        sa.Column('location_name', sa.String(length=255), nullable=True),
        sa.Column('vessel_name', sa.String(length=100), nullable=True),
        sa.Column('voyage_number', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_container_events_shipment_id', 'container_events', ['shipment_id'])
    op.create_index('ix_container_events_event_time', 'container_events', ['event_time'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notification_type', postgresql.ENUM('DOCUMENT_UPLOADED', 'DOCUMENT_VALIDATED', 'DOCUMENT_REJECTED', 'SHIPMENT_CREATED', 'SHIPMENT_STATUS_CHANGED', 'CONTAINER_UPDATE', 'COMPLIANCE_ALERT', 'DEADLINE_REMINDER', 'SYSTEM', name='notificationtype', create_type=False), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('link', sa.String(length=500), nullable=True),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('container_events')
    op.drop_table('parties')
    op.drop_table('origins')
    op.drop_table('products')
    op.drop_table('documents')
    op.drop_table('shipments')
    op.drop_table('users')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS eventstatus")
    op.execute("DROP TYPE IF EXISTS partytype")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS documenttype")
    op.execute("DROP TYPE IF EXISTS shipmentstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
