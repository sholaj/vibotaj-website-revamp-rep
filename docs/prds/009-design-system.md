# PRD-009: Design System — Shadcn Component Kit + Domain Composites

**Status:** Specified
**Complexity:** Medium
**Target:** Week 5
**Dependencies:** PRD-001 (Next.js scaffold), PRD-008 (v1 bridge — existing layout/tokens)
**Branch:** `feature/prd-009-design-system`

---

## Problem

The v2 Next.js scaffold (PRD-001/008) has Shadcn configured with brand tokens, a basic layout shell, and 13 UI primitives. But Phase 2 pages (dashboard, shipments, documents, analytics, user management) need ~15 more Shadcn components, a dark mode toggle, role-based navigation, and reusable domain composites (status badges, data tables, page headers, empty/loading/error states). Without these building blocks, every Phase 2 PRD will reinvent the same patterns.

## Acceptance Criteria

### Shadcn Component Kit
1. All Shadcn components needed for Phase 2 are installed: `table`, `dialog`, `dropdown-menu`, `tabs`, `form`, `select`, `textarea`, `avatar`, `alert`, `progress`, `scroll-area`, `switch`, `checkbox`, `radio-group`, `command`, `popover`, `breadcrumb`, `collapsible`
2. All components render correctly in both light and dark mode

### Dark Mode
3. `next-themes` installed and configured with `ThemeProvider` wrapping the app
4. Dark mode toggle component in the header (sun/moon icon button)
5. Theme persists across page reloads (localStorage)
6. System preference detection as default (`system` → `light` | `dark`)

### Role-Based Navigation
7. Sidebar uses Next.js `Link` (not `<a>` tags) for client-side navigation
8. Active route highlighted via `usePathname()`
9. Navigation items filtered by user role:
   - **admin:** All items (Dashboard, Shipments, Documents, Compliance, Analytics, Users, Organizations, Settings)
   - **compliance_officer:** Dashboard, Shipments, Documents, Compliance, Analytics
   - **logistics:** Dashboard, Shipments, Documents
   - **buyer:** Dashboard, Shipments (own org), Documents (own org)
   - **supplier:** Dashboard, Shipments (own org), Documents (own org)
   - **viewer:** Dashboard, Shipments (read-only)
10. Sidebar groups are collapsible (Operations, Compliance, Admin)
11. Mobile-responsive: sidebar collapses to sheet overlay on small screens (already via Shadcn sidebar)

### Domain Composites
12. `StatusBadge` — renders shipment status, document status, or role with correct color/icon. Accepts `variant` (shipment | document | role | compliance) and `status` string. Uses Shadcn Badge internally.
13. `DataTable` — generic sortable/filterable table built on Shadcn Table + `@tanstack/react-table`. Accepts column definitions and data array. Includes pagination, row selection, and column visibility toggle.
14. `PageHeader` — title, optional breadcrumbs (Shadcn Breadcrumb), optional description, optional action buttons slot. Consistent spacing across all pages.
15. `EmptyState` — centered icon + heading + description + optional CTA button. Configurable icon and text.
16. `LoadingState` — skeleton placeholders matching common layouts (table rows, card grid, detail page). Uses Shadcn Skeleton.
17. `ErrorState` — error icon + message + optional retry button. Matches v1 error pattern.
18. `ConfirmDialog` — wraps Shadcn AlertDialog. Title, description, confirm/cancel buttons with loading state. Used for delete confirmations.

### Testing
19. All domain composites have Vitest + Testing Library tests
20. StatusBadge tests cover all variant/status combinations
21. DataTable tests cover sorting, filtering, pagination, empty state
22. Dark mode toggle test verifies theme switching
23. Navigation tests verify role-based filtering (admin sees all, viewer sees minimal)

## API Changes

None — this is frontend-only.

## Database Changes

None.

## Frontend Changes

### New Dependencies
```bash
npm install next-themes @tanstack/react-table
```

### New Files
```
v2/frontend/src/
  components/
    theme/
      theme-provider.tsx         # next-themes ThemeProvider wrapper
      theme-toggle.tsx           # Sun/Moon toggle button
    domain/
      status-badge.tsx           # StatusBadge composite
      data-table.tsx             # DataTable composite (generic)
      data-table-pagination.tsx  # Pagination sub-component
      data-table-column-header.tsx  # Sortable column header
      data-table-toolbar.tsx     # Filter/search/column visibility toolbar
      page-header.tsx            # PageHeader composite
      empty-state.tsx            # EmptyState composite
      loading-state.tsx          # LoadingState composite (skeleton variants)
      error-state.tsx            # ErrorState composite
      confirm-dialog.tsx         # ConfirmDialog composite
  lib/
    navigation.ts               # Nav items + role filtering logic
  __tests__/
    components/
      status-badge.test.tsx
      data-table.test.tsx
      page-header.test.tsx
      empty-state.test.tsx
      loading-state.test.tsx
      error-state.test.tsx
      confirm-dialog.test.tsx
      theme-toggle.test.tsx
      navigation.test.tsx
```

### Modified Files
```
v2/frontend/src/
  app/layout.tsx                           # Wrap in ThemeProvider
  app/globals.css                          # (no changes — tokens already set)
  components/layout/header.tsx             # Add ThemeToggle, wire user menu
  components/layout/app-sidebar.tsx        # Role-based nav, Next.js Link, collapsible groups, active states
```

## Compliance Impact

None — design system has no compliance logic. Check `docs/COMPLIANCE_MATRIX.md` confirmed: no HS code or EUDR impact.

## Status Badge Variants

### Shipment Status
| Status | Color | Icon |
|--------|-------|------|
| `draft` | info (blue) | `FileEdit` |
| `docs_pending` | warning (amber) | `Clock` |
| `docs_complete` | success (green) | `CheckCircle` |
| `in_transit` | info (blue) | `Ship` |
| `arrived` | success (green) | `MapPin` |
| `customs` | warning (amber) | `Shield` |
| `delivered` | success (green) | `CheckCircle2` |
| `archived` | muted (gray) | `Archive` |

### Document Status
| Status | Color | Icon |
|--------|-------|------|
| `pending` | muted (gray) | `Clock` |
| `uploaded` | warning (amber) | `Clock` |
| `under_review` | info (blue) | `Eye` |
| `approved` | success (green) | `CheckCircle` |
| `rejected` | destructive (red) | `XCircle` |
| `expired` | warning (amber) | `AlertTriangle` |

### Role
| Role | Color |
|------|-------|
| `admin` | purple (`bg-purple-100 text-purple-700`) |
| `compliance_officer` | blue |
| `logistics` | teal |
| `buyer` | green |
| `supplier` | orange |
| `viewer` | gray |

## Navigation Structure

```typescript
const NAV_GROUPS = [
  {
    label: "Operations",
    items: [
      { name: "Dashboard", href: "/dashboard", icon: BarChart3, roles: ALL_ROLES },
      { name: "Shipments", href: "/shipments", icon: Package, roles: ALL_ROLES },
      { name: "Documents", href: "/documents", icon: FileText, roles: ["admin", "compliance_officer", "logistics", "buyer", "supplier"] },
    ],
  },
  {
    label: "Compliance",
    items: [
      { name: "Compliance", href: "/compliance", icon: ShieldCheck, roles: ["admin", "compliance_officer"] },
      { name: "Analytics", href: "/analytics", icon: BarChart3, roles: ["admin", "compliance_officer"] },
    ],
  },
  {
    label: "Admin",
    items: [
      { name: "Users", href: "/users", icon: Users, roles: ["admin"] },
      { name: "Organizations", href: "/organizations", icon: Building2, roles: ["admin"] },
      { name: "Settings", href: "/settings", icon: Settings, roles: ["admin"] },
    ],
  },
];
```

## Testing Strategy

- **Unit tests (Vitest + Testing Library):** Each domain composite tested in isolation
- **StatusBadge:** Render every variant/status combo, verify correct color class and icon
- **DataTable:** Mount with mock columns/data, test sort click changes order, filter input filters rows, pagination buttons navigate pages, empty state shown when no data
- **PageHeader:** Render with/without breadcrumbs, with/without actions
- **EmptyState/ErrorState/LoadingState:** Render with props, verify text and icon presence
- **ConfirmDialog:** Open, click confirm (verify callback), click cancel (verify closes)
- **ThemeToggle:** Click toggles between light/dark, verify html class changes
- **Navigation:** Filter nav items by role, verify admin sees all, viewer sees minimal

## Out of Scope

- Storybook / Ladle catalog (can add later if needed)
- i18n / RTL support
- Animation library (framer-motion) — use CSS transitions only
- Custom icon set — stick with Lucide
- Page-level components (those belong to PRD-010 through PRD-015)
