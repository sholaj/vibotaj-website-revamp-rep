import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemberTable } from "../member-table";
import type { UserResponse } from "@/lib/api/user-types";

const mockUsers: UserResponse[] = [
  {
    id: "u1",
    email: "shola@vibotaj.com",
    full_name: "Shola Jibodu",
    role: "admin",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: null,
    last_login: "2026-02-16T10:00:00Z",
    primary_organization: null,
  },
  {
    id: "u2",
    email: "bolaji@vibotaj.com",
    full_name: "Bolaji Jibodu",
    role: "compliance_officer",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: null,
    last_login: null,
    primary_organization: null,
  },
  {
    id: "u3",
    email: "inactive@test.com",
    full_name: "Inactive User",
    role: "viewer",
    is_active: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: null,
    last_login: null,
    primary_organization: null,
  },
];

describe("MemberTable", () => {
  it("renders member count", () => {
    render(<MemberTable users={mockUsers} />);
    expect(screen.getByText("Team Members (3)")).toBeInTheDocument();
  });

  it("renders member names", () => {
    render(<MemberTable users={mockUsers} />);
    expect(screen.getByText("Shola Jibodu")).toBeInTheDocument();
    expect(screen.getByText("Bolaji Jibodu")).toBeInTheDocument();
  });

  it("renders member emails", () => {
    render(<MemberTable users={mockUsers} />);
    expect(screen.getByText("shola@vibotaj.com")).toBeInTheDocument();
    expect(screen.getByText("bolaji@vibotaj.com")).toBeInTheDocument();
  });

  it("renders role badges", () => {
    render(<MemberTable users={mockUsers} />);
    expect(screen.getByText("Admin")).toBeInTheDocument();
    expect(screen.getByText("Compliance")).toBeInTheDocument();
  });

  it("renders inactive badge for deactivated users", () => {
    render(<MemberTable users={mockUsers} />);
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("renders invite button when canManage is true", () => {
    render(
      <MemberTable users={mockUsers} onInvite={vi.fn()} canManage={true} />,
    );
    expect(screen.getByText("Invite Member")).toBeInTheDocument();
  });

  it("hides invite button when canManage is false", () => {
    render(
      <MemberTable users={mockUsers} onInvite={vi.fn()} canManage={false} />,
    );
    expect(screen.queryByText("Invite Member")).not.toBeInTheDocument();
  });

  it("calls onInvite when invite button clicked", async () => {
    const user = userEvent.setup();
    const onInvite = vi.fn();
    render(
      <MemberTable users={mockUsers} onInvite={onInvite} canManage={true} />,
    );
    await user.click(screen.getByText("Invite Member"));
    expect(onInvite).toHaveBeenCalled();
  });

  it("renders empty state when no users", () => {
    render(<MemberTable users={[]} />);
    expect(screen.getByText("No team members")).toBeInTheDocument();
  });

  it("renders avatar initials", () => {
    render(<MemberTable users={mockUsers} />);
    expect(screen.getByText("S")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
  });
});
