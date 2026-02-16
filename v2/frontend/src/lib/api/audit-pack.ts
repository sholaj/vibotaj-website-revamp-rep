"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type { AuditPackStatusResponse } from "./audit-pack-types";

export type {
  AuditPackStatusResponse,
  AuditPackStatus,
  AuditPackContent,
} from "./audit-pack-types";

export {
  PACK_STATUS_LABELS,
  PACK_STATUS_COLORS,
  CONTENT_TYPE_ICONS,
  isPackReady,
  isPackActionable,
  getDocumentContentCount,
  formatGeneratedAt,
} from "./audit-pack-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Organization-Id": orgId,
  };
}

// --- Fetch functions ---

async function fetchAuditPackStatus(
  orgId: string,
  shipmentId: string,
): Promise<AuditPackStatusResponse> {
  const res = await fetch(
    `${API_BASE}/api/shipments/${shipmentId}/audit-pack/status`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error("Failed to fetch audit pack status");
  return res.json();
}

async function fetchAuditPack(
  orgId: string,
  shipmentId: string,
): Promise<AuditPackStatusResponse> {
  const res = await fetch(
    `${API_BASE}/api/shipments/${shipmentId}/audit-pack`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error("Failed to get audit pack");
  return res.json();
}

async function postRegenerateAuditPack(
  orgId: string,
  shipmentId: string,
): Promise<AuditPackStatusResponse> {
  const res = await fetch(
    `${API_BASE}/api/shipments/${shipmentId}/audit-pack/regenerate`,
    {
      method: "POST",
      headers: authHeaders(orgId),
    },
  );
  if (!res.ok) throw new Error("Failed to regenerate audit pack");
  return res.json();
}

// --- React Query Hooks ---

export function useAuditPackStatus(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  return useQuery({
    queryKey: ["audit-pack-status", shipmentId, orgId],
    queryFn: () => fetchAuditPackStatus(orgId!, shipmentId),
    enabled: !!orgId && !!shipmentId,
    staleTime: 2 * 60_000,
  });
}

export function useDownloadAuditPack(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => fetchAuditPack(orgId!, shipmentId),
    onSuccess: (data) => {
      queryClient.setQueryData(
        ["audit-pack-status", shipmentId, orgId],
        data,
      );
      if (data.download_url) {
        window.open(data.download_url, "_blank");
      }
    },
  });
}

export function useRegenerateAuditPack(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => postRegenerateAuditPack(orgId!, shipmentId),
    onSuccess: (data) => {
      queryClient.setQueryData(
        ["audit-pack-status", shipmentId, orgId],
        data,
      );
    },
  });
}
