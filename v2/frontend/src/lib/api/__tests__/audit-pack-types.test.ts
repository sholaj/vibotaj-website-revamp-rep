import { describe, it, expect } from "vitest";
import {
  isPackReady,
  isPackActionable,
  getDocumentContentCount,
  formatGeneratedAt,
  PACK_STATUS_LABELS,
  PACK_STATUS_COLORS,
  CONTENT_TYPE_ICONS,
} from "../audit-pack-types";
import type { AuditPackContent, AuditPackStatus } from "../audit-pack-types";

describe("audit-pack-types helpers", () => {
  describe("isPackReady", () => {
    it("returns true for ready status", () => {
      expect(isPackReady("ready")).toBe(true);
    });

    it("returns false for non-ready statuses", () => {
      expect(isPackReady("generating")).toBe(false);
      expect(isPackReady("outdated")).toBe(false);
      expect(isPackReady("none")).toBe(false);
    });
  });

  describe("isPackActionable", () => {
    it("returns true for all statuses except generating", () => {
      expect(isPackActionable("ready")).toBe(true);
      expect(isPackActionable("outdated")).toBe(true);
      expect(isPackActionable("none")).toBe(true);
    });

    it("returns false for generating", () => {
      expect(isPackActionable("generating")).toBe(false);
    });
  });

  describe("getDocumentContentCount", () => {
    it("counts only document type contents", () => {
      const contents: AuditPackContent[] = [
        { name: "00-INDEX.pdf", type: "index" },
        { name: "01-bol.pdf", type: "document", document_type: "bill_of_lading" },
        { name: "02-coo.pdf", type: "document", document_type: "certificate_of_origin" },
        { name: "tracking.json", type: "tracking" },
        { name: "metadata.json", type: "metadata" },
      ];
      expect(getDocumentContentCount(contents)).toBe(2);
    });

    it("returns 0 for empty contents", () => {
      expect(getDocumentContentCount([])).toBe(0);
    });
  });

  describe("formatGeneratedAt", () => {
    it("returns Never for null", () => {
      expect(formatGeneratedAt(null)).toBe("Never");
    });

    it("formats a valid ISO date", () => {
      const result = formatGeneratedAt("2026-02-16T10:30:00Z");
      expect(result).toBeTruthy();
      expect(typeof result).toBe("string");
      expect(result).not.toBe("Never");
    });
  });

  describe("constants", () => {
    it("PACK_STATUS_LABELS covers all statuses", () => {
      const statuses: AuditPackStatus[] = ["ready", "generating", "outdated", "none"];
      for (const s of statuses) {
        expect(PACK_STATUS_LABELS[s]).toBeTruthy();
      }
    });

    it("PACK_STATUS_COLORS covers all statuses", () => {
      const statuses: AuditPackStatus[] = ["ready", "generating", "outdated", "none"];
      for (const s of statuses) {
        expect(PACK_STATUS_COLORS[s]).toBeTruthy();
      }
    });

    it("CONTENT_TYPE_ICONS covers main types", () => {
      expect(CONTENT_TYPE_ICONS["index"]).toBeTruthy();
      expect(CONTENT_TYPE_ICONS["document"]).toBeTruthy();
      expect(CONTENT_TYPE_ICONS["tracking"]).toBeTruthy();
      expect(CONTENT_TYPE_ICONS["metadata"]).toBeTruthy();
    });
  });
});
