import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { OrgSwitcher } from "../org-switcher";

const mockSwitchOrg = vi.fn();

const mockOrgs = [
  {
    orgId: "org-vibotaj",
    orgName: "VIBOTAJ Global",
    urlSafeOrgName: "vibotaj-global",
    userAssignedRole: "Admin",
    orgMetadata: {},
    userPermissions: [],
  },
  {
    orgId: "org-hages",
    orgName: "HAGES GmbH",
    urlSafeOrgName: "hages-gmbh",
    userAssignedRole: "Member",
    orgMetadata: {},
    userPermissions: [],
  },
  {
    orgId: "org-wita",
    orgName: "Witatrade BV",
    urlSafeOrgName: "witatrade-bv",
    userAssignedRole: "Member",
    orgMetadata: {},
    userPermissions: [],
  },
];

vi.mock("@/lib/auth/org-context", () => ({
  useCurrentOrg: () => ({
    org: mockOrgs[0],
    orgId: "org-vibotaj",
    role: "admin" as const,
    orgs: mockOrgs,
    switchOrg: mockSwitchOrg,
    isLoading: false,
  }),
}));

describe("OrgSwitcher", () => {
  beforeEach(() => {
    mockSwitchOrg.mockClear();
  });

  it("renders current org name", () => {
    render(<OrgSwitcher />);
    expect(screen.getByText("VIBOTAJ Global")).toBeInTheDocument();
  });

  it("shows all orgs in dropdown when clicked", async () => {
    const user = userEvent.setup();
    render(<OrgSwitcher />);

    await user.click(
      screen.getByRole("button", { name: /switch organization/i }),
    );

    expect(screen.getByText("HAGES GmbH")).toBeInTheDocument();
    expect(screen.getByText("Witatrade BV")).toBeInTheDocument();
  });

  it("calls switchOrg when another org is selected", async () => {
    const user = userEvent.setup();
    render(<OrgSwitcher />);

    await user.click(
      screen.getByRole("button", { name: /switch organization/i }),
    );
    await user.click(screen.getByText("HAGES GmbH"));

    expect(mockSwitchOrg).toHaveBeenCalledWith("org-hages");
  });

  it("shows org initials as avatar fallback", () => {
    render(<OrgSwitcher />);
    // "VIBOTAJ Global" → "VG" initials
    expect(screen.getByText("VG")).toBeInTheDocument();
  });
});
