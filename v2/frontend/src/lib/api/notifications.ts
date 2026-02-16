"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCurrentOrg } from "@/lib/auth/org-context";
import type {
  NotificationPreferencesResponse,
  NotificationPreferencesUpdate,
} from "./notification-types";

export type {
  NotificationPreference,
  NotificationPreferencesResponse,
  NotificationPreferencesUpdate,
  NotificationEventType,
  EmailStatusResponse,
} from "./notification-types";

export {
  ALL_EVENT_TYPES,
  EVENT_TYPE_LABELS,
  EVENT_CATEGORIES,
  CATEGORY_LABELS,
  groupByCategory,
  getDefaultPreferences,
} from "./notification-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(orgId: string): Record<string, string> {
  return {
    "X-Organization-Id": orgId,
  };
}

// --- Fetch functions ---

async function fetchPreferences(
  orgId: string,
): Promise<NotificationPreferencesResponse> {
  const res = await fetch(
    `${API_BASE}/api/users/me/notification-preferences`,
    {
      headers: authHeaders(orgId),
    },
  );
  if (!res.ok) throw new Error("Failed to fetch notification preferences");
  return res.json();
}

async function updatePreferences(
  orgId: string,
  body: NotificationPreferencesUpdate,
): Promise<NotificationPreferencesResponse> {
  const res = await fetch(
    `${API_BASE}/api/users/me/notification-preferences`,
    {
      method: "PUT",
      headers: {
        ...authHeaders(orgId),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );
  if (!res.ok) throw new Error("Failed to update notification preferences");
  return res.json();
}

// --- React Query Hooks ---

export function useNotificationPreferences() {
  const { orgId } = useCurrentOrg();
  return useQuery({
    queryKey: ["notification-preferences", orgId],
    queryFn: () => fetchPreferences(orgId!),
    enabled: !!orgId,
  });
}

export function useUpdateNotificationPreferences() {
  const { orgId } = useCurrentOrg();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: NotificationPreferencesUpdate) =>
      updatePreferences(orgId!, body),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["notification-preferences"],
      });
    },
  });
}
