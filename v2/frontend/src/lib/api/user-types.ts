// --- User & Organization types (no React/PropelAuth dependencies) ---

export type OrgType = "vibotaj" | "buyer" | "supplier" | "logistics_agent";
export type OrgStatus = "active" | "suspended" | "pending_setup";
export type OrgRole = "admin" | "manager" | "member" | "viewer";
export type MembershipStatus = "active" | "suspended" | "pending";
export type InvitationStatus = "pending" | "accepted" | "expired" | "revoked";

export interface Member {
  id: string;
  user_id: string;
  organization_id: string;
  email: string | null;
  full_name: string | null;
  org_role: OrgRole;
  status: MembershipStatus;
  is_primary: boolean;
  joined_at: string;
  last_active_at: string | null;
  invited_by: string | null;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
  last_login: string | null;
  primary_organization: {
    organization_id: string;
    organization_name: string;
    organization_type: OrgType;
    org_role: OrgRole;
  } | null;
}

export interface UsersListResponse {
  items: UserResponse[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface RoleInfo {
  name: string;
  description: string;
  can_assign: boolean;
}

export interface OrgListItem {
  id: string;
  name: string;
  slug: string;
  type: OrgType;
  status: OrgStatus;
  member_count: number;
  created_at: string;
}

export interface OrgListResponse {
  items: OrgListItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface OrgDetail {
  id: string;
  name: string;
  slug: string;
  type: OrgType;
  status: OrgStatus;
  contact_email: string;
  contact_phone: string | null;
  member_count: number | null;
  shipment_count: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface Invitation {
  id: string;
  organization_id: string;
  organization_name: string | null;
  email: string;
  org_role: OrgRole;
  status: InvitationStatus;
  created_at: string;
  expires_at: string;
  created_by_name: string | null;
  accepted_at: string | null;
}

// --- Labels & Helpers ---

export const ORG_TYPE_LABELS: Record<OrgType, string> = {
  vibotaj: "Vibotaj",
  buyer: "Buyer",
  supplier: "Supplier",
  logistics_agent: "Logistics",
};

export const ORG_STATUS_LABELS: Record<OrgStatus, string> = {
  active: "Active",
  suspended: "Suspended",
  pending_setup: "Pending Setup",
};

export const ORG_ROLE_LABELS: Record<OrgRole, string> = {
  admin: "Admin",
  manager: "Manager",
  member: "Member",
  viewer: "Viewer",
};

export const MEMBERSHIP_STATUS_LABELS: Record<MembershipStatus, string> = {
  active: "Active",
  suspended: "Suspended",
  pending: "Pending",
};

export const INVITATION_STATUS_LABELS: Record<InvitationStatus, string> = {
  pending: "Pending",
  accepted: "Accepted",
  expired: "Expired",
  revoked: "Revoked",
};

export function isInvitationActionable(invitation: Invitation): boolean {
  return invitation.status === "pending";
}

export function getMemberDisplayName(member: Member): string {
  return member.full_name ?? member.email ?? "Unknown";
}

export function formatLastActive(iso: string | null): string {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
