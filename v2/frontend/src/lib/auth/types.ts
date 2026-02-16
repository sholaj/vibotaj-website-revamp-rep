"use client";

export type { User, OrgMemberInfo, UseUser } from "@propelauth/nextjs/client";

export type UserRole =
  | "admin"
  | "compliance_officer"
  | "logistics"
  | "buyer"
  | "supplier"
  | "viewer";

export interface CurrentOrgContext {
  /** The currently active organization membership info */
  org: import("@propelauth/nextjs/client").OrgMemberInfo | null;
  /** Shortcut: org.orgId */
  orgId: string | null;
  /** User's role in the current org, defaults to "viewer" */
  role: UserRole;
  /** All organizations the user belongs to */
  orgs: import("@propelauth/nextjs/client").OrgMemberInfo[];
  /** Switch to a different organization by ID */
  switchOrg: (orgId: string) => void;
  /** True while auth/org data is loading */
  isLoading: boolean;
}
