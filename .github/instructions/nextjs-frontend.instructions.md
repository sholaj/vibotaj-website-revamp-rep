---
applyTo: "v2/frontend/**/*.ts,v2/frontend/**/*.tsx"
---

# Next.js Frontend Conventions (v2)

## Stack

- Next.js 15 (App Router)
- TypeScript (strict mode)
- Tailwind CSS
- Shadcn UI components
- TanStack Query (React Query) for server state
- Hey API generated client (from FastAPI OpenAPI spec)
- PropelAuth for authentication
- Zod for runtime validation
- Sentry for error monitoring
- Vitest + Testing Library for unit tests
- Playwright for E2E tests

## Directory Structure

```
v2/frontend/src/
  app/                  — Next.js App Router pages
    (dashboard)/        — Protected app routes (layout with auth)
    (auth)/             — Login/signup pages
    api/                — BFF API routes (proxy to FastAPI)
  components/           — Shared UI components (Shadcn-based)
  lib/                  — Utilities, API client, hooks
    api/generated/      — Hey API auto-generated TypeScript client
  hooks/                — Custom React hooks
```

## Type Safety

- No `any` types — ever. Use `unknown` and narrow with type guards.
- All API responses validated with Zod at boundaries
- TypeScript client auto-generated from FastAPI OpenAPI spec via Hey API
- Never manually define types that mirror backend models

```bash
# Regenerate TypeScript client
npx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o src/lib/api/generated
```

## Component Patterns

- Use Shadcn UI primitives — don't reinvent form inputs, dialogs, tables
- Compose with `cn()` utility for conditional Tailwind classes
- Server Components by default; add `"use client"` only when needed
- Keep client components small and focused

```tsx
// Prefer server components
export default async function ShipmentsPage() {
  const shipments = await getShipments()
  return <ShipmentTable data={shipments} />
}

// Client component only for interactivity
"use client"
export function ShipmentActions({ id }: { id: string }) {
  const mutation = useApproveShipment()
  return <Button onClick={() => mutation.mutate(id)}>Approve</Button>
}
```

## Data Fetching

- TanStack Query for client-side data fetching and caching
- Server Components with `fetch()` for initial page loads
- BFF API routes for auth proxy and response shaping
- Never call FastAPI directly from client — always via BFF

```tsx
// TanStack Query pattern
const { data, isLoading } = useQuery({
  queryKey: ['shipments', orgId],
  queryFn: () => api.shipments.list({ organizationId: orgId }),
})
```

## Authentication

- PropelAuth React components for login/signup flows
- Auth state from PropelAuth hooks (`useAuthInfo`, `useLogoutFunction`)
- Protected routes via layout-level auth checks
- Organization context from auth token — never from URL params

## BFF API Routes

```
app/api/
  auth/         — PropelAuth callbacks
  shipments/    — Proxy to FastAPI with auth headers
  documents/    — Proxy to FastAPI with auth headers
```

- Proxy to FastAPI — never duplicate business logic
- Add auth headers from PropelAuth session
- Shape responses for frontend consumption (remove internal fields)
- Cache where appropriate

## Anti-Patterns

- Never use `any` — find the right type or use `unknown`
- Never call backend API directly from client components
- Never store auth tokens in localStorage — use PropelAuth session
- Never duplicate backend validation — validate at boundaries with Zod
- Never use CSS modules — use Tailwind + Shadcn
- Never use Redux/Zustand — prefer server-derived state via TanStack Query
