"use client";

import { useQuery } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type {
  AnalyticsDashboard,
  ShipmentTrendsResponse,
  DocumentDistributionResponse,
  ComplianceMetrics,
  TrackingStats,
  RecentActivityResponse,
  TrendGroupBy,
} from "./analytics-types";

// Re-export types
export type {
  AnalyticsDashboard,
  ShipmentStats,
  ShipmentTrendsResponse,
  ShipmentTrendPoint,
  TrendGroupBy,
  DocumentStats,
  DocumentDistributionResponse,
  DocumentDistributionItem,
  ComplianceMetrics,
  TrackingStats,
  ActivityItem,
  RecentActivityResponse,
} from "./analytics-types";

export {
  DOC_STATUS_LABELS,
  DOC_STATUS_COLORS,
  ACTION_LABELS,
  formatTrendDate,
  formatActivityTime,
  getActionLabel,
  hasAlerts,
} from "./analytics-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Organization-Id": orgId,
  };
}

// --- Fetch functions ---

async function fetchAnalyticsDashboard(orgId: string): Promise<AnalyticsDashboard> {
  const res = await fetch(`${API_BASE}/api/analytics/dashboard`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch analytics dashboard: ${res.status}`);
  return res.json() as Promise<AnalyticsDashboard>;
}

async function fetchShipmentTrends(
  orgId: string,
  days: number,
  groupBy: TrendGroupBy,
): Promise<ShipmentTrendsResponse> {
  const params = new URLSearchParams({ days: String(days), group_by: groupBy });
  const res = await fetch(`${API_BASE}/api/analytics/shipments/trends?${params}`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch shipment trends: ${res.status}`);
  return res.json() as Promise<ShipmentTrendsResponse>;
}

async function fetchDocumentDistribution(orgId: string): Promise<DocumentDistributionResponse> {
  const res = await fetch(`${API_BASE}/api/analytics/documents/distribution`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch document distribution: ${res.status}`);
  return res.json() as Promise<DocumentDistributionResponse>;
}

async function fetchComplianceMetrics(orgId: string): Promise<ComplianceMetrics> {
  const res = await fetch(`${API_BASE}/api/analytics/compliance`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch compliance metrics: ${res.status}`);
  return res.json() as Promise<ComplianceMetrics>;
}

async function fetchTrackingStats(orgId: string): Promise<TrackingStats> {
  const res = await fetch(`${API_BASE}/api/analytics/tracking`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch tracking stats: ${res.status}`);
  return res.json() as Promise<TrackingStats>;
}

async function fetchRecentActivity(orgId: string, limit = 10): Promise<RecentActivityResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  const res = await fetch(`${API_BASE}/api/analytics/activity?${params}`, {
    headers: authHeaders(orgId),
  });
  if (!res.ok) throw new Error(`Failed to fetch recent activity: ${res.status}`);
  return res.json() as Promise<RecentActivityResponse>;
}

// --- React Query hooks ---

export function useAnalyticsDashboard() {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["analytics-dashboard", orgId],
    queryFn: () => fetchAnalyticsDashboard(orgId!),
    enabled: !!orgId,
    staleTime: 2 * 60_000,
  });
}

export function useShipmentTrends(days = 30, groupBy: TrendGroupBy = "day") {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["shipment-trends", orgId, days, groupBy],
    queryFn: () => fetchShipmentTrends(orgId!, days, groupBy),
    enabled: !!orgId,
    staleTime: 5 * 60_000,
  });
}

export function useDocumentDistribution() {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["document-distribution", orgId],
    queryFn: () => fetchDocumentDistribution(orgId!),
    enabled: !!orgId,
    staleTime: 5 * 60_000,
  });
}

export function useComplianceMetrics() {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["compliance-metrics", orgId],
    queryFn: () => fetchComplianceMetrics(orgId!),
    enabled: !!orgId,
    staleTime: 5 * 60_000,
  });
}

export function useTrackingStats() {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["tracking-stats", orgId],
    queryFn: () => fetchTrackingStats(orgId!),
    enabled: !!orgId,
    staleTime: 2 * 60_000,
  });
}

export function useRecentActivity(limit = 10) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["recent-activity", orgId, limit],
    queryFn: () => fetchRecentActivity(orgId!, limit),
    enabled: !!orgId,
    staleTime: 60_000,
  });
}
