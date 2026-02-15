-- PRD-002: users table

CREATE TABLE users (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email            varchar(255) NOT NULL UNIQUE,
  hashed_password  varchar(255) NOT NULL,
  full_name        varchar(100) NOT NULL,
  role             userrole NOT NULL DEFAULT 'viewer',
  is_active        boolean NOT NULL DEFAULT true,
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz DEFAULT now(),
  last_login       timestamptz,
  deleted_at       timestamptz,
  deleted_by       uuid REFERENCES users(id) ON DELETE SET NULL,
  deletion_reason  varchar(500)
);

-- Now add the deferred FK from organizations.created_by -> users.id
ALTER TABLE organizations
  ADD CONSTRAINT fk_organizations_created_by
  FOREIGN KEY (created_by) REFERENCES users(id);
