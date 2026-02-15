/**
 * React Query hooks for Documents API.
 *
 * PRD-007: OpenAPI → Hey API Type Bridge
 */

"use client";

export const DOCUMENTS_KEY = ["documents"] as const;

export function documentsQueryKey(params?: Record<string, unknown>) {
  return params ? ([...DOCUMENTS_KEY, params] as const) : DOCUMENTS_KEY;
}

export function documentQueryKey(id: string) {
  return [...DOCUMENTS_KEY, id] as const;
}
