import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ShipmentComplianceCard } from "../shipment-compliance-card";
import type {
  ComplianceSummaryCount,
  ComplianceOverride,
} from "@/lib/api/compliance-types";

const mockSummary: ComplianceSummaryCount = {
  total_rules: 15,
  passed: 12,
  failed: 2,
  warnings: 1,
};

const mockOverride: ComplianceOverride = {
  reason: "Admin approved after manual review",
  overridden_by: "admin@vibotaj.com",
  overridden_at: "2026-02-16T10:00:00Z",
};

describe("ShipmentComplianceCard", () => {
  it("renders decision badge for APPROVE", () => {
    render(
      <ShipmentComplianceCard
        decision="APPROVE"
        summary={mockSummary}
        override={null}
      />,
    );
    expect(screen.getByTestId("decision-badge")).toHaveTextContent("Approved");
  });

  it("renders decision badge for HOLD", () => {
    render(
      <ShipmentComplianceCard
        decision="HOLD"
        summary={mockSummary}
        override={null}
      />,
    );
    expect(screen.getByTestId("decision-badge")).toHaveTextContent("On Hold");
  });

  it("renders decision badge for REJECT", () => {
    render(
      <ShipmentComplianceCard
        decision="REJECT"
        summary={mockSummary}
        override={null}
      />,
    );
    expect(screen.getByTestId("decision-badge")).toHaveTextContent("Rejected");
  });

  it("renders summary counts", () => {
    render(
      <ShipmentComplianceCard
        decision="HOLD"
        summary={mockSummary}
        override={null}
      />,
    );
    expect(screen.getByTestId("total-rules")).toHaveTextContent("15");
    expect(screen.getByTestId("passed-count")).toHaveTextContent("12");
    expect(screen.getByTestId("failed-count")).toHaveTextContent("2");
    expect(screen.getByTestId("warning-count")).toHaveTextContent("1");
  });

  it("renders override info when present", () => {
    render(
      <ShipmentComplianceCard
        decision="APPROVE"
        summary={mockSummary}
        override={mockOverride}
      />,
    );
    expect(
      screen.getByText("Compliance Override Active"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Admin approved after manual review"),
    ).toBeInTheDocument();
    expect(screen.getByText("By: admin@vibotaj.com")).toBeInTheDocument();
  });

  it("does not render override info when null", () => {
    render(
      <ShipmentComplianceCard
        decision="HOLD"
        summary={mockSummary}
        override={null}
      />,
    );
    expect(
      screen.queryByText("Compliance Override Active"),
    ).not.toBeInTheDocument();
  });

  it("renders override button when canOverride and not approved", () => {
    const onOverride = vi.fn();
    render(
      <ShipmentComplianceCard
        decision="REJECT"
        summary={mockSummary}
        override={null}
        canOverride={true}
        onOverride={onOverride}
      />,
    );
    expect(
      screen.getByText("Override Compliance"),
    ).toBeInTheDocument();
  });

  it("does not render override button when already approved", () => {
    render(
      <ShipmentComplianceCard
        decision="APPROVE"
        summary={mockSummary}
        override={null}
        canOverride={true}
        onOverride={vi.fn()}
      />,
    );
    expect(
      screen.queryByText("Override Compliance"),
    ).not.toBeInTheDocument();
  });

  it("calls onOverride when button clicked", async () => {
    const user = userEvent.setup();
    const onOverride = vi.fn();
    render(
      <ShipmentComplianceCard
        decision="HOLD"
        summary={mockSummary}
        override={null}
        canOverride={true}
        onOverride={onOverride}
      />,
    );
    await user.click(screen.getByText("Override Compliance"));
    expect(onOverride).toHaveBeenCalledOnce();
  });
});
