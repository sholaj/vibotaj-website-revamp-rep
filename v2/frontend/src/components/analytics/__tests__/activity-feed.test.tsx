import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ActivityFeed } from "../activity-feed";
import type { ActivityItem } from "@/lib/api/analytics-types";

const mockActivities: ActivityItem[] = [
  {
    id: "a1",
    action: "document.upload",
    username: "Shola",
    resource_type: "document",
    resource_id: "d1",
    timestamp: "2026-02-16T14:30:00Z",
    details: {},
  },
  {
    id: "a2",
    action: "tracking.refresh",
    username: "Bolaji",
    resource_type: null,
    resource_id: null,
    timestamp: "2026-02-16T13:00:00Z",
    details: {},
  },
  {
    id: "a3",
    action: "auth.login.success",
    username: "Admin",
    resource_type: null,
    resource_id: null,
    timestamp: "2026-02-16T12:00:00Z",
    details: {},
  },
];

describe("ActivityFeed", () => {
  it("renders title", () => {
    render(<ActivityFeed activities={mockActivities} />);
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
  });

  it("renders all activity items", () => {
    render(<ActivityFeed activities={mockActivities} />);
    expect(screen.getByText("Shola")).toBeInTheDocument();
    expect(screen.getByText("Bolaji")).toBeInTheDocument();
    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("renders action labels", () => {
    render(<ActivityFeed activities={mockActivities} />);
    expect(screen.getByText("Uploaded document")).toBeInTheDocument();
    expect(screen.getByText("Refreshed tracking")).toBeInTheDocument();
    expect(screen.getByText("Logged in")).toBeInTheDocument();
  });

  it("renders resource type when present", () => {
    render(<ActivityFeed activities={mockActivities} />);
    expect(screen.getByText("(document)")).toBeInTheDocument();
  });

  it("renders empty state when no activities", () => {
    render(<ActivityFeed activities={[]} />);
    expect(screen.getByText("No recent activity")).toBeInTheDocument();
  });

  it("renders timestamp for each item", () => {
    render(<ActivityFeed activities={mockActivities} />);
    // Should contain date text
    const timeElements = screen.getAllByText(/Feb/);
    expect(timeElements.length).toBeGreaterThanOrEqual(3);
  });
});
