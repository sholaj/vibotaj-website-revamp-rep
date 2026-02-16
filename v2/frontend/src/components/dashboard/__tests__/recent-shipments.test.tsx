import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RecentShipments } from "../recent-shipments";
import type { Shipment } from "@/lib/api/shipment-types";

const mockShipments: Shipment[] = [
  {
    id: "s1",
    reference: "SH-001",
    container_number: "ABCU1234567",
    status: "in_transit",
    product_type: "horn",
    vessel_name: "MV Test",
    voyage_number: "V001",
    pol_code: "NGAPP",
    pol_name: "Apapa",
    pod_code: "BEANR",
    pod_name: "Antwerp",
    eta: "2026-03-01T00:00:00Z",
    etd: "2026-02-10T00:00:00Z",
    created_at: "2026-02-01T00:00:00Z",
    updated_at: "2026-02-01T00:00:00Z",
    organization_id: "org-1",
  },
  {
    id: "s2",
    reference: "SH-002",
    container_number: null,
    status: "docs_pending",
    product_type: null,
    vessel_name: null,
    voyage_number: null,
    pol_code: null,
    pol_name: null,
    pod_code: "DEHAM",
    pod_name: "Hamburg",
    eta: null,
    etd: null,
    created_at: "2026-01-15T00:00:00Z",
    updated_at: "2026-01-15T00:00:00Z",
    organization_id: "org-1",
  },
];

describe("RecentShipments", () => {
  it("renders shipment references as links", () => {
    render(<RecentShipments shipments={mockShipments} />);
    const link = screen.getByText("SH-001");
    expect(link).toBeInTheDocument();
    expect(link.closest("a")).toHaveAttribute("href", "/shipments/s1");
  });

  it("renders destination from pod_name", () => {
    render(<RecentShipments shipments={mockShipments} />);
    expect(screen.getByText("Antwerp")).toBeInTheDocument();
    expect(screen.getByText("Hamburg")).toBeInTheDocument();
  });

  it("renders ETA formatted", () => {
    render(<RecentShipments shipments={mockShipments} />);
    expect(screen.getByText("1 Mar 2026")).toBeInTheDocument();
  });

  it("renders dash for missing ETA", () => {
    render(<RecentShipments shipments={mockShipments} />);
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it("renders empty state when no shipments", () => {
    render(<RecentShipments shipments={[]} />);
    expect(screen.getByText("No shipments yet")).toBeInTheDocument();
  });

  it("renders View all link", () => {
    render(<RecentShipments shipments={mockShipments} />);
    const viewAll = screen.getByText("View all");
    expect(viewAll.closest("a")).toHaveAttribute("href", "/shipments");
  });
});
