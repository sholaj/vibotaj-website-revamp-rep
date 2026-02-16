import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PageHeader } from "../page-header";

describe("PageHeader", () => {
  it("renders title", () => {
    render(<PageHeader title="Shipments" />);
    expect(
      screen.getByRole("heading", { name: "Shipments" }),
    ).toBeInTheDocument();
  });

  it("renders description when provided", () => {
    render(
      <PageHeader title="Shipments" description="Manage your shipments" />,
    );
    expect(screen.getByText("Manage your shipments")).toBeInTheDocument();
  });

  it("does not render description when not provided", () => {
    const { container } = render(<PageHeader title="Shipments" />);
    const paragraphs = container.querySelectorAll("p");
    expect(paragraphs).toHaveLength(0);
  });

  it("renders breadcrumbs when provided", () => {
    render(
      <PageHeader
        title="Shipment Detail"
        breadcrumbs={[
          { label: "Shipments", href: "/shipments" },
          { label: "SHP-001" },
        ]}
      />,
    );
    expect(screen.getByText("Shipments")).toBeInTheDocument();
    expect(screen.getByText("SHP-001")).toBeInTheDocument();
  });

  it("renders actions slot when provided", () => {
    render(
      <PageHeader
        title="Shipments"
        actions={<button>Create Shipment</button>}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Create Shipment" }),
    ).toBeInTheDocument();
  });
});
