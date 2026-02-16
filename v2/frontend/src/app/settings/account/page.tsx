"use client";

import { ExternalLink, Mail, Shield, Building2 } from "lucide-react";
import { useUser } from "@propelauth/nextjs/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/domain/page-header";
import { StatusBadge } from "@/components/domain/status-badge";
import { LoadingState } from "@/components/domain/loading-state";
import { useCurrentOrg } from "@/lib/auth/org-context";

export default function AccountSettingsPage() {
  const { loading, isLoggedIn, user } = useUser();
  const { role, orgs } = useCurrentOrg();

  if (loading || !isLoggedIn || !user) {
    return (
      <div className="space-y-6">
        <PageHeader title="Account Settings" />
        <LoadingState variant="detail" />
      </div>
    );
  }

  const authUrl = process.env.NEXT_PUBLIC_PROPELAUTH_URL;
  const accountUrl = authUrl ? `${authUrl}/account` : undefined;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Account Settings"
        description="Manage your account and organization memberships"
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
          { label: "Account" },
        ]}
      />

      {/* Profile info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <Mail className="text-muted-foreground h-4 w-4" />
            <div>
              <p className="text-sm font-medium">Email</p>
              <p className="text-muted-foreground text-sm">{user.email}</p>
            </div>
          </div>
          {user.firstName && (
            <div className="flex items-center gap-3">
              <Shield className="text-muted-foreground h-4 w-4" />
              <div>
                <p className="text-sm font-medium">Name</p>
                <p className="text-muted-foreground text-sm">
                  {user.firstName} {user.lastName}
                </p>
              </div>
            </div>
          )}
          <div className="flex items-center gap-3">
            <Shield className="text-muted-foreground h-4 w-4" />
            <div>
              <p className="text-sm font-medium">Current Role</p>
              <div className="mt-1">
                <StatusBadge variant="role" status={role} />
              </div>
            </div>
          </div>
          <Separator />
          {accountUrl && (
            <Button variant="outline" asChild>
              <a href={accountUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                Manage Account (Password, MFA)
              </a>
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Org memberships */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Organizations</CardTitle>
        </CardHeader>
        <CardContent>
          {orgs.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              You are not a member of any organization. Contact your
              administrator.
            </p>
          ) : (
            <div className="space-y-3">
              {orgs.map((org) => (
                <div
                  key={org.orgId}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <Building2 className="text-muted-foreground h-4 w-4" />
                    <div>
                      <p className="text-sm font-medium">{org.orgName}</p>
                      <p className="text-muted-foreground text-xs">
                        {org.userAssignedRole}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
