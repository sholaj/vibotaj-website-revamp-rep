/**
 * React Query hooks for Organizations API.
 *
 * PRD-007: OpenAPI → Hey API Type Bridge
 */

"use client";

export const ORGANIZATIONS_KEY = ["organizations"] as const;

export function organizationsQueryKey(params?: Record<string, unknown>) {
  return params ? ([...ORGANIZATIONS_KEY, params] as const) : ORGANIZATIONS_KEY;
}

export function organizationQueryKey(id: string) {
  return [...ORGANIZATIONS_KEY, id] as const;
}
