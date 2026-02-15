-- PRD-002: organizations table
-- Note: created_by FK references users.id which doesn't exist yet.
-- We add the FK constraint in a later migration after users table is created.

CREATE TABLE organizations (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                varchar(255) NOT NULL,
  slug                varchar(50) NOT NULL UNIQUE,
  type                organizationtype NOT NULL,
  status              organizationstatus NOT NULL DEFAULT 'active',
  contact_email       varchar(255) NOT NULL,
  contact_phone       varchar(50),
  address             jsonb DEFAULT '{}'::jsonb,
  tax_id              varchar(100),
  registration_number varchar(100),
  logo_url            varchar(500),
  settings            jsonb DEFAULT '{}'::jsonb,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz DEFAULT now(),
  created_by          uuid  -- FK added in 004 after users table exists
);
