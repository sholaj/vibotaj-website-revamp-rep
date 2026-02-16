import { describe, it, expect } from "vitest";
import {
  formatTrendDate,
  formatActivityTime,
  getActionLabel,
  hasAlerts,
  DOC_STATUS_LABELS,
  ACTION_LABELS,
  type AnalyticsDashboard,
} from "../analytics-types";

describe("formatTrendDate", () => {
  it("formats day grouping as 'd MMM'", () => {
    expect(formatTrendDate("2026-02-15", "day")).toBe("15 Feb");
  });

  it("formats week grouping as 'd MMM'", () => {
    expect(formatTrendDate("2026-02-10", "week")).toBe("10 Feb");
  });

  it("formats month grouping as 'MMM yyyy'", () => {
    expect(formatTrendDate("2026-02-01", "month")).toBe("Feb 2026");
  });
});

describe("formatActivityTime", () => {
  it("formats timestamp as 'd MMM, HH:mm'", () => {
    const result = formatActivityTime("2026-02-16T14:30:00Z");
    expect(result).toContain("16 Feb");
  });
});

describe("getActionLabel", () => {
  it("returns label for known action", () => {
    expect(getActionLabel("document.upload")).toBe("Uploaded document");
  });

  it("returns label for auth login", () => {
    expect(getActionLabel("auth.login.success")).toBe("Logged in");
  });

  it("returns last segment for unknown action", () => {
    expect(getActionLabel("custom.unknown.action")).toBe("action");
  });
});

describe("hasAlerts", () => {
  const baseDashboard: AnalyticsDashboard = {
    shipments: { total: 10, in_transit: 3, delivered_this_month: 2, with_delays: 0 },
    documents: { total: 50, pending_validation: 5, completion_rate: 80, expiring_soon: 0 },
    compliance: { rate: 85, eudr_coverage: 70, needing_attention: 0 },
    tracking: { events_today: 5, delays_detected: 0, containers_tracked: 3 },
    generated_at: "2026-02-16T12:00:00Z",
  };

  it("returns false when no alerts", () => {
    expect(hasAlerts(baseDashboard)).toBe(false);
  });

  it("returns true when documents expiring soon", () => {
    const d = { ...baseDashboard, documents: { ...baseDashboard.documents, expiring_soon: 3 } };
    expect(hasAlerts(d)).toBe(true);
  });

  it("returns true when shipments delayed", () => {
    const d = { ...baseDashboard, shipments: { ...baseDashboard.shipments, with_delays: 2 } };
    expect(hasAlerts(d)).toBe(true);
  });
});

describe("DOC_STATUS_LABELS", () => {
  it("has labels for all 7 statuses", () => {
    expect(Object.keys(DOC_STATUS_LABELS)).toHaveLength(7);
  });

  it("maps compliance_ok to Compliant", () => {
    expect(DOC_STATUS_LABELS["compliance_ok"]).toBe("Compliant");
  });
});

describe("ACTION_LABELS", () => {
  it("has 8 action labels", () => {
    expect(Object.keys(ACTION_LABELS)).toHaveLength(8);
  });
});
