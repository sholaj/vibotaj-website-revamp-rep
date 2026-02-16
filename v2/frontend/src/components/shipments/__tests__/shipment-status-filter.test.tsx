import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ShipmentStatusFilter } from "../shipment-status-filter";

describe("ShipmentStatusFilter", () => {
  it("renders all status options", () => {
    render(<ShipmentStatusFilter value="all" onChange={vi.fn()} />);
    expect(screen.getByText("All")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Docs Pending")).toBeInTheDocument();
    expect(screen.getByText("Docs Complete")).toBeInTheDocument();
    expect(screen.getByText("In Transit")).toBeInTheDocument();
    expect(screen.getByText("Arrived")).toBeInTheDocument();
    expect(screen.getByText("Customs")).toBeInTheDocument();
    expect(screen.getByText("Delivered")).toBeInTheDocument();
    expect(screen.getByText("Archived")).toBeInTheDocument();
  });

  it("calls onChange when a status is clicked", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ShipmentStatusFilter value="all" onChange={onChange} />);

    await user.click(screen.getByText("In Transit"));
    expect(onChange).toHaveBeenCalledWith("in_transit");
  });

  it("highlights the active status", () => {
    render(<ShipmentStatusFilter value="in_transit" onChange={vi.fn()} />);
    const inTransitButton = screen.getByText("In Transit").closest("button");
    // Default variant has different classes than outline
    expect(inTransitButton).not.toHaveClass("border-input");
  });

  it("displays counts when provided", () => {
    render(
      <ShipmentStatusFilter
        value="all"
        onChange={vi.fn()}
        counts={{ all: 42, in_transit: 12, draft: 5 }}
      />,
    );
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });
});
