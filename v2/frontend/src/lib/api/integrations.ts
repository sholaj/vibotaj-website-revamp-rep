/**
 * React Query hooks for third-party integrations (PRD-021).
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  IntegrationConfigUpdate,
  IntegrationLogsResponse,
  IntegrationsListResponse,
  IntegrationType,
  TestConnectionResponse,
} from "./integration-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as Record<string, unknown>).message as string ??
        `HTTP ${res.status}`,
    );
  }
  return res.json() as Promise<T>;
}

// --- Query keys ---

export const integrationKeys = {
  all: ["integrations"] as const,
  list: () => [...integrationKeys.all, "list"] as const,
  logs: (type: IntegrationType) =>
    [...integrationKeys.all, "logs", type] as const,
};

// --- Queries ---

export function useIntegrations() {
  return useQuery({
    queryKey: integrationKeys.list(),
    queryFn: () =>
      fetchJSON<IntegrationsListResponse>(`${API_BASE}/api/integrations`),
  });
}

export function useIntegrationLogs(type: IntegrationType) {
  return useQuery({
    queryKey: integrationKeys.logs(type),
    queryFn: () =>
      fetchJSON<IntegrationLogsResponse>(
        `${API_BASE}/api/integrations/${type}/logs?limit=10`,
      ),
  });
}

// --- Mutations ---

export function useUpdateIntegration() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      type,
      body,
    }: {
      type: IntegrationType;
      body: IntegrationConfigUpdate;
    }) =>
      fetchJSON(`${API_BASE}/api/integrations/${type}`, {
        method: "PUT",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: integrationKeys.list() });
    },
  });
}

export function useTestConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (type: IntegrationType) =>
      fetchJSON<TestConnectionResponse>(
        `${API_BASE}/api/integrations/${type}/test`,
        { method: "POST" },
      ),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: integrationKeys.all });
    },
  });
}
