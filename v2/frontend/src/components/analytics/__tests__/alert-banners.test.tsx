import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AlertBanners } from "../alert-banners";
import type { AnalyticsDashboard } from "@/lib/api/analytics-types";

function makeDashboard(
  overrides: Partial<{
    expiring_soon: number;
    with_delays: number;
    needing_attention: number;
  }> = {},
): AnalyticsDashboard {
  return {
    shipments: { total: 10, in_transit: 3, delivered_this_month: 2, with_delays: overrides.with_delays ?? 0 },
    documents: { total: 50, pending_validation: 5, completion_rate: 80, expiring_soon: overrides.expiring_soon ?? 0 },
    compliance: { rate: 85, eudr_coverage: 70, needing_attention: overrides.needing_attention ?? 0 },
    tracking: { events_today: 5, delays_detected: 0, containers_tracked: 3 },
    generated_at: "2026-02-16T12:00:00Z",
  };
}

describe("AlertBanners", () => {
  it("renders expiring documents warning", () => {
    render(<AlertBanners dashboard={makeDashboard({ expiring_soon: 3 })} />);
    expect(screen.getByText("3 document(s) expiring soon")).toBeInTheDocument();
    expect(screen.getByText("Within the next 30 days")).toBeInTheDocument();
  });

  it("renders delayed shipments warning", () => {
    render(<AlertBanners dashboard={makeDashboard({ with_delays: 2 })} />);
    expect(screen.getByText("2 shipment(s) delayed")).toBeInTheDocument();
  });

  it("renders all-compliant banner when needing_attention is 0", () => {
    render(<AlertBanners dashboard={makeDashboard({ needing_attention: 0 })} />);
    expect(screen.getByText("All shipments compliant")).toBeInTheDocument();
  });

  it("hides all-compliant banner when needing_attention > 0", () => {
    render(<AlertBanners dashboard={makeDashboard({ needing_attention: 5 })} />);
    expect(screen.queryByText("All shipments compliant")).not.toBeInTheDocument();
  });

  it("renders nothing when no alerts and not compliant", () => {
    const dashboard = makeDashboard({ needing_attention: 1 });
    const { container } = render(<AlertBanners dashboard={dashboard} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders multiple alerts simultaneously", () => {
    render(
      <AlertBanners
        dashboard={makeDashboard({ expiring_soon: 1, with_delays: 1, needing_attention: 0 })}
      />,
    );
    expect(screen.getByText("1 document(s) expiring soon")).toBeInTheDocument();
    expect(screen.getByText("1 shipment(s) delayed")).toBeInTheDocument();
    expect(screen.getByText("All shipments compliant")).toBeInTheDocument();
  });
});
