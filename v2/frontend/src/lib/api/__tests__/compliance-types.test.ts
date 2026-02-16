import { describe, it, expect } from "vitest";
import {
  getStateLabel,
  isDecisionPassing,
  countActiveFailures,
  getStateColor,
  DECISION_COLORS,
  DECISION_LABELS,
  SEVERITY_COLORS,
  SEVERITY_LABELS,
  STATE_LABELS,
} from "../compliance-types";
import type { RuleResult } from "../compliance-types";

describe("compliance-types helpers", () => {
  describe("getStateLabel", () => {
    it("returns label for known states", () => {
      expect(getStateLabel("DRAFT")).toBe("Draft");
      expect(getStateLabel("UPLOADED")).toBe("Uploaded");
      expect(getStateLabel("VALIDATED")).toBe("Validated");
      expect(getStateLabel("COMPLIANCE_OK")).toBe("Compliance OK");
      expect(getStateLabel("COMPLIANCE_FAILED")).toBe("Compliance Failed");
      expect(getStateLabel("LINKED")).toBe("Linked");
      expect(getStateLabel("ARCHIVED")).toBe("Archived");
    });

    it("returns raw string for unknown states", () => {
      expect(getStateLabel("UNKNOWN_STATE")).toBe("UNKNOWN_STATE");
    });
  });

  describe("isDecisionPassing", () => {
    it("returns true for APPROVE", () => {
      expect(isDecisionPassing("APPROVE")).toBe(true);
    });

    it("returns false for HOLD", () => {
      expect(isDecisionPassing("HOLD")).toBe(false);
    });

    it("returns false for REJECT", () => {
      expect(isDecisionPassing("REJECT")).toBe(false);
    });
  });

  describe("countActiveFailures", () => {
    it("counts non-passed, non-overridden rules", () => {
      const results: RuleResult[] = [
        { rule_id: "R1", rule_name: "Rule 1", passed: true, severity: "ERROR", message: null, field_path: null, document_type: null, checked_at: null },
        { rule_id: "R2", rule_name: "Rule 2", passed: false, severity: "ERROR", message: "Fail", field_path: null, document_type: null, checked_at: null },
        { rule_id: "R3", rule_name: "Rule 3", passed: false, severity: "WARNING", message: "Warn", field_path: null, document_type: null, checked_at: null, is_overridden: true },
      ];
      expect(countActiveFailures(results)).toBe(1);
    });

    it("returns 0 when all passed", () => {
      const results: RuleResult[] = [
        { rule_id: "R1", rule_name: "Rule 1", passed: true, severity: "INFO", message: null, field_path: null, document_type: null, checked_at: null },
      ];
      expect(countActiveFailures(results)).toBe(0);
    });

    it("returns 0 for empty results", () => {
      expect(countActiveFailures([])).toBe(0);
    });
  });

  describe("getStateColor", () => {
    it("returns success for COMPLIANCE_OK", () => {
      expect(getStateColor("COMPLIANCE_OK")).toContain("success");
    });

    it("returns destructive for COMPLIANCE_FAILED", () => {
      expect(getStateColor("COMPLIANCE_FAILED")).toContain("destructive");
    });

    it("returns warning for UPLOADED", () => {
      expect(getStateColor("UPLOADED")).toContain("warning");
    });

    it("returns muted for DRAFT", () => {
      expect(getStateColor("DRAFT")).toContain("muted");
    });

    it("returns foreground for unknown state", () => {
      expect(getStateColor("UNKNOWN")).toContain("foreground");
    });
  });

  describe("constants", () => {
    it("DECISION_COLORS has all 3 decisions", () => {
      expect(Object.keys(DECISION_COLORS)).toEqual(["APPROVE", "HOLD", "REJECT"]);
    });

    it("DECISION_LABELS has all 3 decisions", () => {
      expect(DECISION_LABELS.APPROVE).toBe("Approved");
      expect(DECISION_LABELS.HOLD).toBe("On Hold");
      expect(DECISION_LABELS.REJECT).toBe("Rejected");
    });

    it("SEVERITY_COLORS has ERROR, WARNING, INFO", () => {
      expect(Object.keys(SEVERITY_COLORS)).toEqual(["ERROR", "WARNING", "INFO"]);
    });

    it("SEVERITY_LABELS has ERROR, WARNING, INFO", () => {
      expect(SEVERITY_LABELS.ERROR).toBe("Error");
      expect(SEVERITY_LABELS.WARNING).toBe("Warning");
      expect(SEVERITY_LABELS.INFO).toBe("Info");
    });

    it("STATE_LABELS has 7 states", () => {
      expect(Object.keys(STATE_LABELS).length).toBe(7);
    });
  });
});
