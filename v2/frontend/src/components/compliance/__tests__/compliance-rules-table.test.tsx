import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ComplianceRulesTable } from "../compliance-rules-table";
import type { RuleResult } from "@/lib/api/compliance-types";

const mockResults: RuleResult[] = [
  {
    rule_id: "BOL-001",
    rule_name: "Shipper name required",
    passed: true,
    severity: "ERROR",
    message: null,
    field_path: "shipper.name",
    document_type: "bill_of_lading",
    checked_at: "2026-02-16T10:00:00Z",
  },
  {
    rule_id: "PRESENCE_001",
    rule_name: "Required documents present",
    passed: false,
    severity: "ERROR",
    message: "Missing: Veterinary Health Certificate",
    field_path: null,
    document_type: null,
    checked_at: "2026-02-16T10:00:00Z",
  },
  {
    rule_id: "BOL-005",
    rule_name: "Container number format",
    passed: false,
    severity: "WARNING",
    message: "Container number does not match ISO 6346",
    field_path: "container_number",
    document_type: "bill_of_lading",
    checked_at: "2026-02-16T10:00:00Z",
    is_overridden: true,
    override_reason: "Manual format accepted",
  },
];

describe("ComplianceRulesTable", () => {
  it("renders empty state when no results", () => {
    render(<ComplianceRulesTable results={[]} />);
    expect(
      screen.getByText("No compliance rules have been evaluated yet."),
    ).toBeInTheDocument();
  });

  it("renders rule names", () => {
    render(<ComplianceRulesTable results={mockResults} />);
    expect(screen.getByText("Shipper name required")).toBeInTheDocument();
    expect(screen.getByText("Required documents present")).toBeInTheDocument();
  });

  it("renders rule IDs", () => {
    render(<ComplianceRulesTable results={mockResults} />);
    expect(screen.getByText("BOL-001")).toBeInTheDocument();
    expect(screen.getByText("PRESENCE_001")).toBeInTheDocument();
  });

  it("renders severity badges", () => {
    render(<ComplianceRulesTable results={mockResults} />);
    const errorBadges = screen.getAllByText("Error");
    expect(errorBadges.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Warning")).toBeInTheDocument();
  });

  it("renders passed/failed summary", () => {
    render(<ComplianceRulesTable results={mockResults} />);
    expect(screen.getByText("1 passed, 1 failed")).toBeInTheDocument();
  });

  it("renders failure message", () => {
    render(<ComplianceRulesTable results={mockResults} />);
    expect(
      screen.getByText("Missing: Veterinary Health Certificate"),
    ).toBeInTheDocument();
  });

  it("renders override reason for overridden rules", () => {
    render(<ComplianceRulesTable results={mockResults} />);
    expect(
      screen.getByText(/Manual format accepted/),
    ).toBeInTheDocument();
  });

  it("renders data-testid for each rule row", () => {
    render(<ComplianceRulesTable results={mockResults} />);
    expect(screen.getByTestId("rule-BOL-001")).toBeInTheDocument();
    expect(screen.getByTestId("rule-PRESENCE_001")).toBeInTheDocument();
    expect(screen.getByTestId("rule-BOL-005")).toBeInTheDocument();
  });
});
