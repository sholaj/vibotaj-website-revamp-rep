import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { OrgProvider, useCurrentOrg } from "../org-context";

// Mock PropelAuth hooks
const mockUser = {
  userId: "user-1",
  email: "shola@vibotaj.com",
  getOrgs: () => [
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
  ],
};

let mockLoading = false;
let mockIsLoggedIn = true;

vi.mock("@propelauth/nextjs/client", () => ({
  useUser: () => ({
    loading: mockLoading,
    isLoggedIn: mockIsLoggedIn,
    user: mockIsLoggedIn ? mockUser : null,
  }),
}));

// Test component that consumes the context
function TestConsumer() {
  const { org, orgId, role, orgs, switchOrg, isLoading } = useCurrentOrg();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="org-name">{org?.orgName ?? "none"}</span>
      <span data-testid="org-id">{orgId ?? "none"}</span>
      <span data-testid="role">{role}</span>
      <span data-testid="org-count">{orgs.length}</span>
      <button onClick={() => switchOrg("org-hages")}>Switch to HAGES</button>
    </div>
  );
}

describe("OrgProvider + useCurrentOrg", () => {
  beforeEach(() => {
    mockLoading = false;
    mockIsLoggedIn = true;
    localStorage.clear();
  });

  it("defaults to the first org when no localStorage", () => {
    render(
      <OrgProvider>
        <TestConsumer />
      </OrgProvider>,
    );

    expect(screen.getByTestId("org-name")).toHaveTextContent("VIBOTAJ Global");
    expect(screen.getByTestId("org-id")).toHaveTextContent("org-vibotaj");
    expect(screen.getByTestId("org-count")).toHaveTextContent("2");
  });

  it("maps Admin role to admin UserRole", () => {
    render(
      <OrgProvider>
        <TestConsumer />
      </OrgProvider>,
    );

    expect(screen.getByTestId("role")).toHaveTextContent("admin");
  });

  it("switches org when switchOrg is called", async () => {
    const user = userEvent.setup();
    render(
      <OrgProvider>
        <TestConsumer />
      </OrgProvider>,
    );

    await user.click(screen.getByText("Switch to HAGES"));

    expect(screen.getByTestId("org-name")).toHaveTextContent("HAGES GmbH");
    expect(screen.getByTestId("org-id")).toHaveTextContent("org-hages");
  });

  it("persists selected org in localStorage", async () => {
    const user = userEvent.setup();
    render(
      <OrgProvider>
        <TestConsumer />
      </OrgProvider>,
    );

    await user.click(screen.getByText("Switch to HAGES"));

    expect(localStorage.getItem("tracehub_current_org")).toBe("org-hages");
  });

  it("restores org from localStorage on mount", () => {
    localStorage.setItem("tracehub_current_org", "org-hages");

    render(
      <OrgProvider>
        <TestConsumer />
      </OrgProvider>,
    );

    expect(screen.getByTestId("org-name")).toHaveTextContent("HAGES GmbH");
  });

  it("falls back to first org if localStorage org not found", () => {
    localStorage.setItem("tracehub_current_org", "org-deleted");

    render(
      <OrgProvider>
        <TestConsumer />
      </OrgProvider>,
    );

    expect(screen.getByTestId("org-name")).toHaveTextContent("VIBOTAJ Global");
  });

  it("shows loading state while auth is loading", () => {
    mockLoading = true;
    mockIsLoggedIn = false;
    render(
      <OrgProvider>
        <TestConsumer />
      </OrgProvider>,
    );

    expect(screen.getByTestId("loading")).toHaveTextContent("true");
    expect(screen.getByTestId("org-name")).toHaveTextContent("none");
  });

  it("shows no org when user is not logged in", () => {
    mockIsLoggedIn = false;
    render(
      <OrgProvider>
        <TestConsumer />
      </OrgProvider>,
    );

    expect(screen.getByTestId("org-name")).toHaveTextContent("none");
    expect(screen.getByTestId("org-count")).toHaveTextContent("0");
    expect(screen.getByTestId("role")).toHaveTextContent("viewer");
  });
});
