import { describe, it, expect } from "vitest";
import { isEudrRequired, type ShipmentDetail } from "../shipment-types";

function makeShipment(
  overrides: Partial<ShipmentDetail> = {},
): ShipmentDetail {
  return {
    id: "s1",
    reference: "SH-001",
    container_number: null,
    status: "draft",
    product_type: null,
    vessel_name: null,
    voyage_number: null,
    pol_code: null,
    pol_name: null,
    pod_code: null,
    pod_name: null,
    eta: null,
    etd: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    organization_id: "org-1",
    bl_number: null,
    booking_ref: null,
    carrier_code: null,
    carrier_name: null,
    atd: null,
    ata: null,
    incoterms: null,
    exporter_name: null,
    exporter_address: null,
    importer_name: null,
    importer_address: null,
    products: [],
    eudr_compliant: null,
    eudr_statement_id: null,
    buyer_organization_id: null,
    notes: null,
    ...overrides,
  };
}

describe("isEudrRequired", () => {
  it("returns false for horn_hoof product type", () => {
    const shipment = makeShipment({
      product_type: "horn_hoof",
      products: [{ hs_code: "0506", description: "Horn", weight_kg: 100, packaging_type: null }],
    });
    expect(isEudrRequired(shipment)).toBe(false);
  });

  it("returns false for HS 0507 (hoof)", () => {
    const shipment = makeShipment({
      product_type: "horn_hoof",
      products: [{ hs_code: "0507", description: "Hoof", weight_kg: 50, packaging_type: null }],
    });
    expect(isEudrRequired(shipment)).toBe(false);
  });

  it("returns true for cocoa beans (HS 1801)", () => {
    const shipment = makeShipment({
      product_type: "cocoa",
      products: [{ hs_code: "1801.00", description: "Cocoa Beans", weight_kg: 1000, packaging_type: "bags" }],
    });
    expect(isEudrRequired(shipment)).toBe(true);
  });

  it("returns true for coffee (HS 0901)", () => {
    const shipment = makeShipment({
      products: [{ hs_code: "0901.21", description: "Coffee", weight_kg: 500, packaging_type: null }],
    });
    expect(isEudrRequired(shipment)).toBe(true);
  });

  it("returns true for palm oil (HS 1511)", () => {
    const shipment = makeShipment({
      products: [{ hs_code: "1511.10", description: "Palm Oil", weight_kg: 2000, packaging_type: null }],
    });
    expect(isEudrRequired(shipment)).toBe(true);
  });

  it("returns false for empty products", () => {
    const shipment = makeShipment({ products: [] });
    expect(isEudrRequired(shipment)).toBe(false);
  });

  it("returns false for non-EUDR HS codes", () => {
    const shipment = makeShipment({
      products: [{ hs_code: "0714.20", description: "Sweet Potato", weight_kg: 300, packaging_type: null }],
    });
    expect(isEudrRequired(shipment)).toBe(false);
  });

  it("returns true if any product is EUDR-applicable", () => {
    const shipment = makeShipment({
      products: [
        { hs_code: "0714.20", description: "Sweet Potato", weight_kg: 300, packaging_type: null },
        { hs_code: "1801.00", description: "Cocoa Beans", weight_kg: 1000, packaging_type: null },
      ],
    });
    expect(isEudrRequired(shipment)).toBe(true);
  });
});
