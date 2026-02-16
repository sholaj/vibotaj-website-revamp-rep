// --- Container tracking types (no React/PropelAuth dependencies) ---

export type ContainerEventType =
  | "booking_confirmed"
  | "gate_in"
  | "loaded"
  | "departed"
  | "transshipment"
  | "arrived"
  | "discharged"
  | "gate_out"
  | "delivered"
  | "customs_hold"
  | "customs_released"
  | "empty_return"
  | "unknown";

export interface ContainerEvent {
  id: string;
  event_type: ContainerEventType;
  timestamp: string;
  location_name: string | null;
  location_code: string | null;
  vessel_name: string | null;
  voyage_number: string | null;
  description: string | null;
}

export interface ShipmentEventsResponse {
  events: ContainerEvent[];
}

export const EVENT_TYPE_LABELS: Record<ContainerEventType, string> = {
  booking_confirmed: "Booking Confirmed",
  gate_in: "Gate In",
  loaded: "Loaded on Vessel",
  departed: "Departed",
  transshipment: "Transshipment",
  arrived: "Arrived at Port",
  discharged: "Discharged",
  gate_out: "Gate Out",
  delivered: "Delivered",
  customs_hold: "Customs Hold",
  customs_released: "Customs Released",
  empty_return: "Empty Return",
  unknown: "Unknown",
};

export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 30) return `${diffDays}d ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo ago`;
  return `${Math.floor(diffDays / 365)}y ago`;
}
