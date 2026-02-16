import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LiveStatusCard } from "../live-status-card";
import type { ContainerEvent } from "@/lib/api/tracking-types";

const mockEvent: ContainerEvent = {
  id: "e1",
  event_type: "departed",
  timestamp: "2026-02-12T06:00:00Z",
  location_name: "Apapa",
  location_code: "NGAPP",
  vessel_name: "MV Atlantic",
  voyage_number: "V042",
  description: null,
};

describe("LiveStatusCard", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-02-16T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders latest event status", () => {
    render(
      <LiveStatusCard
        latestEvent={mockEvent}
        containerNumber="ABCU1234567"
        eta="2026-03-01T00:00:00Z"
      />,
    );
    expect(screen.getByText("Departed")).toBeInTheDocument();
  });

  it("renders vessel name", () => {
    render(
      <LiveStatusCard
        latestEvent={mockEvent}
        containerNumber="ABCU1234567"
        eta={null}
      />,
    );
    expect(screen.getByText("MV Atlantic")).toBeInTheDocument();
  });

  it("renders location", () => {
    render(
      <LiveStatusCard
        latestEvent={mockEvent}
        containerNumber="ABCU1234567"
        eta={null}
      />,
    );
    expect(screen.getByText(/Apapa/)).toBeInTheDocument();
  });

  it("renders ETA when provided", () => {
    render(
      <LiveStatusCard
        latestEvent={mockEvent}
        containerNumber="ABCU1234567"
        eta="2026-03-01T00:00:00Z"
      />,
    );
    expect(screen.getByText("1 Mar 2026")).toBeInTheDocument();
  });

  it("renders relative time for last updated", () => {
    render(
      <LiveStatusCard
        latestEvent={mockEvent}
        containerNumber="ABCU1234567"
        eta={null}
      />,
    );
    expect(screen.getByText("4d ago")).toBeInTheDocument();
  });

  it("renders empty state when no events", () => {
    render(
      <LiveStatusCard
        latestEvent={null}
        containerNumber="ABCU1234567"
        eta={null}
      />,
    );
    expect(screen.getByText("No tracking data yet")).toBeInTheDocument();
  });

  it("renders empty state for missing container", () => {
    render(
      <LiveStatusCard
        latestEvent={null}
        containerNumber={null}
        eta={null}
      />,
    );
    expect(screen.getByText("No container number assigned")).toBeInTheDocument();
  });

  it("renders error state", () => {
    render(
      <LiveStatusCard
        latestEvent={null}
        containerNumber="ABCU1234567"
        eta={null}
        error="Carrier API unavailable"
      />,
    );
    expect(screen.getByText("Tracking unavailable")).toBeInTheDocument();
    expect(screen.getByText("Carrier API unavailable")).toBeInTheDocument();
  });

  it("renders sync button and calls handler", async () => {
    vi.useRealTimers(); // need real timers for userEvent
    const user = userEvent.setup();
    const onSync = vi.fn();
    render(
      <LiveStatusCard
        latestEvent={null}
        containerNumber="ABCU1234567"
        eta={null}
        onSyncTracking={onSync}
      />,
    );
    await user.click(screen.getByText("Sync Live Tracking"));
    expect(onSync).toHaveBeenCalled();
  });

  it("disables sync button when no container number", () => {
    render(
      <LiveStatusCard
        latestEvent={null}
        containerNumber={null}
        eta={null}
        onSyncTracking={vi.fn()}
      />,
    );
    expect(screen.getByText("Sync Live Tracking")).toBeDisabled();
  });
});
