import { describe, it, expect } from "vitest";
import {
  getClassificationConfidenceLevel,
  getClassificationConfidenceColor,
  formatClassificationConfidence,
  getDocTypeLabel,
  isConfidenceActionable,
  METHOD_LABELS,
  METHOD_COLORS,
  type ClassificationMethod,
} from "../classification-types";

describe("classification-types", () => {
  describe("getClassificationConfidenceLevel", () => {
    it("returns high for >= 0.8", () => {
      expect(getClassificationConfidenceLevel(0.8)).toBe("high");
      expect(getClassificationConfidenceLevel(0.95)).toBe("high");
      expect(getClassificationConfidenceLevel(1.0)).toBe("high");
    });

    it("returns medium for >= 0.5 and < 0.8", () => {
      expect(getClassificationConfidenceLevel(0.5)).toBe("medium");
      expect(getClassificationConfidenceLevel(0.79)).toBe("medium");
      expect(getClassificationConfidenceLevel(0.65)).toBe("medium");
    });

    it("returns low for < 0.5", () => {
      expect(getClassificationConfidenceLevel(0.49)).toBe("low");
      expect(getClassificationConfidenceLevel(0.1)).toBe("low");
      expect(getClassificationConfidenceLevel(0)).toBe("low");
    });
  });

  describe("getClassificationConfidenceColor", () => {
    it("returns green for high confidence", () => {
      expect(getClassificationConfidenceColor(0.9)).toBe("text-green-700");
    });

    it("returns amber for medium confidence", () => {
      expect(getClassificationConfidenceColor(0.6)).toBe("text-amber-700");
    });

    it("returns red for low confidence", () => {
      expect(getClassificationConfidenceColor(0.3)).toBe("text-red-700");
    });
  });

  describe("formatClassificationConfidence", () => {
    it("formats as percentage", () => {
      expect(formatClassificationConfidence(0.92)).toBe("92%");
      expect(formatClassificationConfidence(1.0)).toBe("100%");
      expect(formatClassificationConfidence(0)).toBe("0%");
    });

    it("rounds to nearest integer", () => {
      expect(formatClassificationConfidence(0.856)).toBe("86%");
      expect(formatClassificationConfidence(0.854)).toBe("85%");
    });
  });

  describe("getDocTypeLabel", () => {
    it("returns label for known document types", () => {
      expect(getDocTypeLabel("bill_of_lading")).toBe("Bill of Lading");
      expect(getDocTypeLabel("commercial_invoice")).toBe("Commercial Invoice");
      expect(getDocTypeLabel("packing_list")).toBe("Packing List");
    });

    it("returns raw string for unknown types", () => {
      expect(getDocTypeLabel("some_unknown_type")).toBe("some_unknown_type");
    });
  });

  describe("isConfidenceActionable", () => {
    it("returns true for >= 0.5", () => {
      expect(isConfidenceActionable(0.5)).toBe(true);
      expect(isConfidenceActionable(0.9)).toBe(true);
    });

    it("returns false for < 0.5", () => {
      expect(isConfidenceActionable(0.49)).toBe(false);
      expect(isConfidenceActionable(0)).toBe(false);
    });
  });

  describe("METHOD_LABELS", () => {
    it("has labels for all methods", () => {
      const methods: ClassificationMethod[] = ["ai", "keyword", "manual"];
      for (const m of methods) {
        expect(METHOD_LABELS[m]).toBeDefined();
        expect(typeof METHOD_LABELS[m]).toBe("string");
      }
    });

    it("has expected label values", () => {
      expect(METHOD_LABELS.ai).toBe("AI Detected");
      expect(METHOD_LABELS.keyword).toBe("Keyword Match");
      expect(METHOD_LABELS.manual).toBe("Manual");
    });
  });

  describe("METHOD_COLORS", () => {
    it("has color classes for all methods", () => {
      const methods: ClassificationMethod[] = ["ai", "keyword", "manual"];
      for (const m of methods) {
        expect(METHOD_COLORS[m]).toBeDefined();
        expect(typeof METHOD_COLORS[m]).toBe("string");
      }
    });
  });
});
