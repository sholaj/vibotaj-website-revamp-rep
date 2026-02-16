import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DocumentStateStepper } from "../document-state-stepper";
import type { DocumentTransition } from "@/lib/api/compliance-types";

const mockTransitions: DocumentTransition[] = [
  {
    id: "t1",
    document_id: "doc1",
    from_state: "DRAFT",
    to_state: "UPLOADED",
    actor_id: "user1",
    reason: "File uploaded by user",
    metadata: {},
    created_at: "2026-02-15T09:00:00Z",
  },
  {
    id: "t2",
    document_id: "doc1",
    from_state: "UPLOADED",
    to_state: "VALIDATED",
    actor_id: "user2",
    reason: null,
    metadata: {},
    created_at: "2026-02-15T10:30:00Z",
  },
  {
    id: "t3",
    document_id: "doc1",
    from_state: "VALIDATED",
    to_state: "COMPLIANCE_OK",
    actor_id: "user2",
    reason: "All rules passed",
    metadata: {},
    created_at: "2026-02-15T11:00:00Z",
  },
];

describe("DocumentStateStepper", () => {
  it("renders empty state when no transitions", () => {
    render(<DocumentStateStepper transitions={[]} />);
    expect(
      screen.getByText("No state transitions recorded."),
    ).toBeInTheDocument();
  });

  it("renders transition count in header", () => {
    render(<DocumentStateStepper transitions={mockTransitions} />);
    expect(screen.getByText("State History (3)")).toBeInTheDocument();
  });

  it("renders state labels for each transition", () => {
    render(<DocumentStateStepper transitions={mockTransitions} />);
    expect(screen.getAllByText("Draft").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Uploaded").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Validated").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Compliance OK")).toBeInTheDocument();
  });

  it("renders reason text when provided", () => {
    render(<DocumentStateStepper transitions={mockTransitions} />);
    expect(screen.getByText("File uploaded by user")).toBeInTheDocument();
    expect(screen.getByText("All rules passed")).toBeInTheDocument();
  });

  it("renders data-testid for each transition", () => {
    render(<DocumentStateStepper transitions={mockTransitions} />);
    expect(screen.getByTestId("transition-0")).toBeInTheDocument();
    expect(screen.getByTestId("transition-1")).toBeInTheDocument();
    expect(screen.getByTestId("transition-2")).toBeInTheDocument();
  });

  it("renders timestamps", () => {
    render(<DocumentStateStepper transitions={mockTransitions} />);
    // Timestamps are formatted as locale strings; just check at least one time element exists
    const timeElements = document.querySelectorAll("time");
    expect(timeElements.length).toBe(3);
  });
});
