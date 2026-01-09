// Shared org types mirroring backend enums for frontend use

export type OrganizationType =
  | "vibotaj"
  | "buyer"
  | "supplier"
  | "logistics_agent";

export type OrgRole = "admin" | "manager" | "member" | "viewer";

export type OrgPermission =
  | "members:view"
  | "members:invite"
  | "members:manage"
  | "members:remove"
  | "settings:view"
  | "settings:manage"
  | "shipments:view"
  | "shipments:create"
  | "shipments:update"
  | "shipments:delete"
  | "documents:view"
  | "documents:upload"
  | "documents:validate"
  | "documents:approve"
  | "documents:delete"
  | "tracking:view"
  | "tracking:refresh"
  | "invitations:view"
  | "invitations:create"
  | "invitations:revoke"
  | "audit:view"
  | "audit:export"
  | "compliance:view"
  | "compliance:manage";
