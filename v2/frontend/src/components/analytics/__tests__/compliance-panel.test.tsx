import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CompliancePanel } from "../compliance-panel";
import type { ComplianceMetrics } from "@/lib/api/analytics-types";

const mockMetrics: ComplianceMetrics = {
  compliant_rate: 85,
  eudr_coverage: 70,
  shipments_needing_attention: 3,
  failed_documents: 2,
  issues_summary: { missing_documents: 1, failed_validation: 1, expiring_certificates: 0 },
};

describe("CompliancePanel", () => {
  it("renders title", () => {
    render(<CompliancePanel metrics={mockMetrics} />);
    expect(screen.getByText("Compliance Overview")).toBeInTheDocument();
  });

  it("renders overall compliance ring", () => {
    render(<CompliancePanel metrics={mockMetrics} />);
    expect(screen.getByText("Overall Compliance")).toBeInTheDocument();
  });

  it("renders EUDR coverage ring", () => {
    render(<CompliancePanel metrics={mockMetrics} />);
    expect(screen.getByText("EUDR Coverage")).toBeInTheDocument();
  });

  it("renders percentage values", () => {
    render(<CompliancePanel metrics={mockMetrics} />);
    const ringValues = screen.getAllByTestId("ring-value");
    expect(ringValues[0]!.textContent).toBe("85%");
    expect(ringValues[1]!.textContent).toBe("70%");
  });

  it("renders shipments needing attention", () => {
    render(<CompliancePanel metrics={mockMetrics} />);
    expect(screen.getByText("Shipments needing attention")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders failed documents count", () => {
    render(<CompliancePanel metrics={mockMetrics} />);
    expect(screen.getByText("Failed documents")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });
});
