// --- Analytics types (no React/PropelAuth dependencies) ---

// Response from GET /api/analytics/dashboard
export interface AnalyticsDashboard {
  shipments: {
    total: number;
    in_transit: number;
    delivered_this_month: number;
    with_delays: number;
  };
  documents: {
    total: number;
    pending_validation: number;
    completion_rate: number;
    expiring_soon: number;
  };
  compliance: {
    rate: number;
    eudr_coverage: number;
    needing_attention: number;
  };
  tracking: {
    events_today: number;
    delays_detected: number;
    containers_tracked: number;
  };
  generated_at: string;
}

// Response from GET /api/analytics/shipments
export interface ShipmentStats {
  total: number;
  by_status: Record<string, number>;
  avg_transit_days: number | null;
  recent_shipments: number;
  in_transit_count: number;
  completed_this_month: number;
  delayed_count: number;
}

// Response from GET /api/analytics/shipments/trends
export interface ShipmentTrendPoint {
  date: string;
  count: number;
}

export interface ShipmentTrendsResponse {
  period_days: number;
  group_by: "day" | "week" | "month";
  data: ShipmentTrendPoint[];
}

export type TrendGroupBy = "day" | "week" | "month";

// Response from GET /api/analytics/documents
export interface DocumentStats {
  total: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  completion_rate: number;
  pending_validation: number;
  expiring_soon: number;
  recently_uploaded: number;
}

// Response from GET /api/analytics/documents/distribution
export interface DocumentDistributionItem {
  status: string;
  count: number;
}

export interface DocumentDistributionResponse {
  data: DocumentDistributionItem[];
}

// Response from GET /api/analytics/compliance
export interface ComplianceMetrics {
  compliant_rate: number;
  eudr_coverage: number;
  shipments_needing_attention: number;
  failed_documents: number;
  issues_summary: Record<string, number>;
}

// Response from GET /api/analytics/tracking
export interface TrackingStats {
  total_events: number;
  events_by_type: Record<string, number>;
  delays_detected: number;
  avg_delay_hours: number;
  recent_events_24h: number;
  api_calls_today: number;
  containers_tracked: number;
}

// Activity feed (from audit log)
export interface ActivityItem {
  id: string;
  action: string;
  username: string;
  resource_type: string | null;
  resource_id: string | null;
  timestamp: string;
  details: Record<string, unknown>;
}

export interface RecentActivityResponse {
  activities: ActivityItem[];
}

// --- Constants ---

export const DOC_STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  uploaded: "Uploaded",
  validated: "Validated",
  compliance_ok: "Compliant",
  compliance_failed: "Failed",
  linked: "Linked",
  archived: "Archived",
};

export const DOC_STATUS_COLORS: Record<string, string> = {
  draft: "hsl(var(--muted-foreground))",
  uploaded: "hsl(var(--info))",
  validated: "hsl(var(--success))",
  compliance_ok: "hsl(142 76% 36%)",
  compliance_failed: "hsl(var(--destructive))",
  linked: "hsl(262 83% 58%)",
  archived: "hsl(var(--muted-foreground))",
};

export const ACTION_LABELS: Record<string, string> = {
  "auth.login.success": "Logged in",
  "shipment.view": "Viewed shipment",
  "document.upload": "Uploaded document",
  "document.download": "Downloaded document",
  "document.validate": "Validated document",
  "document.transition": "Updated document status",
  "tracking.refresh": "Refreshed tracking",
  "auditpack.download": "Downloaded audit pack",
};

// --- Helpers ---

export function formatTrendDate(iso: string, groupBy: TrendGroupBy): string {
  const d = new Date(iso);
  if (groupBy === "month") {
    return d.toLocaleDateString("en-GB", { month: "short", year: "numeric" });
  }
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export function formatActivityTime(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getActionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action.split(".").pop() ?? action;
}

export function hasAlerts(dashboard: AnalyticsDashboard): boolean {
  return (
    dashboard.documents.expiring_soon > 0 ||
    dashboard.shipments.with_delays > 0
  );
}
