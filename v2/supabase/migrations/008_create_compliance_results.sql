-- PRD-002: compliance_results table

CREATE TABLE compliance_results (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id     uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  rule_id         varchar(20) NOT NULL,
  rule_name       varchar(100) NOT NULL,
  passed          boolean NOT NULL,
  message         text,
  severity        varchar(20) NOT NULL,
  field_path      varchar(100),
  checked_at      timestamptz NOT NULL DEFAULT now(),
  created_at      timestamptz NOT NULL DEFAULT now(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE
);
