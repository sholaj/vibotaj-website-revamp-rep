# PRD-014: Analytics Dashboard

## Problem Statement

The v2 dashboard (PRD-011) computes stats client-side from a bulk shipment fetch — this won't scale and lacks document-level analytics, real compliance metrics, tracking stats, and activity feeds. The v1 backend has 7 dedicated analytics endpoints that return pre-computed metrics. PRD-014 wires the v2 frontend to these endpoints with rich visualizations.

## Dependencies

- PRD-009 (Design system — Shadcn + Recharts)
- PRD-011 (Dashboard page — will be extended)

## Scope

**In scope:**
- Analytics types matching all 7 v1 backend response schemas
- React Query hooks for each analytics endpoint
- Shipment trends chart (line chart, day/week/month selector)
- Document distribution donut chart (by status)
- Compliance panel with EUDR coverage progress rings
- Tracking stats card (events today, delays, containers tracked)
- Alert banners (expiring documents, delayed shipments)
- Recent activity feed (audit log entries)
- Dedicated `/analytics` page
- Update existing dashboard to use real backend endpoints instead of client-side computation

**Out of scope:**
- New backend endpoints (v1 analytics endpoints are sufficient)
- Export/download analytics data
- Date range pickers (future enhancement)

## Acceptance Criteria

1. `/analytics` page renders with all 6 sections: KPI cards, trends chart, document distribution, compliance panel, tracking stats, activity feed
2. Trends chart supports day/week/month grouping via toggle
3. Document distribution renders as donut chart with status legend
4. Compliance panel shows two progress rings: overall rate + EUDR coverage
5. Alert banners appear conditionally (expiring docs > 0, delayed shipments > 0)
6. Activity feed shows last 10 entries with actor, action, timestamp
7. All data fetched via React Query hooks from `/api/analytics/*` endpoints
8. Loading skeletons shown while data loads
9. Error states with retry buttons
10. All components have Vitest tests

## API Integration

Uses existing v1 backend endpoints (all require auth, all filter by org):

| Endpoint | Hook | Used By |
|----------|------|---------|
| `GET /api/analytics/dashboard` | `useAnalyticsDashboard` | KPI cards, alerts |
| `GET /api/analytics/shipments` | `useShipmentStats` | Shipment metrics |
| `GET /api/analytics/shipments/trends?days=30&group_by=day` | `useShipmentTrends` | Trends chart |
| `GET /api/analytics/documents` | `useDocumentStats` | Document metrics |
| `GET /api/analytics/documents/distribution` | `useDocumentDistribution` | Donut chart |
| `GET /api/analytics/compliance` | `useComplianceMetrics` | Compliance panel |
| `GET /api/analytics/tracking` | `useTrackingStats` | Tracking card |

## Frontend Changes

### New Files
- `src/lib/api/analytics-types.ts` — Pure types for all 7 analytics responses
- `src/lib/api/analytics.ts` — React Query hooks for analytics endpoints
- `src/components/analytics/trends-chart.tsx` — Line chart with time window selector
- `src/components/analytics/document-distribution-chart.tsx` — Donut chart by status
- `src/components/analytics/compliance-panel.tsx` — Two progress rings + metrics
- `src/components/analytics/tracking-stats-card.tsx` — Tracking KPI card
- `src/components/analytics/alert-banners.tsx` — Conditional warning/danger alerts
- `src/components/analytics/activity-feed.tsx` — Recent audit log entries
- `src/app/analytics/page.tsx` — Analytics page composing all sections

### Modified Files
- `src/app/dashboard/page.tsx` — Replace client-side `computeStats()` with `useAnalyticsDashboard` hook
- `src/components/domain/progress-ring.tsx` — Reusable SVG progress ring component

## Database Changes

None — uses existing v1 analytics endpoints.

## Compliance Impact

None — read-only analytics. EUDR coverage percentage comes from backend compliance service which already respects horn/hoof exclusion.

## Testing

- `analytics-types.test.ts` — Type guard and helper function tests
- `trends-chart.test.tsx` — Renders chart, time window toggle works
- `document-distribution-chart.test.tsx` — Renders donut, legend shows statuses
- `compliance-panel.test.tsx` — Progress rings render correct percentages
- `tracking-stats-card.test.tsx` — Renders all tracking metrics
- `alert-banners.test.tsx` — Shows/hides based on threshold values
- `activity-feed.test.tsx` — Renders entries, empty state
