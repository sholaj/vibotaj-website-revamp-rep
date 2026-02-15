-- PRD-002: organization_memberships and invitations tables

CREATE TABLE organization_memberships (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid NOT NULL REFERENCES users(id),
  organization_id uuid NOT NULL REFERENCES organizations(id),
  org_role        orgrole NOT NULL DEFAULT 'member',
  status          membershipstatus NOT NULL DEFAULT 'active',
  is_primary      boolean NOT NULL DEFAULT false,
  joined_at       timestamptz NOT NULL DEFAULT now(),
  last_active_at  timestamptz DEFAULT now(),
  invited_by      uuid REFERENCES users(id),
  invitation_id   uuid  -- FK added below after invitations table exists
);

CREATE TABLE invitations (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id     uuid NOT NULL REFERENCES organizations(id),
  email               varchar(255) NOT NULL,
  org_role            orgrole NOT NULL DEFAULT 'member',
  token_hash          varchar(64) NOT NULL UNIQUE,
  status              invitationstatus NOT NULL DEFAULT 'pending',
  expires_at          timestamptz NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  created_by          uuid NOT NULL REFERENCES users(id),
  accepted_at         timestamptz,
  accepted_by         uuid REFERENCES users(id),
  invitation_metadata jsonb DEFAULT '{}'::jsonb
);

-- Add deferred FK from memberships to invitations
ALTER TABLE organization_memberships
  ADD CONSTRAINT fk_memberships_invitation_id
  FOREIGN KEY (invitation_id) REFERENCES invitations(id);
