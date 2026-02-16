import { describe, it, expect } from "vitest";
import {
  ALL_EVENT_TYPES,
  EVENT_TYPE_LABELS,
  EVENT_CATEGORIES,
  CATEGORY_LABELS,
  groupByCategory,
  getDefaultPreferences,
  type NotificationEventType,
  type NotificationCategory,
} from "../notification-types";

describe("notification-types", () => {
  describe("ALL_EVENT_TYPES", () => {
    it("has 8 event types", () => {
      expect(ALL_EVENT_TYPES).toHaveLength(8);
    });

    it("includes document events", () => {
      expect(ALL_EVENT_TYPES).toContain("document_uploaded");
      expect(ALL_EVENT_TYPES).toContain("document_validated");
      expect(ALL_EVENT_TYPES).toContain("document_rejected");
    });

    it("includes shipment events", () => {
      expect(ALL_EVENT_TYPES).toContain("shipment_status_change");
    });

    it("includes compliance events", () => {
      expect(ALL_EVENT_TYPES).toContain("compliance_alert");
      expect(ALL_EVENT_TYPES).toContain("expiry_warning");
    });

    it("includes team events", () => {
      expect(ALL_EVENT_TYPES).toContain("invitation_sent");
      expect(ALL_EVENT_TYPES).toContain("invitation_accepted");
    });
  });

  describe("EVENT_TYPE_LABELS", () => {
    it("has a label for every event type", () => {
      for (const et of ALL_EVENT_TYPES) {
        expect(EVENT_TYPE_LABELS[et]).toBeDefined();
        expect(typeof EVENT_TYPE_LABELS[et]).toBe("string");
      }
    });

    it("has human-readable labels", () => {
      expect(EVENT_TYPE_LABELS.document_uploaded).toBe("Document Uploaded");
      expect(EVENT_TYPE_LABELS.compliance_alert).toBe("Compliance Alert");
    });
  });

  describe("EVENT_CATEGORIES", () => {
    it("maps every event to a category", () => {
      for (const et of ALL_EVENT_TYPES) {
        expect(EVENT_CATEGORIES[et]).toBeDefined();
      }
    });

    it("groups document events correctly", () => {
      expect(EVENT_CATEGORIES.document_uploaded).toBe("documents");
      expect(EVENT_CATEGORIES.document_validated).toBe("documents");
      expect(EVENT_CATEGORIES.document_rejected).toBe("documents");
    });

    it("groups compliance events correctly", () => {
      expect(EVENT_CATEGORIES.compliance_alert).toBe("compliance");
      expect(EVENT_CATEGORIES.expiry_warning).toBe("compliance");
    });
  });

  describe("CATEGORY_LABELS", () => {
    it("has labels for all categories", () => {
      const categories: NotificationCategory[] = [
        "documents",
        "shipments",
        "compliance",
        "team",
      ];
      for (const c of categories) {
        expect(CATEGORY_LABELS[c]).toBeDefined();
      }
    });
  });

  describe("groupByCategory", () => {
    it("groups all events into categories", () => {
      const grouped = groupByCategory(ALL_EVENT_TYPES);
      expect(grouped.documents).toHaveLength(3);
      expect(grouped.shipments).toHaveLength(1);
      expect(grouped.compliance).toHaveLength(2);
      expect(grouped.team).toHaveLength(2);
    });

    it("total events in groups equals ALL_EVENT_TYPES length", () => {
      const grouped = groupByCategory(ALL_EVENT_TYPES);
      const total =
        grouped.documents.length +
        grouped.shipments.length +
        grouped.compliance.length +
        grouped.team.length;
      expect(total).toBe(ALL_EVENT_TYPES.length);
    });
  });

  describe("getDefaultPreferences", () => {
    it("returns preferences for all event types", () => {
      const defaults = getDefaultPreferences();
      expect(defaults).toHaveLength(ALL_EVENT_TYPES.length);
    });

    it("defaults all to enabled", () => {
      const defaults = getDefaultPreferences();
      for (const pref of defaults) {
        expect(pref.email_enabled).toBe(true);
        expect(pref.in_app_enabled).toBe(true);
      }
    });

    it("covers every event type", () => {
      const defaults = getDefaultPreferences();
      const types = defaults.map((p) => p.event_type);
      for (const et of ALL_EVENT_TYPES) {
        expect(types).toContain(et);
      }
    });
  });
});
