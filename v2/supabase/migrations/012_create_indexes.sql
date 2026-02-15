-- PRD-002: Create all indexes matching v1 SQLAlchemy models
-- Note: unique constraints from CREATE TABLE already create implicit indexes.
-- We only create additional explicit indexes here.

-- ============================================================
-- ORGANIZATIONS
-- ============================================================
-- slug unique index is automatic from UNIQUE constraint
CREATE INDEX ix_organizations_type_status ON organizations (type, status);
CREATE INDEX ix_organizations_name ON organizations (name);

-- ============================================================
-- USERS
-- ============================================================
-- email unique index is automatic from UNIQUE constraint
CREATE INDEX ix_users_organization_id ON users (organization_id);

-- ============================================================
-- ORGANIZATION_MEMBERSHIPS
-- ============================================================
-- user_id + organization_id unique is automatic from UNIQUE constraint
CREATE INDEX ix_membership_org_role ON organization_memberships (organization_id, org_role);
CREATE INDEX ix_membership_user_primary ON organization_memberships (user_id, is_primary);

-- ============================================================
-- INVITATIONS
-- ============================================================
CREATE INDEX ix_invitations_email ON invitations (email);
-- token_hash unique index is automatic from UNIQUE constraint
CREATE INDEX ix_invitation_org_email ON invitations (organization_id, email);
CREATE INDEX ix_invitation_status ON invitations (status);
CREATE INDEX ix_invitation_expires ON invitations (expires_at);

-- ============================================================
-- SHIPMENTS
-- ============================================================
CREATE INDEX ix_shipments_organization_id ON shipments (organization_id);
CREATE INDEX ix_shipments_buyer_organization_id ON shipments (buyer_organization_id);
CREATE INDEX ix_shipments_product_type ON shipments (product_type);
-- org + reference unique is automatic from UNIQUE constraint

-- ============================================================
-- DOCUMENTS
-- ============================================================
CREATE INDEX ix_documents_organization_id ON documents (organization_id);

-- ============================================================
-- DOCUMENT_ISSUES
-- ============================================================
CREATE INDEX ix_document_issues_document_id ON document_issues (document_id);
CREATE INDEX ix_document_issues_shipment_id ON document_issues (shipment_id);
CREATE INDEX ix_document_issues_rule_id ON document_issues (rule_id);
CREATE INDEX ix_document_issues_severity ON document_issues (severity);
CREATE INDEX ix_document_issues_is_overridden ON document_issues (is_overridden);
CREATE INDEX ix_document_issues_organization_id ON document_issues (organization_id);

-- ============================================================
-- COMPLIANCE_RESULTS
-- ============================================================
CREATE INDEX ix_compliance_results_document_id ON compliance_results (document_id);
CREATE INDEX ix_compliance_results_organization_id ON compliance_results (organization_id);

-- ============================================================
-- CONTAINER_EVENTS
-- ============================================================
CREATE INDEX ix_container_events_shipment_id ON container_events (shipment_id);
CREATE INDEX ix_container_events_organization_id ON container_events (organization_id);
CREATE INDEX ix_container_events_event_time ON container_events (event_time);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
CREATE INDEX ix_notifications_user_id ON notifications (user_id);
CREATE INDEX ix_notifications_user_read ON notifications (user_id, read);
CREATE INDEX ix_notifications_user_created ON notifications (user_id, created_at);

-- ============================================================
-- ORIGINS
-- ============================================================
CREATE INDEX ix_origins_shipment_id ON origins (shipment_id);
CREATE INDEX ix_origins_organization_id ON origins (organization_id);

-- ============================================================
-- PRODUCTS
-- ============================================================
CREATE INDEX ix_products_shipment_id ON products (shipment_id);
CREATE INDEX ix_products_organization_id ON products (organization_id);

-- ============================================================
-- REFERENCE_REGISTRY
-- ============================================================
CREATE INDEX ix_reference_registry_reference_number ON reference_registry (reference_number);
-- composite unique on (shipment_id, reference_number, document_type) is automatic

-- ============================================================
-- AUDIT_LOGS
-- ============================================================
CREATE INDEX ix_audit_logs_organization_id ON audit_logs (organization_id);
CREATE INDEX ix_audit_logs_request_id ON audit_logs (request_id);
CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);
CREATE INDEX ix_audit_logs_user_timestamp ON audit_logs (username, timestamp);
CREATE INDEX ix_audit_logs_action_timestamp ON audit_logs (action, timestamp);
CREATE INDEX ix_audit_logs_resource ON audit_logs (resource_type, resource_id);
