import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ShipmentHeader } from "../shipment-header";
import type { ShipmentDetail } from "@/lib/api/shipment-types";

const mockShipment: ShipmentDetail = {
  id: "s1",
  reference: "SH-001",
  container_number: "ABCU1234567",
  status: "in_transit",
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
};

describe("ShipmentHeader", () => {
  it("renders reference and container number", () => {
    render(<ShipmentHeader shipment={mockShipment} />);
    expect(screen.getByText("SH-001")).toBeInTheDocument();
    expect(screen.getByText("ABCU1234567")).toBeInTheDocument();
  });

  it("renders status badge", () => {
    render(<ShipmentHeader shipment={mockShipment} />);
    expect(screen.getByText("In Transit")).toBeInTheDocument();
  });

  it("renders back link to shipments", () => {
    render(<ShipmentHeader shipment={mockShipment} />);
    const backLink = screen.getByRole("link");
    expect(backLink).toHaveAttribute("href", "/shipments");
  });

  it("renders audit pack button when handler provided", () => {
    const onDownload = vi.fn();
    render(
      <ShipmentHeader
        shipment={mockShipment}
        onDownloadAuditPack={onDownload}
      />,
    );
    expect(screen.getByText("Audit Pack")).toBeInTheDocument();
  });

  it("calls onDownloadAuditPack when clicked", async () => {
    const user = userEvent.setup();
    const onDownload = vi.fn();
    render(
      <ShipmentHeader
        shipment={mockShipment}
        onDownloadAuditPack={onDownload}
      />,
    );
    await user.click(screen.getByText("Audit Pack"));
    expect(onDownload).toHaveBeenCalled();
  });

  it("hides container number when null", () => {
    render(
      <ShipmentHeader
        shipment={{ ...mockShipment, container_number: null }}
      />,
    );
    expect(screen.queryByText("ABCU1234567")).not.toBeInTheDocument();
  });
});
