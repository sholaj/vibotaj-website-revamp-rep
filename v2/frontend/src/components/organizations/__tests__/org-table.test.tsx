import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OrgTable } from "../org-table";
import type { OrgListItem } from "@/lib/api/user-types";

const mockOrgs: OrgListItem[] = [
  {
    id: "org1",
    name: "VIBOTAJ Global",
    slug: "vibotaj",
    type: "vibotaj",
    status: "active",
    member_count: 5,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "org2",
    name: "HAGES GmbH",
    slug: "hages",
    type: "buyer",
    status: "active",
    member_count: 3,
    created_at: "2026-01-15T00:00:00Z",
  },
  {
    id: "org3",
    name: "Pending Corp",
    slug: "pending-corp",
    type: "supplier",
    status: "pending_setup",
    member_count: 0,
    created_at: "2026-02-01T00:00:00Z",
  },
];

describe("OrgTable", () => {
  it("renders organization count", () => {
    render(<OrgTable organizations={mockOrgs} />);
    expect(screen.getByText("Organizations (3)")).toBeInTheDocument();
  });

  it("renders organization names", () => {
    render(<OrgTable organizations={mockOrgs} />);
    expect(screen.getByText("VIBOTAJ Global")).toBeInTheDocument();
    expect(screen.getByText("HAGES GmbH")).toBeInTheDocument();
  });

  it("renders type badges", () => {
    render(<OrgTable organizations={mockOrgs} />);
    expect(screen.getByText("Vibotaj")).toBeInTheDocument();
    expect(screen.getByText("Buyer")).toBeInTheDocument();
    expect(screen.getByText("Supplier")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(<OrgTable organizations={mockOrgs} />);
    const activeBadges = screen.getAllByText("Active");
    expect(activeBadges).toHaveLength(2);
    expect(screen.getByText("Pending Setup")).toBeInTheDocument();
  });

  it("renders member counts", () => {
    render(<OrgTable organizations={mockOrgs} />);
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("calls onSelect when org clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<OrgTable organizations={mockOrgs} onSelect={onSelect} />);
    await user.click(screen.getByText("HAGES GmbH"));
    expect(onSelect).toHaveBeenCalledWith("org2");
  });

  it("renders empty state when no organizations", () => {
    render(<OrgTable organizations={[]} />);
    expect(screen.getByText("No organizations")).toBeInTheDocument();
  });
});
