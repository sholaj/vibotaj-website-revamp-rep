import {
  BarChart3,
  Building2,
  FileText,
  Package,
  Settings,
  ShieldCheck,
  Users,
  type LucideIcon,
} from "lucide-react";

export type UserRole =
  | "admin"
  | "compliance_officer"
  | "logistics"
  | "buyer"
  | "supplier"
  | "viewer";

export interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  roles: readonly UserRole[];
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

const ALL_ROLES: readonly UserRole[] = [
  "admin",
  "compliance_officer",
  "logistics",
  "buyer",
  "supplier",
  "viewer",
] as const;

const OPERATIONAL_ROLES: readonly UserRole[] = [
  "admin",
  "compliance_officer",
  "logistics",
  "buyer",
  "supplier",
] as const;

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Operations",
    items: [
      {
        name: "Dashboard",
        href: "/dashboard",
        icon: BarChart3,
        roles: ALL_ROLES,
      },
      {
        name: "Shipments",
        href: "/shipments",
        icon: Package,
        roles: ALL_ROLES,
      },
      {
        name: "Documents",
        href: "/documents",
        icon: FileText,
        roles: OPERATIONAL_ROLES,
      },
    ],
  },
  {
    label: "Compliance",
    items: [
      {
        name: "Compliance",
        href: "/compliance",
        icon: ShieldCheck,
        roles: ["admin", "compliance_officer"],
      },
      {
        name: "Analytics",
        href: "/analytics",
        icon: BarChart3,
        roles: ["admin", "compliance_officer"],
      },
    ],
  },
  {
    label: "Admin",
    items: [
      { name: "Users", href: "/users", icon: Users, roles: ["admin"] },
      {
        name: "Organizations",
        href: "/organizations",
        icon: Building2,
        roles: ["admin"],
      },
      { name: "Settings", href: "/settings", icon: Settings, roles: ["admin"] },
    ],
  },
];

export function getNavGroupsForRole(role: UserRole): NavGroup[] {
  return NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => item.roles.includes(role)),
  })).filter((group) => group.items.length > 0);
}
