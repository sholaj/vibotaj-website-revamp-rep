"use client";

import { useQuery } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import {
  computeStats,
  type DashboardStats,
  type ShipmentListParams,
  type ShipmentListResponse,
} from "./shipment-types";
import type { AnalyticsDashboard } from "./analytics-types";

// Re-export types for convenience
export type {
  Shipment,
  ShipmentStatus,
  ShipmentListResponse,
  ShipmentListParams,
  DashboardStats,
} from "./shipment-types";
export { computeStats, formatMonth } from "./shipment-types";

// --- API client ---

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchShipments(
  orgId: string,
  params: ShipmentListParams,
): Promise<ShipmentListResponse> {
  const searchParams = new URLSearchParams();
  if (params.status && params.status !== "all")
    searchParams.set("status", params.status);
  if (params.search) searchParams.set("search", params.search);
  searchParams.set("limit", String(params.limit ?? 20));
  searchParams.set("offset", String(params.offset ?? 0));

  const url = `${API_BASE}/api/shipments?${searchParams.toString()}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Organization-Id": orgId,
  };

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error(`Failed to fetch shipments: ${res.status}`);
  return res.json() as Promise<ShipmentListResponse>;
}

// --- React Query hooks ---

export function useShipments(params: ShipmentListParams = {}) {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["shipments", orgId, params],
    queryFn: () => fetchShipments(orgId!, params),
    enabled: !!orgId,
    staleTime: 30_000,
  });
}

async function fetchAnalyticsDashboard(
  orgId: string,
): Promise<AnalyticsDashboard> {
  const res = await fetch(`${API_BASE}/api/analytics/dashboard`, {
    headers: {
      "Content-Type": "application/json",
      "X-Organization-Id": orgId,
    },
  });
  if (!res.ok) throw new Error(`Analytics endpoint unavailable: ${res.status}`);
  return res.json() as Promise<AnalyticsDashboard>;
}

function mapAnalyticsToDashboardStats(
  a: AnalyticsDashboard,
): DashboardStats {
  return {
    totalShipments: a.shipments.total,
    docsPending: a.documents.pending_validation,
    inTransit: a.shipments.in_transit,
    complianceRate: Math.round(a.compliance.rate),
    statusBreakdown: [],
    monthlyVolume: [],
    complianceTrend: [],
    recentShipments: [],
  };
}

export function useDashboardStats() {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["dashboard-stats", orgId],
    queryFn: async () => {
      // Try real analytics endpoint first; fall back to client-side computation
      try {
        const analytics = await fetchAnalyticsDashboard(orgId!);
        return mapAnalyticsToDashboardStats(analytics);
      } catch {
        const data = await fetchShipments(orgId!, { limit: 100, offset: 0 });
        return computeStats(data.items);
      }
    },
    enabled: !!orgId,
    staleTime: 5 * 60_000,
  });
}
