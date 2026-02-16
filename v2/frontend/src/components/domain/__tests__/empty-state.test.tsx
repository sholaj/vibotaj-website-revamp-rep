import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FileText } from "lucide-react";
import { EmptyState } from "../empty-state";

describe("EmptyState", () => {
  it("renders title", () => {
    render(<EmptyState title="No shipments found" />);
    expect(screen.getByText("No shipments found")).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(
      <EmptyState
        title="No shipments found"
        description="Create a shipment to get started."
      />,
    );
    expect(
      screen.getByText("Create a shipment to get started."),
    ).toBeInTheDocument();
  });

  it("renders action when provided", () => {
    render(
      <EmptyState
        title="No documents"
        action={<button>Upload Document</button>}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Upload Document" }),
    ).toBeInTheDocument();
  });

  it("accepts custom icon", () => {
    render(<EmptyState icon={FileText} title="No documents" />);
    expect(screen.getByText("No documents")).toBeInTheDocument();
  });
});
