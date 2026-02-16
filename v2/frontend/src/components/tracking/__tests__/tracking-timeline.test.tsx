import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TrackingTimeline } from "../tracking-timeline";
import type { ContainerEvent } from "@/lib/api/tracking-types";

const mockEvents: ContainerEvent[] = [
  {
    id: "e1",
    event_type: "gate_in",
    timestamp: "2026-02-10T08:00:00Z",
    location_name: "Apapa Terminal",
    location_code: "NGAPP",
    vessel_name: null,
    voyage_number: null,
    description: null,
  },
  {
    id: "e2",
    event_type: "loaded",
    timestamp: "2026-02-11T14:00:00Z",
    location_name: "Apapa Terminal",
    location_code: "NGAPP",
    vessel_name: "MV Atlantic",
    voyage_number: "V042",
    description: null,
  },
  {
    id: "e3",
    event_type: "departed",
    timestamp: "2026-02-12T06:00:00Z",
    location_name: "Apapa",
    location_code: "NGAPP",
    vessel_name: "MV Atlantic",
    voyage_number: "V042",
    description: "Vessel departed port",
  },
];

describe("TrackingTimeline", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-02-16T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders event count in header", () => {
    render(<TrackingTimeline events={mockEvents} />);
    expect(screen.getByText("Tracking (3 events)")).toBeInTheDocument();
  });

  it("renders event type labels", () => {
    render(<TrackingTimeline events={mockEvents} />);
    expect(screen.getByText("Gate In")).toBeInTheDocument();
    expect(screen.getByText("Loaded on Vessel")).toBeInTheDocument();
    expect(screen.getByText("Departed")).toBeInTheDocument();
  });

  it("renders 'Latest' badge on most recent event", () => {
    render(<TrackingTimeline events={mockEvents} />);
    expect(screen.getByText("Latest")).toBeInTheDocument();
  });

  it("renders location names", () => {
    render(<TrackingTimeline events={mockEvents} />);
    const apapa = screen.getAllByText("Apapa Terminal");
    expect(apapa.length).toBeGreaterThanOrEqual(1);
  });

  it("renders vessel info when present", () => {
    render(<TrackingTimeline events={mockEvents} />);
    const vessels = screen.getAllByText(/MV Atlantic/);
    expect(vessels.length).toBeGreaterThanOrEqual(1);
  });

  it("renders empty state when no events", () => {
    render(<TrackingTimeline events={[]} />);
    expect(screen.getByText("No tracking events")).toBeInTheDocument();
  });

  it("sorts events most recent first", () => {
    render(<TrackingTimeline events={mockEvents} />);
    const labels = screen.getAllByText(/Gate In|Loaded on Vessel|Departed/);
    // Departed is most recent, should appear first
    expect(labels[0]!.textContent).toBe("Departed");
  });
});
