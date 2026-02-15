/**
 * React Query hooks for Shipments API.
 *
 * These hooks wrap the auto-generated SDK functions with
 * TanStack React Query for caching, refetching, and mutations.
 *
 * PRD-007: OpenAPI → Hey API Type Bridge
 */

"use client";

// NOTE: Import paths will resolve once the client is generated.
// For now these are placeholder hooks that demonstrate the pattern.
// After running `npx @hey-api/openapi-ts`, the generated TanStack
// Query hooks in `src/lib/api/generated/` can be used directly.

export const SHIPMENTS_KEY = ["shipments"] as const;

export function shipmentsQueryKey(params?: Record<string, unknown>) {
  return params ? ([...SHIPMENTS_KEY, params] as const) : SHIPMENTS_KEY;
}

export function shipmentQueryKey(id: string) {
  return [...SHIPMENTS_KEY, id] as const;
}
