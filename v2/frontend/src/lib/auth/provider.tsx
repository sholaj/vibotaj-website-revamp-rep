"use client";

import { AuthProvider as PropelAuthProvider } from "@propelauth/nextjs/client";

/**
 * Wraps the PropelAuth AuthProvider for TraceHub.
 * Add this to the root layout to enable client-side auth hooks.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const authUrl = process.env.NEXT_PUBLIC_PROPELAUTH_URL;

  if (!authUrl) {
    // In development without PropelAuth configured, render children directly
    return <>{children}</>;
  }

  return <PropelAuthProvider authUrl={authUrl}>{children}</PropelAuthProvider>;
}
