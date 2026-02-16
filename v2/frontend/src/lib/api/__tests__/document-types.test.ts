import { describe, it, expect } from "vitest";
import {
  getComplianceProgress,
  isDocumentComplete,
  type DocumentSummary,
} from "../document-types";

describe("getComplianceProgress", () => {
  it("returns 100 when no documents required", () => {
    const summary: DocumentSummary = {
      total_required: 0,
      total_present: 0,
      missing_types: [],
      pending_validation: [],
    };
    expect(getComplianceProgress(summary)).toBe(100);
  });

  it("returns correct percentage", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 3,
      missing_types: ["bill_of_lading", "packing_list", "certificate_of_origin"],
      pending_validation: [],
    };
    expect(getComplianceProgress(summary)).toBe(50);
  });

  it("returns 100 when all present", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 6,
      missing_types: [],
      pending_validation: [],
    };
    expect(getComplianceProgress(summary)).toBe(100);
  });

  it("rounds to nearest integer", () => {
    const summary: DocumentSummary = {
      total_required: 3,
      total_present: 1,
      missing_types: ["bill_of_lading", "packing_list"],
      pending_validation: [],
    };
    expect(getComplianceProgress(summary)).toBe(33);
  });
});

describe("isDocumentComplete", () => {
  it("returns true when no missing or pending", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 6,
      missing_types: [],
      pending_validation: [],
    };
    expect(isDocumentComplete(summary)).toBe(true);
  });

  it("returns false when missing types exist", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 4,
      missing_types: ["bill_of_lading", "packing_list"],
      pending_validation: [],
    };
    expect(isDocumentComplete(summary)).toBe(false);
  });

  it("returns false when pending validation exists", () => {
    const summary: DocumentSummary = {
      total_required: 6,
      total_present: 6,
      missing_types: [],
      pending_validation: ["commercial_invoice"],
    };
    expect(isDocumentComplete(summary)).toBe(false);
  });
});
