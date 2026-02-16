"use client";

import { useState } from "react";
import { PageHeader } from "@/components/domain/page-header";
import { LoadingState } from "@/components/domain/loading-state";
import { ErrorState } from "@/components/domain/error-state";
import { AccessDenied } from "@/components/domain/access-denied";
import { OrgTable } from "@/components/organizations/org-table";
import { OrgDetailPanel } from "@/components/organizations/org-detail-panel";
import { Input } from "@/components/ui/input";
import {
  useOrganizations,
  useOrganization,
  useOrgDetailMembers,
} from "@/lib/api/users";
import { useCurrentOrg } from "@/lib/auth/org-context";

export default function OrganizationsPage() {
  const { role } = useCurrentOrg();
  const isAdmin = role === "admin";

  const [search, setSearch] = useState("");
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);

  const {
    data: orgsData,
    isLoading,
    error,
    refetch,
  } = useOrganizations({ search: search || undefined });

  const { data: orgDetail } = useOrganization(selectedOrgId);
  const { data: orgMembers } = useOrgDetailMembers(selectedOrgId);

  const handleSelectOrg = (orgId: string) => {
    setSelectedOrgId(orgId);
    setPanelOpen(true);
  };

  if (!isAdmin) {
    return (
      <div className="space-y-6">
        <PageHeader title="Organizations" />
        <AccessDenied />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Organizations"
        description="View and manage organizations in the system."
      />

      <div className="max-w-sm">
        <Input
          placeholder="Search organizations..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading && <LoadingState variant="table" />}

      {error && (
        <ErrorState
          message="Failed to load organizations."
          onRetry={() => refetch()}
        />
      )}

      {orgsData && (
        <OrgTable
          organizations={orgsData.items}
          onSelect={handleSelectOrg}
        />
      )}

      <OrgDetailPanel
        org={orgDetail ?? null}
        members={orgMembers ?? []}
        open={panelOpen}
        onOpenChange={setPanelOpen}
      />
    </div>
  );
}
