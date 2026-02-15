/**
 * Auth Bridge — glue between PropelAuth React SDK and the Axios API client.
 *
 * PropelAuth manages tokens via its SDK hooks (useAuthInfo).
 * The API client (Axios) needs a synchronous way to get the current token.
 * This bridge stores a reference to the token accessor function that
 * the PropelAuth-aware components set on mount.
 *
 * PRD-008: v1 Frontend → v2 Infrastructure Bridge
 */

let accessTokenFn: (() => Promise<string | null>) | null = null

/**
 * Called from the App shell once PropelAuth is initialized.
 * Stores a reference to the function that retrieves the current access token.
 */
export function setAccessTokenFn(fn: () => Promise<string | null>): void {
  accessTokenFn = fn
}

/**
 * Called by the Axios request interceptor to get the current bearer token.
 * Returns null if PropelAuth is not yet initialized or user is logged out.
 */
export async function getAccessToken(): Promise<string | null> {
  return accessTokenFn ? await accessTokenFn() : null
}

/**
 * Clear the stored localStorage tokens from v1 JWT auth.
 * Called once on app init to clean up stale v1 sessions.
 */
export function clearLegacyTokens(): void {
  try {
    localStorage.removeItem('tracehub_token')
    localStorage.removeItem('tracehub_token_expiry')
  } catch {
    // localStorage may be unavailable in some contexts
  }
}
