"use client";

import { useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase, isSupabaseConfigured } from "./client";
import {
  rowToContainerEvent,
  type ContainerEventRow,
} from "@/lib/api/tracking-types";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type { RealtimeChannel } from "@supabase/supabase-js";

/**
 * Subscribe to new container events for a shipment via Supabase Realtime.
 * Invalidates React Query cache when new events arrive.
 * Returns the latest new event (for animation) and a connection status.
 */
export function useContainerEventsRealtime(
  shipmentId: string,
  onNewEvent?: (event: ReturnType<typeof rowToContainerEvent>) => void,
) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  const channelRef = useRef<RealtimeChannel | null>(null);

  useEffect(() => {
    if (!isSupabaseConfigured() || !shipmentId || !orgId) return;

    const channel = supabase
      .channel(`events:${shipmentId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "container_events",
          filter: `shipment_id=eq.${shipmentId}`,
        },
        (payload) => {
          const row = payload.new as ContainerEventRow;
          const event = rowToContainerEvent(row);

          // Invalidate React Query cache to refetch
          void queryClient.invalidateQueries({
            queryKey: ["shipment-events", orgId, shipmentId],
          });

          onNewEvent?.(event);
        },
      )
      .subscribe();

    channelRef.current = channel;

    return () => {
      void supabase.removeChannel(channel);
      channelRef.current = null;
    };
  }, [shipmentId, orgId, queryClient, onNewEvent]);
}

/**
 * Subscribe to shipment updates (status changes, ETA updates) via Supabase Realtime.
 * Invalidates shipment detail + dashboard caches.
 */
export function useShipmentRealtime(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!isSupabaseConfigured() || !shipmentId || !orgId) return;

    const channel = supabase
      .channel(`shipment:${shipmentId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "shipments",
          filter: `id=eq.${shipmentId}`,
        },
        () => {
          // Invalidate shipment detail and dashboard stats
          void queryClient.invalidateQueries({
            queryKey: ["shipment", orgId, shipmentId],
          });
          void queryClient.invalidateQueries({
            queryKey: ["dashboard-stats", orgId],
          });
        },
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [shipmentId, orgId, queryClient]);
}

/**
 * Trigger a tracking refresh via the backend API.
 * Returns mutation-like helpers.
 */
export function useRefreshTracking(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();

  const refresh = useCallback(async () => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await fetch(
      `${API_BASE}/api/tracking/refresh/${shipmentId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Organization-Id": orgId ?? "",
        },
      },
    );
    if (!res.ok) throw new Error(`Refresh failed: ${res.status}`);

    // Fallback: also refetch via React Query in case Realtime is slow
    void queryClient.invalidateQueries({
      queryKey: ["shipment-events", orgId, shipmentId],
    });
    void queryClient.invalidateQueries({
      queryKey: ["shipment", orgId, shipmentId],
    });

    return res.json();
  }, [shipmentId, orgId, queryClient]);

  return { refresh };
}
