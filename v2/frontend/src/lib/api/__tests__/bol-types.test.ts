import { describe, it, expect } from "vitest";
import {
  isParsed,
  isBol,
  getConfidenceLevel,
  getConfidenceColor,
  formatConfidence,
  countUpdates,
  countPlaceholders,
  getOrderedFieldKeys,
  PARSE_STATUS_LABELS,
  PARSE_STATUS_COLORS,
  BOL_FIELD_LABELS,
  SYNC_FIELD_LABELS,
} from "../bol-types";
import type { BolParseStatus, BolField, SyncChange } from "../bol-types";

describe("bol-types helpers", () => {
  describe("isParsed", () => {
    it("returns true for parsed status", () => {
      expect(isParsed("parsed")).toBe(true);
    });

    it("returns false for other statuses", () => {
      expect(isParsed("pending")).toBe(false);
      expect(isParsed("failed")).toBe(false);
      expect(isParsed("not_bol")).toBe(false);
    });
  });

  describe("isBol", () => {
    it("returns true for all BoL statuses", () => {
      expect(isBol("parsed")).toBe(true);
      expect(isBol("pending")).toBe(true);
      expect(isBol("failed")).toBe(true);
    });

    it("returns false for not_bol", () => {
      expect(isBol("not_bol")).toBe(false);
    });
  });

  describe("getConfidenceLevel", () => {
    it("returns high for >= 0.8", () => {
      expect(getConfidenceLevel(0.95)).toBe("high");
      expect(getConfidenceLevel(0.8)).toBe("high");
    });

    it("returns medium for >= 0.5 and < 0.8", () => {
      expect(getConfidenceLevel(0.79)).toBe("medium");
      expect(getConfidenceLevel(0.5)).toBe("medium");
    });

    it("returns low for < 0.5", () => {
      expect(getConfidenceLevel(0.49)).toBe("low");
      expect(getConfidenceLevel(0)).toBe("low");
    });
  });

  describe("getConfidenceColor", () => {
    it("returns green for high confidence", () => {
      expect(getConfidenceColor(0.95)).toContain("green");
    });

    it("returns amber for medium confidence", () => {
      expect(getConfidenceColor(0.6)).toContain("amber");
    });

    it("returns red for low confidence", () => {
      expect(getConfidenceColor(0.3)).toContain("red");
    });
  });

  describe("formatConfidence", () => {
    it("formats as percentage", () => {
      expect(formatConfidence(0.85)).toBe("85%");
      expect(formatConfidence(1.0)).toBe("100%");
      expect(formatConfidence(0)).toBe("0%");
    });

    it("rounds to nearest integer", () => {
      expect(formatConfidence(0.856)).toBe("86%");
      expect(formatConfidence(0.854)).toBe("85%");
    });
  });

  describe("countUpdates", () => {
    it("counts changes with will_update true", () => {
      const changes: SyncChange[] = [
        { field: "bl_number", current: null, new_value: "MSC123", is_placeholder: false, will_update: true },
        { field: "vessel_name", current: "OLD", new_value: "NEW", is_placeholder: false, will_update: false },
        { field: "container_number", current: "TBD", new_value: "MSCU123", is_placeholder: true, will_update: true },
      ];
      expect(countUpdates(changes)).toBe(2);
    });

    it("returns 0 for empty changes", () => {
      expect(countUpdates([])).toBe(0);
    });
  });

  describe("countPlaceholders", () => {
    it("counts placeholder changes", () => {
      const changes: SyncChange[] = [
        { field: "bl_number", current: null, new_value: "MSC123", is_placeholder: false, will_update: true },
        { field: "container_number", current: "HAGES-CNT-001", new_value: "MSCU123", is_placeholder: true, will_update: true },
      ];
      expect(countPlaceholders(changes)).toBe(1);
    });
  });

  describe("getOrderedFieldKeys", () => {
    it("returns keys in display order", () => {
      const fields: Record<string, BolField> = {
        vessel_name: { value: "RHINE MAERSK", confidence: 0.8 },
        bol_number: { value: "MSC123", confidence: 0.95 },
        shipper: { value: "VIBOTAJ", confidence: 0.9 },
      };
      const ordered = getOrderedFieldKeys(fields);
      expect(ordered).toEqual(["bol_number", "shipper", "vessel_name"]);
    });

    it("filters out missing keys", () => {
      const fields: Record<string, BolField> = {
        bol_number: { value: "MSC123", confidence: 0.95 },
      };
      const ordered = getOrderedFieldKeys(fields);
      expect(ordered).toEqual(["bol_number"]);
    });

    it("returns empty for empty fields", () => {
      expect(getOrderedFieldKeys({})).toEqual([]);
    });
  });

  describe("constants", () => {
    it("PARSE_STATUS_LABELS covers all statuses", () => {
      const statuses: BolParseStatus[] = ["parsed", "pending", "failed", "not_bol"];
      for (const s of statuses) {
        expect(PARSE_STATUS_LABELS[s]).toBeTruthy();
      }
    });

    it("PARSE_STATUS_COLORS covers all statuses", () => {
      const statuses: BolParseStatus[] = ["parsed", "pending", "failed", "not_bol"];
      for (const s of statuses) {
        expect(PARSE_STATUS_COLORS[s]).toBeTruthy();
      }
    });

    it("BOL_FIELD_LABELS covers core fields", () => {
      expect(BOL_FIELD_LABELS["bol_number"]).toBe("B/L Number");
      expect(BOL_FIELD_LABELS["shipper"]).toBe("Shipper");
      expect(BOL_FIELD_LABELS["consignee"]).toBe("Consignee");
      expect(BOL_FIELD_LABELS["container_number"]).toBe("Container");
    });

    it("SYNC_FIELD_LABELS covers sync fields", () => {
      expect(SYNC_FIELD_LABELS["bl_number"]).toBe("B/L Number");
      expect(SYNC_FIELD_LABELS["container_number"]).toBe("Container Number");
      expect(SYNC_FIELD_LABELS["vessel_name"]).toBe("Vessel Name");
    });
  });
});
