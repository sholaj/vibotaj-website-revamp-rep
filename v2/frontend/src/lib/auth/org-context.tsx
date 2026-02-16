"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { useUser } from "@propelauth/nextjs/client";
import type { OrgMemberInfo } from "@propelauth/nextjs/client";
import type { CurrentOrgContext, UserRole } from "./types";

const STORAGE_KEY = "tracehub_current_org";

/** Map PropelAuth role strings to TraceHub UserRole. */
function mapRole(propelAuthRole: string | undefined): UserRole {
  if (!propelAuthRole) return "viewer";
  const normalized = propelAuthRole.toLowerCase().replace(/\s+/g, "_");
  const roleMap: Record<string, UserRole> = {
    admin: "admin",
    owner: "admin",
    compliance_officer: "compliance_officer",
    compliance: "compliance_officer",
    logistics: "logistics",
    logistics_agent: "logistics",
    buyer: "buyer",
    supplier: "supplier",
    member: "viewer",
    viewer: "viewer",
  };
  return roleMap[normalized] ?? "viewer";
}

const OrgContext = createContext<CurrentOrgContext | null>(null);

export function OrgProvider({ children }: { children: React.ReactNode }) {
  const { loading, isLoggedIn, user } = useUser();

  const orgs = useMemo<OrgMemberInfo[]>(() => {
    if (!isLoggedIn || !user) return [];
    return user.getOrgs();
  }, [isLoggedIn, user]);

  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(STORAGE_KEY);
  });

  const currentOrg = useMemo(() => {
    if (orgs.length === 0) return null;
    // Try to find the stored org
    if (selectedOrgId) {
      const found = orgs.find((o) => o.orgId === selectedOrgId);
      if (found) return found;
    }
    // Fall back to first org
    return orgs[0] ?? null;
  }, [orgs, selectedOrgId]);

  const switchOrg = useCallback(
    (orgId: string) => {
      const found = orgs.find((o) => o.orgId === orgId);
      if (found) {
        setSelectedOrgId(orgId);
        localStorage.setItem(STORAGE_KEY, orgId);
      }
    },
    [orgs],
  );

  const role = useMemo<UserRole>(
    () => mapRole(currentOrg?.userAssignedRole),
    [currentOrg],
  );

  const value = useMemo<CurrentOrgContext>(
    () => ({
      org: currentOrg,
      orgId: currentOrg?.orgId ?? null,
      role,
      orgs,
      switchOrg,
      isLoading: loading,
    }),
    [currentOrg, role, orgs, switchOrg, loading],
  );

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>;
}

export function useCurrentOrg(): CurrentOrgContext {
  const context = useContext(OrgContext);
  if (!context) {
    throw new Error("useCurrentOrg must be used within an OrgProvider");
  }
  return context;
}
