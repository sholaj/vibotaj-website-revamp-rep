"use client";

import { useQuery } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import {
  computeStats,
  type ShipmentListParams,
  type ShipmentListResponse,
} from "./shipment-types";

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

export function useDashboardStats() {
  const { orgId } = useCurrentOrg();

  return useQuery({
    queryKey: ["dashboard-stats", orgId],
    queryFn: async () => {
      const data = await fetchShipments(orgId!, { limit: 100, offset: 0 });
      return computeStats(data.items);
    },
    enabled: !!orgId,
    staleTime: 5 * 60_000,
  });
}
