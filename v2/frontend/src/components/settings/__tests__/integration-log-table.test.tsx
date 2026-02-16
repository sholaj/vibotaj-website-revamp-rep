import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { IntegrationLogTable } from "../integration-log-table";
import type { IntegrationLog } from "@/lib/api/integration-types";

describe("IntegrationLogTable", () => {
  const sampleLogs: IntegrationLog[] = [
    {
      id: "1",
      integration_type: "customs",
      provider: "mock",
      method: "check_pre_clearance",
      request_summary: "Pre-clearance: HS 0506 from NG",
      status: "success",
      response_time_ms: 42,
      error_message: null,
      shipment_id: null,
      created_at: "2026-02-16T12:00:00Z",
    },
    {
      id: "2",
      integration_type: "banking",
      provider: "mock",
      method: "verify_lc",
      request_summary: "LC verification: LC-001",
      status: "error",
      response_time_ms: 150,
      error_message: "Timeout",
      shipment_id: null,
      created_at: "2026-02-16T11:00:00Z",
    },
  ];

  it("renders empty state when no logs", () => {
    render(<IntegrationLogTable logs={[]} />);
    expect(screen.getByText("No recent activity")).toBeInTheDocument();
  });

  it("renders table headers", () => {
    render(<IntegrationLogTable logs={sampleLogs} />);
    expect(screen.getByText("Method")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Provider")).toBeInTheDocument();
    expect(screen.getByText("Time (ms)")).toBeInTheDocument();
    expect(screen.getByText("Date")).toBeInTheDocument();
  });

  it("renders log method labels", () => {
    render(<IntegrationLogTable logs={sampleLogs} />);
    expect(screen.getByText("Pre-Clearance Check")).toBeInTheDocument();
    expect(screen.getByText("LC Verification")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(<IntegrationLogTable logs={sampleLogs} />);
    expect(screen.getByText("success")).toBeInTheDocument();
    expect(screen.getByText("error")).toBeInTheDocument();
  });

  it("renders provider names", () => {
    render(<IntegrationLogTable logs={sampleLogs} />);
    const mockCells = screen.getAllByText("mock");
    expect(mockCells.length).toBe(2);
  });

  it("renders response times", () => {
    render(<IntegrationLogTable logs={sampleLogs} />);
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
  });

  it("renders correct number of rows", () => {
    render(<IntegrationLogTable logs={sampleLogs} />);
    const rows = screen.getAllByRole("row");
    // 1 header row + 2 data rows
    expect(rows).toHaveLength(3);
  });
});
