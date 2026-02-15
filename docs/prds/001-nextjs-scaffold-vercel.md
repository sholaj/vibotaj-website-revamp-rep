# PRD-001: Next.js 15 Scaffold + Vercel Deployment

**Status:** Done
**Complexity:** Medium
**Target:** Week 1
**Dependencies:** None
**Branch:** `feature/prd-001-nextjs-scaffold`

---

## Problem

v1 frontend is React 18 + Vite SPA served via Docker/Nginx on Hostinger VPS. No server-side rendering, no edge caching, no preview deploys, no incremental static regeneration. Every route change requires full client-side hydration. Deployment is SSH + rsync — no CI/CD pipeline.

## Acceptance Criteria

1. Next.js 15 App Router bootstrapped in `v2/frontend/` (coexists with v1 in `tracehub/frontend/`)
2. TypeScript strict mode (`strict: true`, `noUncheckedIndexedAccess: true`)
3. Tailwind CSS v4 with TraceHub brand tokens extracted from `tracehub/frontend/src/index.css`
4. Shadcn UI initialized (new-york variant, zinc base color)
5. Health page at `/` renders server-side with project version and environment
6. Layout shell: sidebar placeholder, header with brand name, main content area
7. Vercel project linked with preview deploys on PRs to `main`
8. ESLint (Next.js strict config) + Prettier pass with zero errors
9. `v2/frontend/.env.example` documents all required env vars

## Technical Approach

### 1. Project Bootstrap

```bash
npx create-next-app@latest v2/frontend \
  --typescript --tailwind --eslint --app --src-dir \
  --import-alias "@/*"
```

### 2. TypeScript Configuration

Extend `tsconfig.json` with strict settings:
- `strict: true`
- `noUncheckedIndexedAccess: true`
- `noUnusedLocals: true` (warning, not error — for iterative dev)
- Path alias: `@/*` → `src/*`

### 3. Tailwind v4 + Brand Tokens

Extract color tokens from v1 `tracehub/frontend/src/index.css`:
- Primary: blue-600 (TraceHub brand)
- Background: gray-50
- Text: gray-900
- Component tokens: btn-primary, btn-secondary, card, badge variants (success/warning/danger/info)

Define as CSS custom properties in `globals.css` for Shadcn compatibility.

### 4. Shadcn UI Setup

```bash
npx shadcn@latest init --defaults --base-color zinc
```

Install initial components: `button`, `card`, `input`, `label`, `badge`, `sidebar`.

### 5. Layout Shell

Server component layout matching v1 structure from `tracehub/frontend/src/components/Layout.tsx`:
- Collapsible sidebar (placeholder nav items: Shipments, Dashboard, Users, Organizations)
- Header with TraceHub brand + user menu placeholder
- Main content area with responsive padding

### 6. Vercel Deployment

- `vercel.json` with build command, output directory, env var references
- Root directory set to `v2/frontend/`
- Preview deploys enabled for all PR branches
- Production deploy on push to `main` (when v2 is ready — initially only previews)

## Files to Create

```
v2/frontend/
  package.json
  next.config.ts
  tsconfig.json
  tailwind.config.ts
  postcss.config.mjs
  .eslintrc.json
  .prettierrc
  vercel.json
  .env.example
  src/
    app/
      layout.tsx              # Root layout with sidebar + header shell
      page.tsx                # Health/landing page (SSR)
      globals.css             # Tailwind + brand tokens
    components/
      layout/
        sidebar.tsx           # Sidebar placeholder
        header.tsx            # Header with brand
        main-content.tsx      # Content wrapper
    lib/
      utils.ts                # cn() helper (Shadcn standard)
```

## v1 Reference Files

| v1 File | What to Extract |
|---------|----------------|
| `tracehub/frontend/src/index.css` | Color tokens, component classes |
| `tracehub/frontend/src/components/Layout.tsx` | Layout structure, nav items, role badge styles |
| `tracehub/frontend/package.json` | Dependency versions for compatibility reference |

## Testing Strategy

- `npm run build` succeeds with zero errors
- `npm run lint` passes with zero warnings
- TypeScript compilation (`npx tsc --noEmit`) passes
- Health page renders correct content (manual verification + Playwright smoke test later)
- Vercel preview deploy succeeds from PR branch

## Migration Notes

- v1 frontend at `tracehub/frontend/` is untouched — both coexist
- No shared dependencies between v1 and v2 — separate `node_modules`
- Brand tokens are extracted (copied), not symlinked — v2 owns its design system going forward
- Vercel project name: `tracehub-v2` (separate from any v1 hosting)
