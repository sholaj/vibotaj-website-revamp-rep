-- PRD-002: documents and document_issues tables

CREATE TABLE documents (
  id                         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id                uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  name                       varchar(255) NOT NULL,
  document_type              documenttype NOT NULL,
  status                     documentstatus NOT NULL,
  file_name                  varchar(255),
  file_path                  varchar(500),
  file_size                  integer,
  mime_type                  varchar(100),
  document_date              timestamptz,
  expiry_date                timestamptz,
  issuer                     varchar(255),
  reference_number           varchar(100),
  validation_notes           text,
  validated_by               uuid REFERENCES users(id),
  validated_at               timestamptz,
  uploaded_by                uuid REFERENCES users(id),
  extracted_container_number varchar(20),
  extraction_confidence      double precision,
  bol_parsed_data            jsonb,
  compliance_status          varchar(20),
  compliance_checked_at      timestamptz,
  canonical_data             jsonb,
  version                    integer NOT NULL DEFAULT 1,
  is_primary                 boolean NOT NULL DEFAULT true,
  supersedes_id              uuid REFERENCES documents(id) ON DELETE SET NULL,
  classification_confidence  double precision,
  parsed_at                  timestamptz,
  parser_version             varchar(20),
  last_validated_at          timestamptz,
  validation_version         integer,
  -- IMPORTANT: organization_id is nullable (backward compat from v1 Sprint 10)
  organization_id            uuid REFERENCES organizations(id),
  created_at                 timestamptz DEFAULT now(),
  updated_at                 timestamptz DEFAULT now()
);

COMMENT ON COLUMN documents.canonical_data IS 'Canonical extracted data in standardized format';
COMMENT ON COLUMN documents.version IS 'Document version number';
COMMENT ON COLUMN documents.is_primary IS 'Whether this is the primary version for validation';
COMMENT ON COLUMN documents.supersedes_id IS 'ID of the document this version supersedes';
COMMENT ON COLUMN documents.classification_confidence IS 'AI classification confidence (0.0-1.0)';
COMMENT ON COLUMN documents.parsed_at IS 'When document was parsed';
COMMENT ON COLUMN documents.parser_version IS 'Version of parser used';
COMMENT ON COLUMN documents.last_validated_at IS 'Last validation timestamp';
COMMENT ON COLUMN documents.validation_version IS 'Version of validation rules used';

CREATE TABLE document_issues (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id          uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  shipment_id          uuid REFERENCES shipments(id) ON DELETE CASCADE,
  rule_id              varchar(50) NOT NULL,
  rule_name            varchar(255) NOT NULL,
  severity             varchar(20) NOT NULL,
  message              text NOT NULL,
  field                varchar(100),
  expected_value       text,
  actual_value         text,
  source_document_type varchar(50),
  target_document_type varchar(50),
  is_overridden        boolean NOT NULL DEFAULT false,
  overridden_by        uuid REFERENCES users(id),
  overridden_at        timestamptz,
  override_reason      text,
  organization_id      uuid REFERENCES organizations(id),
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

COMMENT ON COLUMN document_issues.rule_id IS 'Rule identifier (e.g., DOC-001, XD-002)';
COMMENT ON COLUMN document_issues.rule_name IS 'Human-readable rule name';
COMMENT ON COLUMN document_issues.severity IS 'ERROR, WARNING, or INFO';
COMMENT ON COLUMN document_issues.message IS 'Validation failure message';
COMMENT ON COLUMN document_issues.field IS 'Field path that failed validation';
COMMENT ON COLUMN document_issues.expected_value IS 'Expected value (for comparison rules)';
COMMENT ON COLUMN document_issues.actual_value IS 'Actual value found';
COMMENT ON COLUMN document_issues.is_overridden IS 'Whether issue has been overridden';
COMMENT ON COLUMN document_issues.override_reason IS 'Reason for override';
