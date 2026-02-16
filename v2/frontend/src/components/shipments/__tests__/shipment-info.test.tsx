import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ShipmentInfo } from "../shipment-info";
import type { ShipmentDetail } from "@/lib/api/shipment-types";

const mockShipment: ShipmentDetail = {
  id: "s1",
  reference: "SH-001",
  container_number: "ABCU1234567",
  status: "in_transit",
  product_type: "horn_hoof",
  vessel_name: "MV Atlantic",
  voyage_number: "V042",
  pol_code: "NGAPP",
  pol_name: "Apapa",
  pod_code: "DEHAM",
  pod_name: "Hamburg",
  eta: "2026-03-01T00:00:00Z",
  etd: "2026-02-10T00:00:00Z",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  organization_id: "org-1",
  bl_number: "BL-2026-001",
  booking_ref: "BK-001",
  carrier_code: "MSC",
  carrier_name: "Mediterranean Shipping",
  atd: null,
  ata: null,
  incoterms: "CIF",
  exporter_name: "VIBOTAJ Global",
  exporter_address: "Lagos, Nigeria",
  importer_name: "HAGES GmbH",
  importer_address: "Hamburg, Germany",
  products: [
    {
      hs_code: "0506.10",
      description: "Ossein",
      weight_kg: 22000,
      packaging_type: "bags",
    },
  ],
  eudr_compliant: null,
  eudr_statement_id: null,
  buyer_organization_id: null,
  notes: null,
};

describe("ShipmentInfo", () => {
  it("renders vessel and voyage", () => {
    render(<ShipmentInfo shipment={mockShipment} />);
    expect(screen.getByText(/MV Atlantic/)).toBeInTheDocument();
    expect(screen.getByText(/V042/)).toBeInTheDocument();
  });

  it("renders B/L number", () => {
    render(<ShipmentInfo shipment={mockShipment} />);
    expect(screen.getByText("BL-2026-001")).toBeInTheDocument();
  });

  it("renders route", () => {
    render(<ShipmentInfo shipment={mockShipment} />);
    expect(screen.getByText("Route")).toBeInTheDocument();
    // Route text is split across span children with an arrow icon
    const routeLabel = screen.getByText("Route");
    const routeSection = routeLabel.closest(".flex.items-start");
    expect(routeSection?.textContent).toContain("Apapa");
    expect(routeSection?.textContent).toContain("Hamburg");
  });

  it("renders exporter and importer", () => {
    render(<ShipmentInfo shipment={mockShipment} />);
    expect(screen.getByText("VIBOTAJ Global")).toBeInTheDocument();
    expect(screen.getByText("HAGES GmbH")).toBeInTheDocument();
  });

  it("renders cargo with HS code and weight", () => {
    render(<ShipmentInfo shipment={mockShipment} />);
    expect(screen.getByText("0506.10")).toBeInTheDocument();
    expect(screen.getByText("Ossein")).toBeInTheDocument();
    expect(screen.getByText("(22000 kg)")).toBeInTheDocument();
  });

  it("renders incoterms", () => {
    render(<ShipmentInfo shipment={mockShipment} />);
    expect(screen.getByText("CIF")).toBeInTheDocument();
  });

  it("renders carrier", () => {
    render(<ShipmentInfo shipment={mockShipment} />);
    expect(screen.getByText("Mediterranean Shipping")).toBeInTheDocument();
  });
});
