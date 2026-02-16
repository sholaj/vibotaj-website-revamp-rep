"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type {
  ComplianceReport,
  TransitionHistoryResponse,
} from "./compliance-types";

export type {
  ComplianceReport,
  ComplianceDecision,
  RuleResult,
  RuleSeverity,
  ComplianceSummaryCount,
  ComplianceOverride,
  DocumentTransition,
  TransitionHistoryResponse,
} from "./compliance-types";

export {
  DECISION_COLORS,
  DECISION_LABELS,
  SEVERITY_COLORS,
  SEVERITY_LABELS,
  STATE_LABELS,
  getStateLabel,
  isDecisionPassing,
  countActiveFailures,
  getStateColor,
} from "./compliance-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Organization-Id": orgId,
  };
}

// --- Fetch functions ---

async function fetchComplianceReport(
  orgId: string,
  shipmentId: string,
): Promise<ComplianceReport> {
  const res = await fetch(
    `${API_BASE}/api/validation/shipments/${shipmentId}/compliance`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error("Failed to fetch compliance report");
  return res.json();
}

async function fetchTransitionHistory(
  orgId: string,
  shipmentId: string,
): Promise<TransitionHistoryResponse> {
  const res = await fetch(
    `${API_BASE}/api/validation/shipments/${shipmentId}/transitions`,
    { headers: authHeaders(orgId) },
  );
  if (!res.ok) throw new Error("Failed to fetch transition history");
  return res.json();
}

async function postComplianceOverride(
  orgId: string,
  shipmentId: string,
  reason: string,
): Promise<ComplianceReport> {
  const res = await fetch(
    `${API_BASE}/api/validation/shipments/${shipmentId}/override`,
    {
      method: "POST",
      headers: authHeaders(orgId),
      body: JSON.stringify({ reason }),
    },
  );
  if (!res.ok) throw new Error("Failed to submit compliance override");
  return res.json();
}

async function deleteComplianceOverride(
  orgId: string,
  shipmentId: string,
): Promise<ComplianceReport> {
  const res = await fetch(
    `${API_BASE}/api/validation/shipments/${shipmentId}/override`,
    {
      method: "DELETE",
      headers: authHeaders(orgId),
    },
  );
  if (!res.ok) throw new Error("Failed to clear compliance override");
  return res.json();
}

// --- React Query Hooks ---

export function useComplianceReport(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  return useQuery({
    queryKey: ["compliance-report", shipmentId, orgId],
    queryFn: () => fetchComplianceReport(orgId!, shipmentId),
    enabled: !!orgId && !!shipmentId,
    staleTime: 2 * 60_000,
  });
}

export function useTransitionHistory(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  return useQuery({
    queryKey: ["transition-history", shipmentId, orgId],
    queryFn: () => fetchTransitionHistory(orgId!, shipmentId),
    enabled: !!orgId && !!shipmentId,
    staleTime: 2 * 60_000,
  });
}

export function useSubmitOverride(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reason: string) =>
      postComplianceOverride(orgId!, shipmentId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["compliance-report", shipmentId],
      });
    },
  });
}

export function useClearOverride(shipmentId: string) {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => deleteComplianceOverride(orgId!, shipmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["compliance-report", shipmentId],
      });
    },
  });
}
