import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TrendsChart } from "../trends-chart";
import type { ShipmentTrendPoint } from "@/lib/api/analytics-types";

// Mock recharts to avoid canvas issues in jsdom
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

const mockData: ShipmentTrendPoint[] = [
  { date: "2026-02-10", count: 3 },
  { date: "2026-02-11", count: 5 },
  { date: "2026-02-12", count: 2 },
];

describe("TrendsChart", () => {
  it("renders chart title", () => {
    render(
      <TrendsChart data={mockData} groupBy="day" onGroupByChange={vi.fn()} />,
    );
    expect(screen.getByText("Shipments Over Time")).toBeInTheDocument();
  });

  it("renders time window buttons", () => {
    render(
      <TrendsChart data={mockData} groupBy="day" onGroupByChange={vi.fn()} />,
    );
    expect(screen.getByText("Day")).toBeInTheDocument();
    expect(screen.getByText("Week")).toBeInTheDocument();
    expect(screen.getByText("Month")).toBeInTheDocument();
  });

  it("calls onGroupByChange when button clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <TrendsChart data={mockData} groupBy="day" onGroupByChange={onChange} />,
    );
    await user.click(screen.getByText("Week"));
    expect(onChange).toHaveBeenCalledWith("week");
  });

  it("renders chart when data present", () => {
    render(
      <TrendsChart data={mockData} groupBy="day" onGroupByChange={vi.fn()} />,
    );
    expect(screen.getByTestId("line-chart")).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    render(
      <TrendsChart data={[]} groupBy="day" onGroupByChange={vi.fn()} />,
    );
    expect(
      screen.getByText("No shipment data available for the selected period"),
    ).toBeInTheDocument();
  });
});
