-- PRD-002: Seed data for development
-- 2 orgs (VIBOTAJ, HAGES), 4 users, sample shipments and documents

-- ============================================================
-- Organizations
-- ============================================================
INSERT INTO organizations (id, name, slug, type, status, contact_email) VALUES
  ('a0000000-0000-0000-0000-000000000001', 'VIBOTAJ Global Nigeria Ltd', 'vibotaj', 'vibotaj', 'active', 'info@vibotaj.com'),
  ('a0000000-0000-0000-0000-000000000002', 'HAGES GmbH', 'hages', 'buyer', 'active', 'contact@hages.de');

-- ============================================================
-- Users (password: "password123" hashed with bcrypt)
-- ============================================================
INSERT INTO users (id, email, hashed_password, full_name, role, organization_id) VALUES
  ('b0000000-0000-0000-0000-000000000001', 'shola@vibotaj.com',
   '$2b$12$LJ3m4ys3Gzx.OYbMfQZjqeKGqU9qvQqXL5UU7Q7u8LmCZH5EF2v6',
   'Shola Adewale', 'admin', 'a0000000-0000-0000-0000-000000000001'),

  ('b0000000-0000-0000-0000-000000000002', 'bolaji@vibotaj.com',
   '$2b$12$LJ3m4ys3Gzx.OYbMfQZjqeKGqU9qvQqXL5UU7Q7u8LmCZH5EF2v6',
   'Bolaji Jibodu', 'compliance', 'a0000000-0000-0000-0000-000000000001'),

  ('b0000000-0000-0000-0000-000000000003', 'buyer@hages.de',
   '$2b$12$LJ3m4ys3Gzx.OYbMfQZjqeKGqU9qvQqXL5UU7Q7u8LmCZH5EF2v6',
   'Hans Mueller', 'buyer', 'a0000000-0000-0000-0000-000000000002'),

  ('b0000000-0000-0000-0000-000000000004', 'viewer@hages.de',
   '$2b$12$LJ3m4ys3Gzx.OYbMfQZjqeKGqU9qvQqXL5UU7Q7u8LmCZH5EF2v6',
   'Anna Schmidt', 'viewer', 'a0000000-0000-0000-0000-000000000002');

-- ============================================================
-- Organization Memberships
-- ============================================================
INSERT INTO organization_memberships (user_id, organization_id, org_role, is_primary) VALUES
  ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'admin', true),
  ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'manager', true),
  ('b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000002', 'admin', true),
  ('b0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000002', 'viewer', true);

-- ============================================================
-- Shipments
-- ============================================================
INSERT INTO shipments (id, reference, container_number, bl_number, vessel_name, status,
                       product_type, organization_id, buyer_organization_id,
                       pol_code, pol_name, pod_code, pod_name) VALUES
  ('c0000000-0000-0000-0000-000000000001', 'VBT-2026-001', 'MSCU1234567',
   'MSCUBOL001', 'MSC GULSUN', 'in_transit', 'horn_hoof',
   'a0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002',
   'NGAPP', 'Apapa, Lagos', 'DEHAM', 'Hamburg'),

  ('c0000000-0000-0000-0000-000000000002', 'VBT-2026-002', NULL,
   NULL, NULL, 'draft', 'sweet_potato',
   'a0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000002',
   'NGAPP', 'Apapa, Lagos', 'DEHAM', 'Hamburg');

-- ============================================================
-- Documents (for the in-transit shipment)
-- ============================================================
INSERT INTO documents (id, shipment_id, name, document_type, status, organization_id) VALUES
  ('d0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001',
   'Bill of Lading - VBT-2026-001', 'bill_of_lading', 'validated',
   'a0000000-0000-0000-0000-000000000001'),

  ('d0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001',
   'Commercial Invoice - VBT-2026-001', 'commercial_invoice', 'uploaded',
   'a0000000-0000-0000-0000-000000000001'),

  ('d0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001',
   'EU TRACES Certificate', 'eu_traces_certificate', 'draft',
   'a0000000-0000-0000-0000-000000000001');
