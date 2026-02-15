-- PRD-002: origins, products, reference_registry, audit_logs tables

CREATE TABLE origins (
  id                            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id                   uuid NOT NULL REFERENCES shipments(id),
  organization_id               uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
  farm_name                     varchar(255),
  plot_identifier               varchar(100),
  latitude                      double precision,
  longitude                     double precision,
  country                       varchar(100) NOT NULL,
  region                        varchar(255),
  address                       text,
  production_date               timestamptz,
  harvest_date                  timestamptz,
  supplier_name                 varchar(255),
  supplier_id                   varchar(100),
  deforestation_free            boolean,
  eudr_cutoff_compliant         boolean,
  deforestation_free_statement  boolean,
  due_diligence_statement_ref   varchar(255),
  geolocation_polygon           text,
  supplier_attestation_date     timestamptz,
  risk_level                    risklevel,
  verified                      boolean NOT NULL DEFAULT false,
  verified_by                   uuid REFERENCES users(id) ON DELETE SET NULL,
  verified_at                   timestamptz,
  verification_notes            text,
  created_at                    timestamptz NOT NULL DEFAULT now(),
  updated_at                    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE products (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id      uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
  name             varchar(255) NOT NULL,
  description      text,
  hs_code          varchar(20),
  quantity_net_kg  double precision,
  quantity_gross_kg double precision,
  quantity_units   integer,
  packaging        varchar(100),
  batch_number     varchar(100),
  lot_number       varchar(100),
  moisture_content double precision,
  quality_grade    varchar(50),
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE reference_registry (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id         uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  reference_number    varchar(100) NOT NULL,
  document_type       documenttype NOT NULL,
  document_content_id uuid REFERENCES document_contents(id) ON DELETE SET NULL,
  document_id         uuid REFERENCES documents(id) ON DELETE SET NULL,
  first_seen_at       timestamptz DEFAULT now(),

  CONSTRAINT uq_reference_per_shipment_type
    UNIQUE (shipment_id, reference_number, document_type)
);

CREATE TABLE audit_logs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid REFERENCES organizations(id) ON DELETE CASCADE,
  -- NOTE: user_id is String(100) in v1, not a UUID FK (for immutability)
  user_id         varchar(100),
  username        varchar(100),
  ip_address      varchar(45),
  user_agent      varchar(500),
  action          varchar(100) NOT NULL,
  resource_type   varchar(50),
  resource_id     varchar(100),
  request_id      varchar(100),
  method          varchar(10),
  path            varchar(500),
  status_code     varchar(10),
  -- NOTE: success is String in v1, not Boolean
  success         varchar(10) DEFAULT 'true',
  details         jsonb DEFAULT '{}'::jsonb,
  error_message   text,
  -- NOTE: duration_ms is String in v1, not Integer
  duration_ms     varchar(20),
  timestamp       timestamptz NOT NULL DEFAULT now()
);
