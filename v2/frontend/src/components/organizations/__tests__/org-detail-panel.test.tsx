import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { OrgDetailPanel } from "../org-detail-panel";
import type { OrgDetail, Member } from "@/lib/api/user-types";

const mockOrg: OrgDetail = {
  id: "org1",
  name: "VIBOTAJ Global",
  slug: "vibotaj",
  type: "vibotaj",
  status: "active",
  contact_email: "info@vibotaj.com",
  contact_phone: "+234 800 000 0000",
  member_count: 5,
  shipment_count: 12,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
};

const mockMembers: Member[] = [
  {
    id: "m1",
    user_id: "u1",
    organization_id: "org1",
    email: "shola@vibotaj.com",
    full_name: "Shola Jibodu",
    org_role: "admin",
    status: "active",
    is_primary: true,
    joined_at: "2026-01-01T00:00:00Z",
    last_active_at: null,
    invited_by: null,
  },
  {
    id: "m2",
    user_id: "u2",
    organization_id: "org1",
    email: "bolaji@vibotaj.com",
    full_name: "Bolaji Jibodu",
    org_role: "manager",
    status: "active",
    is_primary: false,
    joined_at: "2026-01-15T00:00:00Z",
    last_active_at: null,
    invited_by: null,
  },
];

describe("OrgDetailPanel", () => {
  it("renders org name in header", () => {
    render(
      <OrgDetailPanel
        org={mockOrg}
        members={mockMembers}
        open={true}
        onOpenChange={vi.fn()}
      />,
    );
    expect(screen.getByText("VIBOTAJ Global")).toBeInTheDocument();
  });

  it("renders type and status badges", () => {
    render(
      <OrgDetailPanel
        org={mockOrg}
        members={mockMembers}
        open={true}
        onOpenChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Vibotaj")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders contact email", () => {
    render(
      <OrgDetailPanel
        org={mockOrg}
        members={mockMembers}
        open={true}
        onOpenChange={vi.fn()}
      />,
    );
    expect(screen.getByText("info@vibotaj.com")).toBeInTheDocument();
  });

  it("renders contact phone", () => {
    render(
      <OrgDetailPanel
        org={mockOrg}
        members={mockMembers}
        open={true}
        onOpenChange={vi.fn()}
      />,
    );
    expect(screen.getByText("+234 800 000 0000")).toBeInTheDocument();
  });

  it("renders member count section", () => {
    render(
      <OrgDetailPanel
        org={mockOrg}
        members={mockMembers}
        open={true}
        onOpenChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Members (2)")).toBeInTheDocument();
  });

  it("renders member names", () => {
    render(
      <OrgDetailPanel
        org={mockOrg}
        members={mockMembers}
        open={true}
        onOpenChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Shola Jibodu")).toBeInTheDocument();
    expect(screen.getByText("Bolaji Jibodu")).toBeInTheDocument();
  });

  it("renders member roles", () => {
    render(
      <OrgDetailPanel
        org={mockOrg}
        members={mockMembers}
        open={true}
        onOpenChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Admin")).toBeInTheDocument();
    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("renders nothing when org is null", () => {
    const { container } = render(
      <OrgDetailPanel
        org={null}
        members={[]}
        open={true}
        onOpenChange={vi.fn()}
      />,
    );
    expect(container.innerHTML).toBe("");
  });
});
