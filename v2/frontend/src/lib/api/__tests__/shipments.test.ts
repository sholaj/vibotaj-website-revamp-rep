import { describe, expect, it } from "vitest";
import { computeStats, formatMonth, type Shipment } from "../shipment-types";

function makeShipment(
  overrides: Partial<Shipment> & { status: Shipment["status"] },
): Shipment {
  return {
    id: crypto.randomUUID(),
    reference: `SHP-${Math.random().toString(36).slice(2, 6).toUpperCase()}`,
    container_number: null,
    product_type: null,
    vessel_name: null,
    voyage_number: null,
    pol_code: "NGAPP",
    pol_name: "Apapa",
    pod_code: "DEHAM",
    pod_name: "Hamburg",
    eta: null,
    etd: null,
    created_at: "2026-02-01T00:00:00Z",
    updated_at: "2026-02-01T00:00:00Z",
    organization_id: "org-1",
    ...overrides,
  };
}

describe("computeStats", () => {
  it("computes totalShipments correctly", () => {
    const shipments = [
      makeShipment({ status: "draft" }),
      makeShipment({ status: "in_transit" }),
      makeShipment({ status: "delivered" }),
    ];
    const stats = computeStats(shipments);
    expect(stats.totalShipments).toBe(3);
  });

  it("counts docs_pending correctly", () => {
    const shipments = [
      makeShipment({ status: "docs_pending" }),
      makeShipment({ status: "docs_pending" }),
      makeShipment({ status: "draft" }),
    ];
    const stats = computeStats(shipments);
    expect(stats.docsPending).toBe(2);
  });

  it("counts in_transit correctly", () => {
    const shipments = [
      makeShipment({ status: "in_transit" }),
      makeShipment({ status: "draft" }),
    ];
    const stats = computeStats(shipments);
    expect(stats.inTransit).toBe(1);
  });

  it("computes compliance rate as percentage of compliant shipments", () => {
    const shipments = [
      makeShipment({ status: "docs_complete" }),
      makeShipment({ status: "delivered" }),
      makeShipment({ status: "arrived" }),
      makeShipment({ status: "draft" }),
    ];
    const stats = computeStats(shipments);
    // 3 out of 4 are compliant = 75%
    expect(stats.complianceRate).toBe(75);
  });

  it("returns 0 compliance rate for empty list", () => {
    const stats = computeStats([]);
    expect(stats.complianceRate).toBe(0);
  });

  it("computes status breakdown sorted by count descending", () => {
    const shipments = [
      makeShipment({ status: "draft" }),
      makeShipment({ status: "draft" }),
      makeShipment({ status: "draft" }),
      makeShipment({ status: "in_transit" }),
      makeShipment({ status: "delivered" }),
    ];
    const stats = computeStats(shipments);
    expect(stats.statusBreakdown[0]).toEqual({ status: "draft", count: 3 });
  });

  it("returns last 5 recent shipments sorted by date desc", () => {
    const shipments = Array.from({ length: 10 }, (_, i) =>
      makeShipment({
        status: "draft",
        reference: `SHP-${String(i).padStart(3, "0")}`,
        created_at: `2026-01-${String(i + 1).padStart(2, "0")}T00:00:00Z`,
      }),
    );
    const stats = computeStats(shipments);
    expect(stats.recentShipments).toHaveLength(5);
    expect(stats.recentShipments[0]!.reference).toBe("SHP-009"); // most recent
  });

  it("computes monthly volume for last 6 months", () => {
    const stats = computeStats([]);
    expect(stats.monthlyVolume).toHaveLength(6);
  });

  it("computes compliance trend for last 6 months", () => {
    const stats = computeStats([]);
    expect(stats.complianceTrend).toHaveLength(6);
  });
});

describe("formatMonth", () => {
  it("formats YYYY-MM to short month name + year", () => {
    expect(formatMonth("2026-01")).toBe("Jan 2026");
    expect(formatMonth("2026-06")).toBe("Jun 2026");
    expect(formatMonth("2026-12")).toBe("Dec 2026");
  });
});
