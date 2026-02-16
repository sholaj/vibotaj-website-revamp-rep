import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TrackingStatsCard } from "../tracking-stats-card";
import type { TrackingStats } from "@/lib/api/analytics-types";

const mockStats: TrackingStats = {
  total_events: 150,
  events_by_type: {},
  delays_detected: 4,
  avg_delay_hours: 12.5,
  recent_events_24h: 8,
  api_calls_today: 20,
  containers_tracked: 6,
};

describe("TrackingStatsCard", () => {
  it("renders title", () => {
    render(<TrackingStatsCard stats={mockStats} />);
    expect(screen.getByText("Tracking Stats")).toBeInTheDocument();
  });

  it("renders events 24h", () => {
    render(<TrackingStatsCard stats={mockStats} />);
    expect(screen.getByText("Events (24h)")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("renders containers tracked", () => {
    render(<TrackingStatsCard stats={mockStats} />);
    expect(screen.getByText("Containers tracked")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
  });

  it("renders delays detected", () => {
    render(<TrackingStatsCard stats={mockStats} />);
    expect(screen.getByText("Delays detected")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("renders avg delay hours", () => {
    render(<TrackingStatsCard stats={mockStats} />);
    expect(screen.getByText("Avg delay")).toBeInTheDocument();
    expect(screen.getByText("12.5h")).toBeInTheDocument();
  });

  it("renders total events", () => {
    render(<TrackingStatsCard stats={mockStats} />);
    expect(screen.getByText("Total events")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
  });

  it("shows 'None' when avg delay is 0", () => {
    const noDelays = { ...mockStats, avg_delay_hours: 0 };
    render(<TrackingStatsCard stats={noDelays} />);
    expect(screen.getByText("None")).toBeInTheDocument();
  });
});
