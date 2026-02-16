# PRD-011: Dashboard + Shipment List

**Status:** Specified
**Complexity:** Medium
**Target:** Week 6
**Dependencies:** PRD-009 (design system), PRD-010 (auth/org context)
**Branch:** `feature/prd-011-dashboard-shipment-list`

---

## Problem

The v2 Next.js app has auth, a design system, and an org context — but no actual pages. The v1 dashboard is a flat shipment card list with no analytics. Users need a dashboard with at-a-glance KPIs and charts, plus a proper shipment list page with search, filtering, sorting, and pagination.

## Acceptance Criteria

### Dashboard (`/dashboard`)
1. KPI stat cards row: Total Shipments, Docs Pending, In Transit, Compliance Rate (% of shipments with docs complete)
2. Shipment status breakdown chart (bar or donut) — count per status
3. Monthly shipment volume chart (bar chart) — shipments created per month (last 6 months)
4. Compliance trend chart (line chart) — compliance rate over last 6 months
5. Recent shipments table — last 5 shipments with reference, status badge, destination, ETA
6. Quick actions: "New Shipment" button (permission-gated to `shipments:create` roles)
7. All data scoped to current org via `useCurrentOrg()`
8. Loading skeletons while data fetches
9. Error state with retry

### Shipment List (`/shipments`)
10. Full DataTable (from PRD-009) with columns: Reference, Container, Status, Route (POL → POD), ETA, Created
11. Sortable columns: Reference, Status, ETA, Created
12. Status filter dropdown (all statuses + "All")
13. Text search on reference and container number
14. Server-side pagination via API `limit`/`offset` params
15. Row click navigates to shipment detail (link, not modal)
16. "New Shipment" button in PageHeader (permission-gated)
17. Empty state when no shipments match filters
18. Loading state while fetching

### Data Fetching
19. React Query (`@tanstack/react-query`) for all API calls
20. Query keys scoped to org: `["shipments", orgId, { status, search, page }]`
21. Stale time: 30 seconds for shipment list, 5 minutes for dashboard stats
22. Prefetch on hover for shipment detail (future PRD-012)

### Testing
23. Dashboard: KPI cards render with mock data, charts render, recent shipments table renders
24. Shipment list: DataTable renders columns, filter changes query params, search filters rows, pagination works
25. Permission gating: "New Shipment" button hidden for viewer role
26. Org scoping: changing org refetches data

## API Changes

None — uses existing v1 backend endpoints:
- `GET /api/shipments?status=X&limit=N&offset=N` → `ShipmentListResponse`
- Dashboard stats computed client-side from shipment list (no dedicated stats endpoint in v1)

## Database Changes

None.

## Frontend Changes

### New Dependencies
```bash
npm install recharts
```

### New Files
```
v2/frontend/src/
  app/
    dashboard/
      page.tsx                    # Dashboard page
    shipments/
      page.tsx                    # Shipment list page
  components/dashboard/
    kpi-cards.tsx                 # KPI stat cards row
    status-chart.tsx              # Shipment status breakdown chart
    volume-chart.tsx              # Monthly volume bar chart
    compliance-chart.tsx          # Compliance trend line chart
    recent-shipments.tsx          # Recent shipments table
  components/shipments/
    shipment-columns.tsx          # TanStack Table column definitions
    shipment-filters.tsx          # Status filter + search toolbar
  lib/api/
    shipments.ts                  # React Query hooks: useShipments, useDashboardStats
  lib/api/__tests__/
    shipments.test.ts             # API hook tests
  components/dashboard/__tests__/
    kpi-cards.test.tsx
    status-chart.test.tsx
  components/shipments/__tests__/
    shipment-list.test.tsx
```

### Modified Files
None — all new pages/components.

## Compliance Impact

None — display only, no compliance logic changes.

## KPI Cards Design

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 📦 Total     │ │ 📋 Docs      │ │ 🚢 In Transit│ │ ✅ Compliance │
│    42        │ │    Pending   │ │    8         │ │    Rate      │
│ shipments    │ │    12        │ │ shipments    │ │    71%       │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

Uses Shadcn Card with icon, value, label. Color-coded: info, warning, info, success/warning.

## Shipment Table Columns

| Column | Accessor | Sortable | Width |
|--------|----------|----------|-------|
| Reference | `reference` | Yes | 150px |
| Container | `container_number` | No | 150px |
| Status | `status` | Yes | 130px |
| Route | `pol_code` → `pod_code` | No | 200px |
| ETA | `eta` | Yes | 120px |
| Created | `created_at` | Yes | 120px |

Status column renders `StatusBadge variant="shipment"`.

## Chart Specifications

### Status Breakdown (Bar/Donut)
- Data: count of shipments per status
- Colors: match StatusBadge colors (info, warning, success, muted)
- Library: Recharts `<BarChart>` or `<PieChart>`

### Monthly Volume (Bar Chart)
- Data: shipments created per month, last 6 months
- X-axis: month labels, Y-axis: count
- Color: primary blue

### Compliance Trend (Line Chart)
- Data: % of shipments with `docs_complete`/`delivered` status per month
- X-axis: month labels, Y-axis: percentage (0-100%)
- Color: success green

## Testing Strategy

- **KPI cards:** Mock shipments array → compute stats → verify card values
- **Charts:** Render with mock data → verify SVG elements present (Recharts)
- **Recent shipments:** Render table with 5 mock shipments → verify rows + status badges
- **Shipment list:** Mount with mock data → test sort click, filter change, search input, pagination navigation, empty state
- **Permission:** Render as viewer → "New Shipment" button not present. Render as admin → button present.
- **Org scoping:** Verify query keys include orgId

## Out of Scope

- Shipment detail page (PRD-012)
- Shipment create/edit modals (PRD-012)
- Real-time updates (PRD-013)
- Server-side rendering of dashboard (client-side for now — SSR deferred)
