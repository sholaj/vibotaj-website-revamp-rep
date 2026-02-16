import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { KpiCards } from "../kpi-cards";
import type { DashboardStats } from "@/lib/api/shipment-types";

const mockStats: DashboardStats = {
  totalShipments: 42,
  docsPending: 7,
  inTransit: 12,
  complianceRate: 85,
  statusBreakdown: [],
  monthlyVolume: [],
  complianceTrend: [],
  recentShipments: [],
};

describe("KpiCards", () => {
  it("renders total shipments", () => {
    render(<KpiCards stats={mockStats} />);
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("Total Shipments")).toBeInTheDocument();
  });

  it("renders docs pending count", () => {
    render(<KpiCards stats={mockStats} />);
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("Docs Pending")).toBeInTheDocument();
  });

  it("renders in transit count", () => {
    render(<KpiCards stats={mockStats} />);
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("In Transit")).toBeInTheDocument();
  });

  it("renders compliance rate with percent", () => {
    render(<KpiCards stats={mockStats} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("Compliance Rate")).toBeInTheDocument();
  });

  it("renders all four KPI cards", () => {
    const { container } = render(<KpiCards stats={mockStats} />);
    const cards = container.querySelectorAll("[data-slot='card']");
    expect(cards).toHaveLength(4);
  });
});
