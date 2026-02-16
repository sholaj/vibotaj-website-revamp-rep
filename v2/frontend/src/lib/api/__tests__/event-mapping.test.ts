import { describe, it, expect } from "vitest";
import {
  mapBackendEventType,
  rowToContainerEvent,
  type ContainerEventRow,
} from "../tracking-types";

describe("mapBackendEventType", () => {
  it("maps BOOKED to booking_confirmed", () => {
    expect(mapBackendEventType("BOOKED")).toBe("booking_confirmed");
  });

  it("maps GATE_IN to gate_in", () => {
    expect(mapBackendEventType("GATE_IN")).toBe("gate_in");
  });

  it("maps LOADED to loaded", () => {
    expect(mapBackendEventType("LOADED")).toBe("loaded");
  });

  it("maps DEPARTED to departed", () => {
    expect(mapBackendEventType("DEPARTED")).toBe("departed");
  });

  it("maps IN_TRANSIT to departed", () => {
    expect(mapBackendEventType("IN_TRANSIT")).toBe("departed");
  });

  it("maps TRANSSHIPMENT to transshipment", () => {
    expect(mapBackendEventType("TRANSSHIPMENT")).toBe("transshipment");
  });

  it("maps ARRIVED to arrived", () => {
    expect(mapBackendEventType("ARRIVED")).toBe("arrived");
  });

  it("maps DISCHARGED to discharged", () => {
    expect(mapBackendEventType("DISCHARGED")).toBe("discharged");
  });

  it("maps GATE_OUT to gate_out", () => {
    expect(mapBackendEventType("GATE_OUT")).toBe("gate_out");
  });

  it("maps DELIVERED to delivered", () => {
    expect(mapBackendEventType("DELIVERED")).toBe("delivered");
  });

  it("maps OTHER to unknown", () => {
    expect(mapBackendEventType("OTHER")).toBe("unknown");
  });

  it("maps unrecognized values to unknown", () => {
    expect(mapBackendEventType("SOMETHING_NEW")).toBe("unknown");
    expect(mapBackendEventType("")).toBe("unknown");
  });
});

describe("rowToContainerEvent", () => {
  it("converts a Supabase row to ContainerEvent", () => {
    const row: ContainerEventRow = {
      id: "e1",
      shipment_id: "s1",
      organization_id: "org-1",
      event_status: "DEPARTED",
      event_time: "2026-02-12T06:00:00Z",
      location_code: "NGAPP",
      location_name: "Apapa",
      vessel_name: "MV Atlantic",
      voyage_number: "V042",
      description: "Vessel departed",
      source: "jsoncargo",
      created_at: "2026-02-12T06:01:00Z",
    };

    const event = rowToContainerEvent(row);
    expect(event).toEqual({
      id: "e1",
      event_type: "departed",
      timestamp: "2026-02-12T06:00:00Z",
      location_name: "Apapa",
      location_code: "NGAPP",
      vessel_name: "MV Atlantic",
      voyage_number: "V042",
      description: "Vessel departed",
    });
  });

  it("handles null fields", () => {
    const row: ContainerEventRow = {
      id: "e2",
      shipment_id: "s1",
      organization_id: "org-1",
      event_status: "BOOKED",
      event_time: "2026-02-01T00:00:00Z",
      location_code: null,
      location_name: null,
      vessel_name: null,
      voyage_number: null,
      description: null,
      source: null,
      created_at: "2026-02-01T00:00:00Z",
    };

    const event = rowToContainerEvent(row);
    expect(event.event_type).toBe("booking_confirmed");
    expect(event.location_name).toBeNull();
    expect(event.vessel_name).toBeNull();
  });
});
