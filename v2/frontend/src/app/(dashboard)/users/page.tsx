"use client";

import { useState, useCallback } from "react";
import { PageHeader } from "@/components/domain/page-header";
import { LoadingState } from "@/components/domain/loading-state";
import { ErrorState } from "@/components/domain/error-state";
import { AccessDenied } from "@/components/domain/access-denied";
import { MemberTable } from "@/components/users/member-table";
import { InviteMemberModal } from "@/components/users/invite-member-modal";
import { PendingInvitations } from "@/components/users/pending-invitations";
import { Input } from "@/components/ui/input";
import {
  useOrgMembers,
  useUpdateUser,
  useInviteMember,
  usePendingInvitations,
  useRevokeInvitation,
  type OrgRole,
} from "@/lib/api/users";
import { useCurrentOrg } from "@/lib/auth/org-context";

export default function UsersPage() {
  const { role, orgId } = useCurrentOrg();
  const isAdmin = role === "admin";

  const [search, setSearch] = useState("");
  const [inviteOpen, setInviteOpen] = useState(false);

  const {
    data: usersData,
    isLoading,
    error,
    refetch,
  } = useOrgMembers({ search: search || undefined });

  const { data: invitations } = usePendingInvitations(orgId);
  const updateMutation = useUpdateUser();
  const inviteMutation = useInviteMember(orgId ?? "");
  const revokeMutation = useRevokeInvitation(orgId ?? "");

  const handleChangeRole = useCallback(
    (userId: string, newRole: string) => {
      updateMutation.mutate({ userId, updates: { role: newRole } });
    },
    [updateMutation],
  );

  const handleToggleActive = useCallback(
    (userId: string, isActive: boolean) => {
      updateMutation.mutate({ userId, updates: { is_active: isActive } });
    },
    [updateMutation],
  );

  const handleInvite = useCallback(
    (email: string, orgRole: OrgRole) => {
      inviteMutation.mutate(
        { email, orgRole },
        { onSuccess: () => setInviteOpen(false) },
      );
    },
    [inviteMutation],
  );

  if (!isAdmin) {
    return (
      <div className="space-y-6">
        <PageHeader title="Team Members" />
        <AccessDenied />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Team Members"
        description="Manage your organization's team members and invitations."
      />

      <div className="max-w-sm">
        <Input
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading && <LoadingState variant="table" />}

      {error && (
        <ErrorState
          message="Failed to load team members."
          onRetry={() => refetch()}
        />
      )}

      {usersData && (
        <MemberTable
          users={usersData.items}
          onInvite={() => setInviteOpen(true)}
          onChangeRole={handleChangeRole}
          onToggleActive={handleToggleActive}
          canManage={isAdmin}
        />
      )}

      {invitations && invitations.length > 0 && (
        <PendingInvitations
          invitations={invitations}
          onRevoke={(id) => revokeMutation.mutate(id)}
          isRevoking={revokeMutation.isPending}
        />
      )}

      <InviteMemberModal
        open={inviteOpen}
        onOpenChange={setInviteOpen}
        onInvite={handleInvite}
        isInviting={inviteMutation.isPending}
      />
    </div>
  );
}
