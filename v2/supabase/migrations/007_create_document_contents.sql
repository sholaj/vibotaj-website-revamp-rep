-- PRD-002: document_contents table
-- NOTE: v1 uses DateTime WITHOUT timezone for created_at/updated_at here.
-- We use timestamptz for consistency with the rest of the schema.
-- This is a deliberate improvement over v1.

CREATE TABLE document_contents (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id      uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  document_type    documenttype NOT NULL,
  status           documentstatus NOT NULL DEFAULT 'uploaded',
  page_start       integer NOT NULL DEFAULT 1,
  page_end         integer NOT NULL DEFAULT 1,
  reference_number varchar(100),
  detected_fields  jsonb DEFAULT '{}'::jsonb,
  confidence_score double precision DEFAULT 0.0,
  detection_method varchar(50) DEFAULT 'manual',
  validation_notes varchar(1000),
  validated_at     timestamptz,
  validated_by     uuid REFERENCES users(id) ON DELETE SET NULL,
  created_at       timestamptz DEFAULT now(),
  updated_at       timestamptz DEFAULT now()
);
