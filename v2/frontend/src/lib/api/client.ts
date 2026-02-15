/**
 * Hey API client instance with PropelAuth authentication interceptor.
 *
 * Import this client in components that need API access.
 * The auth token is automatically injected from PropelAuth.
 *
 * PRD-007: OpenAPI → Hey API Type Bridge
 */

import { createClient } from "@hey-api/client-fetch";

export const apiClient = createClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

/**
 * Set the auth token on the client.
 * Called from the AuthProvider when the PropelAuth token is available.
 */
export function setAuthToken(token: string | null): void {
  if (token) {
    apiClient.setConfig({
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }
}

/**
 * Set the active organization ID header.
 * Used by the backend to resolve org context for multi-tenant queries.
 */
export function setOrganizationId(orgId: string | null): void {
  if (orgId) {
    apiClient.setConfig({
      headers: {
        "X-Organization-Id": orgId,
      },
    });
  }
}
