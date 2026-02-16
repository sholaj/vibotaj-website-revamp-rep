"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type {
  UsersListResponse,
  RoleInfo,
  OrgListResponse,
  OrgDetail,
  Member,
  Invitation,
  OrgRole,
} from "./user-types";

// Re-export types
export type {
  Member,
  UserResponse,
  RoleInfo,
  OrgListItem,
  OrgDetail,
  Invitation,
  OrgType,
  OrgStatus,
  OrgRole,
  MembershipStatus,
  InvitationStatus,
} from "./user-types";

export {
  ORG_TYPE_LABELS,
  ORG_STATUS_LABELS,
  ORG_ROLE_LABELS,
  MEMBERSHIP_STATUS_LABELS,
  INVITATION_STATUS_LABELS,
  isInvitationActionable,
  getMemberDisplayName,
  formatLastActive,
} from "./user-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Organization-Id": orgId,
  };
}

// --- Fetch functions ---

async function fetchUsers(
  orgId: string,
  params: { search?: string; role?: string; limit?: number; offset?: number },
): Promise<UsersListResponse> {
  const searchParams = new URLSearchParams();
  if (params.search) searchParams.set("search", params.search);
  if (params.role && params.role !== "all") searchParams.set("role", params.role);
  searchParams.set("limit", String(params.limit ?? 20));
  searchParams.set("offset", String(params.offset ?? 0));

  const res = await fetch(`${API_BASE}/api/users?${searchParams}`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch users: ${res.status}`);
  return res.json() as Promise<UsersListResponse>;
}

async function fetchRoles(orgId: string): Promise<RoleInfo[]> {
  const res = await fetch(`${API_BASE}/api/users/roles`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch roles: ${res.status}`);
  return res.json() as Promise<RoleInfo[]>;
}

async function fetchOrganizations(
  orgId: string,
  params: { search?: string; type?: string; limit?: number; offset?: number },
): Promise<OrgListResponse> {
  const searchParams = new URLSearchParams();
  if (params.search) searchParams.set("name", params.search);
  if (params.type && params.type !== "all") searchParams.set("type", params.type);
  searchParams.set("limit", String(params.limit ?? 20));
  searchParams.set("offset", String(params.offset ?? 0));

  const res = await fetch(`${API_BASE}/api/organizations?${searchParams}`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch organizations: ${res.status}`);
  return res.json() as Promise<OrgListResponse>;
}

async function fetchOrganization(
  orgId: string,
  targetOrgId: string,
): Promise<OrgDetail> {
  const res = await fetch(`${API_BASE}/api/organizations/${targetOrgId}`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch organization: ${res.status}`);
  return res.json() as Promise<OrgDetail>;
}

async function fetchOrgMembers(
  orgId: string,
  targetOrgId: string,
): Promise<Member[]> {
  const res = await fetch(
    `${API_BASE}/api/organizations/${targetOrgId}/members`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error(`Failed to fetch members: ${res.status}`);
  return res.json() as Promise<Member[]>;
}

async function fetchInvitations(
  orgId: string,
  targetOrgId: string,
): Promise<Invitation[]> {
  const res = await fetch(
    `${API_BASE}/api/organizations/${targetOrgId}/invitations`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error(`Failed to fetch invitations: ${res.status}`);
  return res.json() as Promise<Invitation[]>;
}

// --- React Query hooks ---

export function useOrgMembers(
  params: { search?: string; role?: string } = {},
) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["users", orgId, params],
    queryFn: () => fetchUsers(orgId!, params),
    enabled: !!orgId,
    staleTime: 30_000,
  });
}

export function useRoles() {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["roles", orgId],
    queryFn: () => fetchRoles(orgId!),
    enabled: !!orgId,
    staleTime: 10 * 60_000,
  });
}

export function useOrganizations(
  params: { search?: string; type?: string } = {},
) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["organizations", orgId, params],
    queryFn: () => fetchOrganizations(orgId!, params),
    enabled: !!orgId,
    staleTime: 60_000,
  });
}

export function useOrganization(targetOrgId: string | null) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["organization", orgId, targetOrgId],
    queryFn: () => fetchOrganization(orgId!, targetOrgId!),
    enabled: !!orgId && !!targetOrgId,
    staleTime: 60_000,
  });
}

export function useOrgDetailMembers(targetOrgId: string | null) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["org-members", orgId, targetOrgId],
    queryFn: () => fetchOrgMembers(orgId!, targetOrgId!),
    enabled: !!orgId && !!targetOrgId,
    staleTime: 30_000,
  });
}

export function usePendingInvitations(targetOrgId: string | null) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["invitations", orgId, targetOrgId],
    queryFn: () => fetchInvitations(orgId!, targetOrgId!),
    enabled: !!orgId && !!targetOrgId,
    staleTime: 30_000,
  });
}

export function useUpdateUser() {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      updates,
    }: {
      userId: string;
      updates: { role?: string; is_active?: boolean };
    }) => {
      const res = await fetch(`${API_BASE}/api/users/${userId}`, {
        method: "PATCH",
        headers: authHeaders(orgId!),
        body: JSON.stringify(updates),
      });
      if (!res.ok) throw new Error(`Failed to update user: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["users", orgId] });
    },
  });
}

export function useInviteMember(targetOrgId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      email,
      orgRole,
    }: {
      email: string;
      orgRole: OrgRole;
    }) => {
      const res = await fetch(
        `${API_BASE}/api/organizations/${targetOrgId}/invitations`,
        {
          method: "POST",
          headers: authHeaders(orgId!),
          body: JSON.stringify({ email, org_role: orgRole }),
        },
      );
      if (!res.ok) throw new Error(`Failed to invite member: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["invitations", orgId, targetOrgId],
      });
    },
  });
}

export function useRevokeInvitation(targetOrgId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (invitationId: string) => {
      const res = await fetch(
        `${API_BASE}/api/organizations/${targetOrgId}/invitations/${invitationId}`,
        {
          method: "DELETE",
          headers: authHeaders(orgId!),
        },
      );
      if (!res.ok) throw new Error(`Failed to revoke invitation: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["invitations", orgId, targetOrgId],
      });
    },
  });
}
