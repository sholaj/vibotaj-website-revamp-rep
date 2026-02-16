import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ComplianceStatus } from "../compliance-status";
import type { DocumentSummary } from "@/lib/api/document-types";

describe("ComplianceStatus", () => {
  it("renders Complete badge when all docs present", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 6,
      missing_types: [],
      pending_validation: [],
    };
    render(<ComplianceStatus summary={summary} />);
    expect(screen.getByText("Complete")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("renders Incomplete badge when docs missing", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 4,
      missing_types: ["bill_of_lading", "packing_list"],
      pending_validation: [],
    };
    render(<ComplianceStatus summary={summary} />);
    expect(screen.getByText("Incomplete")).toBeInTheDocument();
    expect(screen.getByText("67%")).toBeInTheDocument();
  });

  it("renders missing document types", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 4,
      missing_types: ["bill_of_lading", "certificate_of_origin"],
      pending_validation: [],
    };
    render(<ComplianceStatus summary={summary} />);
    expect(screen.getByText("Bill of Lading")).toBeInTheDocument();
    expect(screen.getByText("Certificate of Origin")).toBeInTheDocument();
  });

  it("renders pending validation section", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 6,
      missing_types: [],
      pending_validation: ["commercial_invoice"],
    };
    render(<ComplianceStatus summary={summary} />);
    expect(screen.getByText("Pending Validation")).toBeInTheDocument();
    expect(screen.getByText("Commercial Invoice")).toBeInTheDocument();
  });

  it("renders progress fraction", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 3,
      missing_types: ["bill_of_lading", "packing_list", "certificate_of_origin"],
      pending_validation: [],
    };
    render(<ComplianceStatus summary={summary} />);
    expect(screen.getByText("3 / 6 documents")).toBeInTheDocument();
  });
});
