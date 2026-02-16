# PRD-013: Container Tracking Timeline + Supabase Realtime

## Problem Statement

The shipment detail page (PRD-012) has a tracking timeline that only updates via polling (React Query staleTime: 60s) or manual page refresh. When new container events arrive from JSONCargo, users must wait or manually refresh. Supabase Realtime enables instant push updates — new events appear immediately in the timeline, status badges update live, and a live status card shows the latest container position.

## Dependencies

- PRD-002 (Supabase schema — container_events table)
- PRD-012 (shipment detail page, tracking timeline component)

## Acceptance Criteria

### Supabase Client Setup
- [ ] Install `@supabase/supabase-js`
- [ ] Create Supabase browser client at `lib/supabase/client.ts`
- [ ] Environment variables: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Realtime Subscriptions
- [ ] `useContainerEventsRealtime(shipmentId)` — subscribes to `container_events` INSERT filtered by `shipment_id`, invalidates React Query cache
- [ ] `useShipmentRealtime(shipmentId)` — subscribes to `shipments` UPDATE filtered by `id`, invalidates shipment detail cache
- [ ] Subscriptions auto-cleanup on unmount
- [ ] Graceful fallback when Realtime connection fails (polling continues)

### Live Status Card
- [ ] Shows current container position: status, vessel, location, ETA, last updated
- [ ] Loading state when no tracking data
- [ ] Error state when carrier not found
- [ ] "Sync Live Tracking" button when no events yet

### Refresh Tracking
- [ ] "Refresh Tracking" button in shipment header triggers API call
- [ ] Spinner animation while refreshing
- [ ] Success: new events appear via Realtime subscription (or fallback refetch)
- [ ] Error: toast/alert with retry option

### New Event Animation
- [ ] Pulse/highlight animation when new event arrives via Realtime
- [ ] "New event" indicator distinguishes push updates from initial load

### Event Type Mapping
- [ ] Backend enum (BOOKED, GATE_IN, etc.) mapped to frontend types (booking_confirmed, gate_in, etc.)
- [ ] Mapping handles unknown types gracefully (→ "unknown")

## API Changes

None — consume existing endpoints:
- `POST /api/tracking/refresh/{shipment_id}` — trigger JSONCargo refresh
- `GET /api/shipments/{id}/events` — fetch events (fallback)

## Database Changes

None — `container_events` table already exists with RLS (PRD-002).

## Frontend Changes

### New Files
- `lib/supabase/client.ts` — Supabase browser client
- `lib/supabase/use-realtime.ts` — Realtime subscription hooks
- `components/tracking/live-status-card.tsx` — live container position
- `components/tracking/tracking-refresh-button.tsx` — refresh with spinner

### Modified Files
- `components/tracking/tracking-timeline.tsx` — add new-event animation
- `app/shipments/[id]/page.tsx` — wire Realtime subscriptions + live status card

## Auth Model

Anon key + channel-level filters. The Supabase client uses `NEXT_PUBLIC_SUPABASE_ANON_KEY` and subscribes with `filter: shipment_id=eq.<uuid>`. Access is already validated at the API layer (PRD-012 detail page only loads if the user has org access).

## Compliance Impact

None — tracking is informational, no compliance logic changes.
