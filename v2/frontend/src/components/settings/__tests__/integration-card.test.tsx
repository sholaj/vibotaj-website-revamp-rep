import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { IntegrationCard } from "../integration-card";
import type { IntegrationConfig } from "@/lib/api/integration-types";

describe("IntegrationCard", () => {
  const defaultProps = {
    type: "customs" as const,
    config: null,
    onTestConnection: vi.fn(),
    isTesting: false,
    testResult: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders integration type label", () => {
    render(<IntegrationCard {...defaultProps} />);
    expect(screen.getByText("Customs")).toBeInTheDocument();
  });

  it("renders description", () => {
    render(<IntegrationCard {...defaultProps} />);
    expect(
      screen.getByText(/Pre-clearance checks/),
    ).toBeInTheDocument();
  });

  it("shows 'Not Tested' status for null config", () => {
    render(<IntegrationCard {...defaultProps} />);
    expect(screen.getByText("Not Tested")).toBeInTheDocument();
  });

  it("shows 'Not configured' provider for null config", () => {
    render(<IntegrationCard {...defaultProps} />);
    expect(screen.getByText("Not configured")).toBeInTheDocument();
  });

  it("shows 'Connected' for successful test", () => {
    const config: IntegrationConfig = {
      id: "1",
      organization_id: "org-1",
      integration_type: "customs",
      provider: "mock",
      is_active: true,
      last_tested_at: "2026-02-16T12:00:00Z",
      last_test_success: true,
      created_at: "2026-02-16T12:00:00Z",
      updated_at: "2026-02-16T12:00:00Z",
    };
    render(<IntegrationCard {...defaultProps} config={config} />);
    expect(screen.getByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("mock")).toBeInTheDocument();
  });

  it("shows 'Disconnected' for failed test", () => {
    const config: IntegrationConfig = {
      id: "1",
      organization_id: "org-1",
      integration_type: "customs",
      provider: "ncs",
      is_active: true,
      last_tested_at: "2026-02-16T12:00:00Z",
      last_test_success: false,
      created_at: "2026-02-16T12:00:00Z",
      updated_at: "2026-02-16T12:00:00Z",
    };
    render(<IntegrationCard {...defaultProps} config={config} />);
    expect(screen.getByText("Disconnected")).toBeInTheDocument();
  });

  it("renders test connection button", () => {
    render(<IntegrationCard {...defaultProps} />);
    const btn = screen.getByRole("button", { name: /Test Connection/ });
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
  });

  it("calls onTestConnection when button clicked", async () => {
    const user = userEvent.setup();
    render(<IntegrationCard {...defaultProps} />);
    await user.click(screen.getByRole("button", { name: /Test Connection/ }));
    expect(defaultProps.onTestConnection).toHaveBeenCalledWith("customs");
  });

  it("shows loading state when testing", () => {
    render(<IntegrationCard {...defaultProps} isTesting={true} />);
    expect(screen.getByText("Testing...")).toBeInTheDocument();
  });

  it("shows success test result", () => {
    render(
      <IntegrationCard
        {...defaultProps}
        testResult={{ success: true, message: "Connection successful" }}
      />,
    );
    expect(screen.getByText("Connection successful")).toBeInTheDocument();
  });

  it("shows error test result", () => {
    render(
      <IntegrationCard
        {...defaultProps}
        testResult={{ success: false, message: "Connection failed" }}
      />,
    );
    expect(screen.getByText("Connection failed")).toBeInTheDocument();
  });

  it("renders banking type correctly", () => {
    render(<IntegrationCard {...defaultProps} type="banking" />);
    expect(screen.getByText("Banking")).toBeInTheDocument();
    expect(
      screen.getByText(/Letter of Credit/),
    ).toBeInTheDocument();
  });

  it("shows Active status for active config", () => {
    const config: IntegrationConfig = {
      id: "1",
      organization_id: "org-1",
      integration_type: "customs",
      provider: "mock",
      is_active: true,
      last_tested_at: null,
      last_test_success: null,
      created_at: "2026-02-16T12:00:00Z",
      updated_at: "2026-02-16T12:00:00Z",
    };
    render(<IntegrationCard {...defaultProps} config={config} />);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("shows Inactive status for inactive config", () => {
    const config: IntegrationConfig = {
      id: "1",
      organization_id: "org-1",
      integration_type: "customs",
      provider: "mock",
      is_active: false,
      last_tested_at: null,
      last_test_success: null,
      created_at: "2026-02-16T12:00:00Z",
      updated_at: "2026-02-16T12:00:00Z",
    };
    render(<IntegrationCard {...defaultProps} config={config} />);
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });
});
