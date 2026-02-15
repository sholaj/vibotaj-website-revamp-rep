# PRD-008: v1 Frontend → v2 Infrastructure Bridge

**Status:** Specified
**Complexity:** Medium
**Target:** Week 3 (after PRD-001 through PRD-006 are deployed)
**Dependencies:** PRD-003 (PropelAuth), PRD-004 (Railway), PRD-005 (Supabase Storage), PRD-006 (Sentry)
**Branch:** `feature/prd-008-v1-frontend-bridge`

---

## Problem

The v1 React 18 + Vite frontend is tightly coupled to Hostinger infrastructure: nginx reverse-proxies `/api` to a local Docker backend, auth uses custom JWT stored in `localStorage` (`tracehub_token`), and file downloads return raw blobs from local disk. Once Phase 1 infrastructure is live (Railway, Supabase, PropelAuth, Sentry), the frontend must connect to it — otherwise the new backend has no UI.

This is a bridge, not a rewrite. The React SPA stays intact. Only the connection layer changes.

## Acceptance Criteria

1. API client (`client.ts`) points at Railway backend URL instead of nginx-proxied `/api`
2. Auth flow replaced: PropelAuth login UI → PropelAuth token → `Authorization: Bearer` header (replacing custom JWT + `tracehub_token` localStorage)
3. `AuthContext.tsx` uses PropelAuth React SDK (`@propelauth/react`) instead of manual JWT management
4. Route protection uses PropelAuth's `useAuthInfo()` / `withRequiredAuthInfo()` instead of localStorage token check
5. Role/permission helpers (`hasPermission`, `hasRole`, `hasOrgPermission`, `isAdmin`, etc.) preserved — rewired to PropelAuth user metadata
6. File downloads handle Supabase Storage signed URLs (redirect or direct fetch) instead of blob responses
7. File uploads still POST `multipart/form-data` to the same endpoint (backend handles Supabase Storage internally — transparent to frontend)
8. Sentry client-side error tracking via `@sentry/react`
9. All existing pages continue to function: login, dashboard, shipments, documents, analytics, organizations, users, invitations
10. Deployment: Vercel as static SPA export (no SSR needed for bridge phase) OR keep Docker/nginx pointing at Railway
11. Zero regressions — all existing Vitest + Playwright tests updated and passing

## Technical Approach

### 1. API Base URL — Point at Railway

```typescript
// client.ts — change base URL strategy
// Before:
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// After:
const API_BASE_URL = import.meta.env.VITE_API_URL
// .env.development: VITE_API_URL=http://localhost:8000
// .env.production:  VITE_API_URL=https://tracehub-backend.up.railway.app
```

No more nginx reverse proxy — the frontend calls Railway directly. CORS on Railway (PRD-004) must allow the frontend origin.

### 2. Auth — Replace Custom JWT with PropelAuth

**Install:**
```bash
npm install @propelauth/react
```

**Wrap app in AuthProvider:**
```tsx
// main.tsx
import { AuthProvider } from "@propelauth/react";

<AuthProvider authUrl={import.meta.env.VITE_PROPELAUTH_URL}>
  <App />
</AuthProvider>
```

**Replace token storage + injection:**
```typescript
// client.ts — remove localStorage token management entirely

// Before (remove):
const TOKEN_KEY = 'tracehub_token'
const TOKEN_EXPIRY_KEY = 'tracehub_token_expiry'
function getStoredToken() { ... }
function setStoredToken() { ... }
function clearStoredToken() { ... }
function isTokenExpired() { ... }

// After — token comes from PropelAuth SDK:
// The axios request interceptor gets the token from PropelAuth
import { getAccessToken } from "./auth-bridge";

axiosInstance.interceptors.request.use(async (config) => {
  const token = await getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

**Auth bridge module** (glue between PropelAuth SDK and existing api client):
```typescript
// src/api/auth-bridge.ts
let accessTokenFn: (() => Promise<string | null>) | null = null;

export function setAccessTokenFn(fn: () => Promise<string | null>) {
  accessTokenFn = fn;
}

export async function getAccessToken(): Promise<string | null> {
  return accessTokenFn ? await accessTokenFn() : null;
}
```

```tsx
// App.tsx — wire PropelAuth token into the bridge
import { useAuthInfo } from "@propelauth/react";
import { setAccessTokenFn } from "./api/auth-bridge";

function AppShell() {
  const auth = useAuthInfo();

  useEffect(() => {
    if (auth.loading) return;
    setAccessTokenFn(async () => {
      return auth.accessToken ?? null;
    });
  }, [auth]);

  // ... rest of app
}
```

### 3. AuthContext — Rewire to PropelAuth

The existing `AuthContext.tsx` exposes: `user`, `isAuthenticated`, `isLoading`, `login()`, `logout()`, `hasPermission()`, `hasRole()`, `hasOrgPermission()`, plus convenience flags (`isAdmin`, `isCompliance`, etc.).

**Strategy:** Keep the same context interface, replace the internals.

```tsx
// AuthContext.tsx — before:
// - Calls api.login(credentials) → stores JWT → calls api.getCurrentUserFull()
// - isAuthenticated = !!user (from /auth/me/full response)

// AuthContext.tsx — after:
// - Login/logout delegated to PropelAuth (redirect-based or hosted page)
// - User object hydrated from PropelAuth useAuthInfo() + backend /auth/me/full
// - Permission helpers read from PropelAuth user metadata (system_role)
//   + backend response (org_role, org_permissions) — same shape as CurrentUser
```

Key change: `login()` no longer accepts `(email, password)`. It triggers PropelAuth's login flow (redirect to PropelAuth hosted page, or embedded component). The `api.login()` endpoint on the backend is no longer called from the frontend.

```tsx
export function AuthProvider({ children }) {
  const propelAuth = useAuthInfo();
  const [tracehubUser, setTracehubUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    if (propelAuth.isLoggedIn && propelAuth.accessToken) {
      // Fetch TraceHub-specific user data (org permissions, etc.)
      api.getCurrentUserFull().then(setTracehubUser);
    } else {
      setTracehubUser(null);
    }
  }, [propelAuth.isLoggedIn, propelAuth.accessToken]);

  const isAuthenticated = propelAuth.isLoggedIn && !!tracehubUser;

  // hasPermission, hasRole, hasOrgPermission — unchanged logic,
  // reads from tracehubUser.permissions / tracehubUser.org_permissions
}
```

### 4. Route Protection — PropelAuth Guards

```tsx
// Before:
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" />;
  return children;
}

// After:
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth(); // Same hook, rewired internals
  const propelAuth = useAuthInfo();

  if (propelAuth.loading || isLoading) return <LoadingSpinner />;
  if (!propelAuth.isLoggedIn) {
    // Redirect to PropelAuth login
    propelAuth.redirectToLoginPage();
    return null;
  }
  if (!isAuthenticated) return <LoadingSpinner />; // Waiting for /auth/me/full
  return children;
}
```

### 5. Login Page — PropelAuth Hosted or Embedded

Two options:

**Option A: PropelAuth hosted login page (recommended for bridge)**
- Remove `/login` route entirely
- `ProtectedRoute` redirects unauthenticated users to PropelAuth's hosted login
- Zero frontend login code to maintain
- Branded with TraceHub logo + colors in PropelAuth dashboard

**Option B: Embedded PropelAuth components**
- Keep `/login` route, replace form with `<LoginComponent />` from `@propelauth/react`
- More visual control, but more maintenance

Recommend Option A for bridge phase — simplest, least code to change.

### 6. File Downloads — Signed URLs

The backend (PRD-005) returns signed URLs instead of raw blobs. The frontend needs to handle both patterns during migration:

```typescript
// Before:
async downloadDocument(documentId: string): Promise<Blob> {
  const response = await this.axiosInstance.get(
    `documents/${documentId}/download`,
    { responseType: 'blob' }
  );
  return response.data;
}

// After:
async downloadDocument(documentId: string): Promise<string> {
  // Backend returns { url: "https://...supabase.co/storage/..." }
  const response = await this.axiosInstance.get(
    `documents/${documentId}/download`
  );
  return response.data.url; // Signed URL — open in new tab or trigger download
}
```

Components that trigger downloads (document list, audit pack, EUDR report) update from:
```tsx
// Before:
const blob = await api.downloadDocument(id);
const url = URL.createObjectURL(blob);
window.open(url);

// After:
const signedUrl = await api.downloadDocument(id);
window.open(signedUrl, '_blank');
```

File uploads are **unchanged** — the frontend still POSTs `multipart/form-data` to the same endpoint. The backend internally stores to Supabase Storage (transparent to frontend).

### 7. Sentry Client-Side

```bash
npm install @sentry/react
```

```tsx
// main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.VITE_ENVIRONMENT || "development",
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.reactRouterV6BrowserTracingIntegration({ useEffect, useLocation, useNavigationType, createRoutesFromChildren, matchRoutes }),
  ],
  tracesSampleRate: import.meta.env.VITE_ENVIRONMENT === "production" ? 0.1 : 1.0,
  sendDefaultPii: false,
});
```

Wrap `<App />` in `<Sentry.ErrorBoundary>` for automatic error capture.

### 8. Deployment — Vercel Static SPA

The v1 React app can deploy to Vercel as a static export:

```json
// vercel.json (at tracehub/frontend/)
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

SPA fallback (`rewrites` to `index.html`) replaces nginx's `try_files`. No SSR — pure static hosting with Vercel's edge CDN.

Alternatively, keep Docker/nginx but change the proxy target from `http://backend:8000` to Railway URL. This is the lower-risk option if Vercel deployment has issues.

### 9. Environment Variables — Updated Set

| Variable | Old Value | New Value | Notes |
|----------|-----------|-----------|-------|
| `VITE_API_URL` | `/api` | `https://tracehub-backend.up.railway.app` | Direct to Railway |
| `VITE_PROPELAUTH_URL` | _(new)_ | `https://auth.tracehub.vibotaj.com` | PropelAuth auth URL |
| `VITE_SENTRY_DSN` | _(new)_ | `https://...@sentry.io/...` | Sentry frontend DSN |
| `VITE_ENVIRONMENT` | _(new)_ | `production` / `development` | Environment tag |
| `VITE_APP_NAME` | `VIBOTAJ TraceHub` | `VIBOTAJ TraceHub` | Unchanged |
| `VITE_ENABLE_CONTAINER_TRACKING` | `true` | `true` | Unchanged |
| `VITE_ENABLE_DOCUMENT_UPLOAD` | `true` | `true` | Unchanged |
| `VITE_ENABLE_AI_VALIDATION` | `false` | `false` | Unchanged |

Remove: No variables removed — feature flags stay.

## Files to Modify

```
tracehub/frontend/
  package.json                        # ADD: @propelauth/react, @sentry/react
  .env.example                        # UPDATE: new vars
  .env.development                    # UPDATE: new vars
  .env.production                     # UPDATE: Railway URL, PropelAuth URL, Sentry DSN
  vercel.json                         # NEW: Vercel static SPA config (if deploying to Vercel)
  src/
    main.tsx                          # MODIFY: wrap in PropelAuth AuthProvider + Sentry init
    App.tsx                           # MODIFY: ProtectedRoute uses PropelAuth guards
    api/
      client.ts                       # MODIFY: remove JWT storage, add PropelAuth token injection
      auth-bridge.ts                  # NEW: glue between PropelAuth SDK and axios interceptor
    contexts/
      AuthContext.tsx                  # MODIFY: rewire to PropelAuth + /auth/me/full hydration
    pages/
      Login.tsx                       # MODIFY: replace form with PropelAuth redirect (or remove)
    components/
      DocumentUploadModal.tsx         # UNCHANGED (uploads still POST multipart to same endpoint)
      ShipmentDocuments.tsx           # MODIFY: download via signed URL instead of blob (if exists)
      AuditPackButton.tsx             # MODIFY: download via signed URL (if exists)
```

## What Does NOT Change

- **All page components** — shipments, dashboard, analytics, organizations, users, invitations
- **All Tailwind styling** — same classes, same index.css tokens
- **React Router structure** — same routes, same nested layout
- **File upload flow** — same FormData POST, same 50MB limit, same timeout
- **Permission/role helpers interface** — `hasPermission()`, `hasRole()`, `isAdmin` etc. same API
- **Recharts analytics** — same components, same data shape
- **Lucide icons** — unchanged
- **Invitation accept flow** — `/accept-invitation/:token` stays public

## v1 Source of Truth

| v1 File | Lines | What Changes |
|---------|-------|-------------|
| `tracehub/frontend/src/api/client.ts` | 1,777 | Remove JWT storage (lines 217-239), rewire interceptor to PropelAuth token, change download methods from blob to signed URL |
| `tracehub/frontend/src/contexts/AuthContext.tsx` | ~200 | Replace JWT login/logout with PropelAuth SDK, keep permission helpers |
| `tracehub/frontend/src/App.tsx` | ~150 | ProtectedRoute uses PropelAuth guard, wrap in Sentry ErrorBoundary |
| `tracehub/frontend/src/main.tsx` | ~20 | Add AuthProvider + Sentry.init |
| `tracehub/frontend/src/pages/Login.tsx` | ~100 | Replace form with PropelAuth redirect or remove entirely |

## Testing Strategy

- **Unit tests (Vitest):** AuthContext provides same interface — mock PropelAuth SDK, verify `hasPermission`, `hasRole`, `isAdmin` produce correct values
- **Unit tests:** API client injects PropelAuth token correctly in request interceptor
- **Unit tests:** Download methods return signed URL string (not blob)
- **Integration test:** PropelAuth login → token → API call to Railway → authorized response
- **Playwright E2E:** Login flow via PropelAuth → navigate all pages → verify data loads
- **Playwright E2E:** Document upload → download via signed URL → file opens
- **Regression:** All existing Vitest tests updated to mock PropelAuth instead of JWT — no skipped tests

## Migration Notes

- **Cutover is atomic:** Once this ships, the frontend talks to Railway + PropelAuth + Supabase. No gradual rollout needed since there are no active users.
- **v1 backend login endpoint** (`POST /auth/login`) becomes unused by the frontend but stays in the code (PropelAuth backend validates tokens instead).
- **localStorage cleanup:** On first load after deploy, clear `tracehub_token` and `tracehub_token_expiry` — stale JWT tokens are meaningless once PropelAuth is active.
- **Demo user removed:** The `00000000-0000-0000-0000-000000000001` demo fallback in the backend is not replicated in PropelAuth.
- **CORS:** Railway backend must allow the Vercel domain (or Docker host domain) in `CORS_ORIGINS`.
- **Invitation accept flow:** `/accept-invitation/:token` currently calls v1 backend — needs to work with PropelAuth's user creation. May need a PropelAuth webhook or custom signup flow for invited users.
- **Estimated change surface:** ~500 lines modified across 5-6 files. No new pages, no new components, no layout changes.
