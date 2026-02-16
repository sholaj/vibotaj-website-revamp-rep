import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PendingInvitations } from "../pending-invitations";
import type { Invitation } from "@/lib/api/user-types";

const mockInvitations: Invitation[] = [
  {
    id: "inv1",
    organization_id: "org1",
    organization_name: "Vibotaj",
    email: "new@test.com",
    org_role: "member",
    status: "pending",
    created_at: "2026-02-15T00:00:00Z",
    expires_at: "2026-02-22T00:00:00Z",
    created_by_name: "Shola",
    accepted_at: null,
  },
  {
    id: "inv2",
    organization_id: "org1",
    organization_name: "Vibotaj",
    email: "accepted@test.com",
    org_role: "viewer",
    status: "accepted",
    created_at: "2026-02-10T00:00:00Z",
    expires_at: "2026-02-17T00:00:00Z",
    created_by_name: "Shola",
    accepted_at: "2026-02-11T00:00:00Z",
  },
];

describe("PendingInvitations", () => {
  it("renders pending invitation count", () => {
    render(<PendingInvitations invitations={mockInvitations} />);
    expect(screen.getByText("Pending Invitations (1)")).toBeInTheDocument();
  });

  it("renders pending invitation email", () => {
    render(<PendingInvitations invitations={mockInvitations} />);
    expect(screen.getByText("new@test.com")).toBeInTheDocument();
  });

  it("does not render accepted invitations", () => {
    render(<PendingInvitations invitations={mockInvitations} />);
    expect(screen.queryByText("accepted@test.com")).not.toBeInTheDocument();
  });

  it("renders role badge", () => {
    render(<PendingInvitations invitations={mockInvitations} />);
    expect(screen.getByText("Member")).toBeInTheDocument();
  });

  it("renders revoke button", () => {
    render(
      <PendingInvitations invitations={mockInvitations} onRevoke={vi.fn()} />,
    );
    expect(screen.getByText("Revoke")).toBeInTheDocument();
  });

  it("calls onRevoke with invitation id", async () => {
    const user = userEvent.setup();
    const onRevoke = vi.fn();
    render(
      <PendingInvitations invitations={mockInvitations} onRevoke={onRevoke} />,
    );
    await user.click(screen.getByText("Revoke"));
    expect(onRevoke).toHaveBeenCalledWith("inv1");
  });

  it("returns null when no pending invitations", () => {
    const accepted = mockInvitations.filter((i) => i.status !== "pending");
    const { container } = render(
      <PendingInvitations invitations={accepted} />,
    );
    expect(container.innerHTML).toBe("");
  });
});
