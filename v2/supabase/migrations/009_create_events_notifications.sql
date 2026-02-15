-- PRD-002: container_events and notifications tables

CREATE TABLE container_events (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id     uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
  event_status    eventstatus NOT NULL,
  event_time      timestamptz NOT NULL,
  location_code   varchar(20),
  location_name   varchar(255),
  vessel_name     varchar(100),
  voyage_number   varchar(50),
  description     text,
  source          varchar(50),
  raw_data        jsonb,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type       varchar(50) NOT NULL,
  title      varchar(255) NOT NULL,
  message    text NOT NULL,
  data       jsonb DEFAULT '{}'::jsonb,
  read       boolean NOT NULL DEFAULT false,
  read_at    timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
