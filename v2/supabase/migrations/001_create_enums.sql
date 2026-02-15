-- PRD-002: Create all enum types
-- Order matters: enums must exist before tables that reference them.

-- User & role enums
CREATE TYPE userrole AS ENUM (
  'admin', 'compliance', 'logistics_agent', 'buyer', 'supplier', 'viewer'
);

CREATE TYPE orgrole AS ENUM (
  'admin', 'manager', 'member', 'viewer'
);

-- Organization enums
CREATE TYPE organizationtype AS ENUM (
  'vibotaj', 'buyer', 'supplier', 'logistics_agent'
);

CREATE TYPE organizationstatus AS ENUM (
  'active', 'suspended', 'pending_setup'
);

CREATE TYPE membershipstatus AS ENUM (
  'active', 'suspended', 'pending'
);

CREATE TYPE invitationstatus AS ENUM (
  'pending', 'accepted', 'expired', 'revoked'
);

-- Shipment enums
CREATE TYPE shipmentstatus AS ENUM (
  'draft', 'docs_pending', 'docs_complete', 'in_transit',
  'arrived', 'customs', 'delivered', 'archived'
);

CREATE TYPE producttype AS ENUM (
  'horn_hoof', 'sweet_potato', 'hibiscus', 'ginger', 'cocoa', 'other'
);

-- Document enums
CREATE TYPE documenttype AS ENUM (
  'bill_of_lading', 'commercial_invoice', 'packing_list',
  'certificate_of_origin', 'phytosanitary_certificate',
  'fumigation_certificate', 'sanitary_certificate',
  'insurance_certificate', 'customs_declaration', 'contract',
  'eudr_due_diligence', 'quality_certificate',
  'eu_traces_certificate', 'veterinary_health_certificate',
  'export_declaration', 'other'
);

-- Includes deprecated statuses for v1 data migration compatibility
CREATE TYPE documentstatus AS ENUM (
  'draft', 'uploaded', 'validated', 'compliance_ok',
  'compliance_failed', 'linked', 'archived',
  'pending_validation', 'rejected', 'expired'
);

-- Tracking enums
CREATE TYPE eventstatus AS ENUM (
  'booked', 'gate_in', 'loaded', 'departed', 'in_transit',
  'transshipment', 'arrived', 'discharged', 'gate_out',
  'delivered', 'other'
);

-- Risk enums
CREATE TYPE risklevel AS ENUM (
  'low', 'medium', 'high', 'critical'
);
