import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DocumentDistributionChart } from "../document-distribution-chart";
import type { DocumentDistributionItem } from "@/lib/api/analytics-types";

// Mock recharts
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie">{children}</div>
  ),
  Cell: () => <div data-testid="cell" />,
  Tooltip: () => null,
  Legend: () => null,
}));

const mockData: DocumentDistributionItem[] = [
  { status: "uploaded", count: 10 },
  { status: "validated", count: 8 },
  { status: "compliance_ok", count: 5 },
  { status: "compliance_failed", count: 2 },
  { status: "draft", count: 0 },
];

describe("DocumentDistributionChart", () => {
  it("renders chart title", () => {
    render(<DocumentDistributionChart data={mockData} />);
    expect(screen.getByText("Document Status Distribution")).toBeInTheDocument();
  });

  it("renders pie chart when data present", () => {
    render(<DocumentDistributionChart data={mockData} />);
    expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
  });

  it("filters out zero-count statuses", () => {
    render(<DocumentDistributionChart data={mockData} />);
    // 4 cells (draft has count 0, filtered out)
    const cells = screen.getAllByTestId("cell");
    expect(cells).toHaveLength(4);
  });

  it("renders empty state when all counts are zero", () => {
    const emptyData = [
      { status: "draft", count: 0 },
      { status: "uploaded", count: 0 },
    ];
    render(<DocumentDistributionChart data={emptyData} />);
    expect(screen.getByText("No document data available")).toBeInTheDocument();
  });

  it("renders empty state when data is empty", () => {
    render(<DocumentDistributionChart data={[]} />);
    expect(screen.getByText("No document data available")).toBeInTheDocument();
  });
});
