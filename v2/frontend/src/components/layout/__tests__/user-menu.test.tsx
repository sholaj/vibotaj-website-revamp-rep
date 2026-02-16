import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { UserMenu } from "../user-menu";

const mockLogout = vi.fn();
const mockGetOrgs = vi.fn().mockReturnValue([
  {
    orgId: "org-1",
    orgName: "VIBOTAJ Global",
    userAssignedRole: "Admin",
    orgMetadata: {},
    userPermissions: [],
  },
]);

let mockUserState = {
  loading: false,
  isLoggedIn: true,
  user: {
    userId: "user-1",
    email: "shola@vibotaj.com",
    firstName: "Shola",
    lastName: "Adebowale",
    getOrgs: mockGetOrgs,
  },
};

vi.mock("@propelauth/nextjs/client", () => ({
  useUser: () => mockUserState,
  useLogoutFunction: () => mockLogout,
}));

vi.mock("@/lib/auth/org-context", () => ({
  useCurrentOrg: () => ({
    org: {
      orgId: "org-1",
      orgName: "VIBOTAJ Global",
      userAssignedRole: "Admin",
    },
    role: "admin" as const,
    orgs: mockGetOrgs(),
    orgId: "org-1",
    switchOrg: vi.fn(),
    isLoading: false,
  }),
}));

describe("UserMenu", () => {
  beforeEach(() => {
    mockLogout.mockClear();
  });

  it("renders user avatar button", () => {
    render(<UserMenu />);
    expect(
      screen.getByRole("button", { name: /user menu/i }),
    ).toBeInTheDocument();
  });

  it("shows user name and email in dropdown", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button", { name: /user menu/i }));

    expect(screen.getByText("Shola Adebowale")).toBeInTheDocument();
    expect(screen.getByText("shola@vibotaj.com")).toBeInTheDocument();
  });

  it("shows role badge in dropdown", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button", { name: /user menu/i }));

    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("shows account settings menu item", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button", { name: /user menu/i }));

    expect(screen.getByText("Account Settings")).toBeInTheDocument();
  });

  it("calls logout when log out clicked", async () => {
    const user = userEvent.setup();
    render(<UserMenu />);

    await user.click(screen.getByRole("button", { name: /user menu/i }));
    await user.click(screen.getByText("Log out"));

    expect(mockLogout).toHaveBeenCalled();
  });

  it("renders nothing when not logged in", () => {
    mockUserState = {
      loading: false,
      isLoggedIn: false,
      user: null as never,
    };
    const { container } = render(<UserMenu />);
    expect(container.innerHTML).toBe("");
  });
});
