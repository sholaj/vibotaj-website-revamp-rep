-- PRD-002: Enable RLS on all 15 tables and create policies
-- FastAPI middleware sets these per-request via SET LOCAL:
--   app.current_org_id  = UUID of the authenticated user's organization
--   app.is_system_admin = 'true' | 'false'

-- Helper function: get current org ID from session variable
CREATE OR REPLACE FUNCTION current_org_id() RETURNS uuid AS $$
  SELECT NULLIF(current_setting('app.current_org_id', true), '')::uuid;
$$ LANGUAGE sql STABLE;

-- Helper function: check if current user is system admin
CREATE OR REPLACE FUNCTION is_system_admin() RETURNS boolean AS $$
  SELECT COALESCE(current_setting('app.is_system_admin', true), 'false')::boolean;
$$ LANGUAGE sql STABLE;


-- ============================================================
-- 1. ORGANIZATIONS
-- ============================================================
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "org_tenant_isolation" ON organizations
  USING (id = current_org_id() OR is_system_admin());

CREATE POLICY "org_admin_insert" ON organizations FOR INSERT
  WITH CHECK (is_system_admin());


-- ============================================================
-- 2. USERS
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_tenant_isolation" ON users
  USING (organization_id = current_org_id() OR is_system_admin());

CREATE POLICY "users_insert" ON users FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR is_system_admin());


-- ============================================================
-- 3. ORGANIZATION_MEMBERSHIPS
-- ============================================================
ALTER TABLE organization_memberships ENABLE ROW LEVEL SECURITY;

CREATE POLICY "memberships_tenant_isolation" ON organization_memberships
  USING (organization_id = current_org_id() OR is_system_admin());

CREATE POLICY "memberships_insert" ON organization_memberships FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR is_system_admin());


-- ============================================================
-- 4. INVITATIONS
-- ============================================================
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "invitations_tenant_isolation" ON invitations
  USING (organization_id = current_org_id() OR is_system_admin());

CREATE POLICY "invitations_insert" ON invitations FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR is_system_admin());


-- ============================================================
-- 5. SHIPMENTS (dual RLS: owner org + buyer org)
-- ============================================================
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;

-- Owner org can do everything
CREATE POLICY "shipments_owner_isolation" ON shipments
  USING (organization_id = current_org_id() OR is_system_admin());

-- Buyer org gets read-only access
CREATE POLICY "shipments_buyer_read" ON shipments FOR SELECT
  USING (buyer_organization_id = current_org_id());

CREATE POLICY "shipments_insert" ON shipments FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR is_system_admin());


-- ============================================================
-- 6. DOCUMENTS (organization_id is nullable)
-- ============================================================
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "documents_tenant_isolation" ON documents
  USING (
    organization_id = current_org_id()
    OR organization_id IS NULL  -- backward compat: unowned docs visible
    OR is_system_admin()
  );

CREATE POLICY "documents_insert" ON documents FOR INSERT
  WITH CHECK (
    organization_id = current_org_id()
    OR organization_id IS NULL
    OR is_system_admin()
  );


-- ============================================================
-- 7. DOCUMENT_ISSUES
-- ============================================================
ALTER TABLE document_issues ENABLE ROW LEVEL SECURITY;

CREATE POLICY "doc_issues_tenant_isolation" ON document_issues
  USING (organization_id = current_org_id() OR organization_id IS NULL OR is_system_admin());

CREATE POLICY "doc_issues_insert" ON document_issues FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR organization_id IS NULL OR is_system_admin());


-- ============================================================
-- 8. DOCUMENT_CONTENTS (access follows parent document)
-- ============================================================
ALTER TABLE document_contents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "doc_contents_via_document" ON document_contents
  USING (
    EXISTS (
      SELECT 1 FROM documents d
      WHERE d.id = document_contents.document_id
        AND (d.organization_id = current_org_id() OR d.organization_id IS NULL OR is_system_admin())
    )
  );

CREATE POLICY "doc_contents_insert" ON document_contents FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM documents d
      WHERE d.id = document_contents.document_id
        AND (d.organization_id = current_org_id() OR d.organization_id IS NULL OR is_system_admin())
    )
  );


-- ============================================================
-- 9. COMPLIANCE_RESULTS
-- ============================================================
ALTER TABLE compliance_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "compliance_tenant_isolation" ON compliance_results
  USING (organization_id = current_org_id() OR is_system_admin());

CREATE POLICY "compliance_insert" ON compliance_results FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR is_system_admin());


-- ============================================================
-- 10. CONTAINER_EVENTS
-- ============================================================
ALTER TABLE container_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "events_tenant_isolation" ON container_events
  USING (organization_id = current_org_id() OR is_system_admin());

CREATE POLICY "events_insert" ON container_events FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR is_system_admin());


-- ============================================================
-- 11. NOTIFICATIONS (user-scoped, not org-scoped)
-- ============================================================
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "notifications_user_isolation" ON notifications
  USING (
    user_id IN (
      SELECT id FROM users WHERE organization_id = current_org_id()
    )
    OR is_system_admin()
  );

CREATE POLICY "notifications_insert" ON notifications FOR INSERT
  WITH CHECK (
    user_id IN (
      SELECT id FROM users WHERE organization_id = current_org_id()
    )
    OR is_system_admin()
  );


-- ============================================================
-- 12. ORIGINS
-- ============================================================
ALTER TABLE origins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "origins_tenant_isolation" ON origins
  USING (organization_id = current_org_id() OR is_system_admin());

CREATE POLICY "origins_insert" ON origins FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR is_system_admin());


-- ============================================================
-- 13. PRODUCTS
-- ============================================================
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

CREATE POLICY "products_tenant_isolation" ON products
  USING (organization_id = current_org_id() OR is_system_admin());

CREATE POLICY "products_insert" ON products FOR INSERT
  WITH CHECK (organization_id = current_org_id() OR is_system_admin());


-- ============================================================
-- 14. REFERENCE_REGISTRY (access follows parent shipment)
-- ============================================================
ALTER TABLE reference_registry ENABLE ROW LEVEL SECURITY;

CREATE POLICY "ref_registry_via_shipment" ON reference_registry
  USING (
    EXISTS (
      SELECT 1 FROM shipments s
      WHERE s.id = reference_registry.shipment_id
        AND (s.organization_id = current_org_id() OR is_system_admin())
    )
  );

CREATE POLICY "ref_registry_insert" ON reference_registry FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM shipments s
      WHERE s.id = reference_registry.shipment_id
        AND (s.organization_id = current_org_id() OR is_system_admin())
    )
  );


-- ============================================================
-- 15. AUDIT_LOGS (admin-only access)
-- ============================================================
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "audit_logs_admin_read" ON audit_logs FOR SELECT
  USING (
    organization_id = current_org_id()
    OR organization_id IS NULL
    OR is_system_admin()
  );

-- Only the system (via service role) should insert audit logs
CREATE POLICY "audit_logs_system_insert" ON audit_logs FOR INSERT
  WITH CHECK (true);  -- Controlled at application layer
