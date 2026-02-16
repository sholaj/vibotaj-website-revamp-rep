"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type {
  BolParsedResponse,
  BolSyncPreviewResponse,
  CrossValidationIssue,
} from "./bol-types";

export type {
  BolParsedResponse,
  BolSyncPreviewResponse,
  BolField,
  SyncChange,
  BolComplianceResult,
  BolParseStatus,
  CrossValidationIssue,
} from "./bol-types";

export {
  PARSE_STATUS_LABELS,
  PARSE_STATUS_COLORS,
  BOL_FIELD_LABELS,
  SYNC_FIELD_LABELS,
  isParsed,
  isBol,
  getConfidenceLevel,
  getConfidenceColor,
  formatConfidence,
  countUpdates,
  countPlaceholders,
  getOrderedFieldKeys,
} from "./bol-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Organization-Id": orgId,
  };
}

// --- Fetch functions ---

async function fetchBolParsed(
  orgId: string,
  documentId: string,
): Promise<BolParsedResponse> {
  const res = await fetch(
    `${API_BASE}/api/documents/${documentId}/bol/parsed`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error("Failed to fetch BoL parsed data");
  return res.json();
}

async function fetchBolSyncPreview(
  orgId: string,
  documentId: string,
): Promise<BolSyncPreviewResponse> {
  const res = await fetch(
    `${API_BASE}/api/documents/${documentId}/bol/sync-preview-v2`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error("Failed to fetch sync preview");
  return res.json();
}

async function fetchBolCrossValidation(
  orgId: string,
  documentId: string,
): Promise<CrossValidationIssue[]> {
  const res = await fetch(
    `${API_BASE}/api/documents/${documentId}/bol/cross-validation`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error("Failed to fetch cross-validation");
  return res.json();
}

async function postBolSync(
  orgId: string,
  documentId: string,
): Promise<{ synced_fields: string[] }> {
  const res = await fetch(
    `${API_BASE}/api/documents/${documentId}/bol/sync`,
    {
      method: "POST",
      headers: authHeaders(orgId),
    },
  );
  if (!res.ok) throw new Error("Failed to sync BoL data");
  return res.json();
}

async function postBolReparse(
  orgId: string,
  documentId: string,
): Promise<BolParsedResponse> {
  const res = await fetch(
    `${API_BASE}/api/documents/${documentId}/bol/parse`,
    {
      method: "POST",
      headers: authHeaders(orgId),
    },
  );
  if (!res.ok) throw new Error("Failed to re-parse BoL");
  return res.json();
}

// --- React Query Hooks ---

export function useBolParsedData(documentId: string) {
  const { orgId } = useCurrentOrg();
  return useQuery({
    queryKey: ["bol-parsed", documentId, orgId],
    queryFn: () => fetchBolParsed(orgId!, documentId),
    enabled: !!orgId && !!documentId,
    staleTime: 5 * 60_000,
  });
}

export function useBolSyncPreview(documentId: string) {
  const { orgId } = useCurrentOrg();
  return useQuery({
    queryKey: ["bol-sync-preview", documentId, orgId],
    queryFn: () => fetchBolSyncPreview(orgId!, documentId),
    enabled: !!orgId && !!documentId,
    staleTime: 2 * 60_000,
  });
}

export function useBolCrossValidation(documentId: string) {
  const { orgId } = useCurrentOrg();
  return useQuery({
    queryKey: ["bol-cross-validation", documentId, orgId],
    queryFn: () => fetchBolCrossValidation(orgId!, documentId),
    enabled: !!orgId && !!documentId,
    staleTime: 5 * 60_000,
  });
}

export function useApplyBolSync(documentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => postBolSync(orgId!, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["bol-sync-preview", documentId],
      });
      queryClient.invalidateQueries({
        queryKey: ["bol-parsed", documentId],
      });
      queryClient.invalidateQueries({ queryKey: ["shipment-detail"] });
    },
  });
}

export function useReParseBol(documentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => postBolReparse(orgId!, documentId),
    onSuccess: (data) => {
      queryClient.setQueryData(
        ["bol-parsed", documentId, orgId],
        data,
      );
      queryClient.invalidateQueries({
        queryKey: ["bol-sync-preview", documentId],
      });
    },
  });
}
