import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { type ColumnDef } from "@tanstack/react-table";
import { DataTable } from "../data-table";

interface TestRow {
  id: string;
  name: string;
  status: string;
}

const columns: ColumnDef<TestRow>[] = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "status", header: "Status" },
];

const testData: TestRow[] = [
  { id: "1", name: "Shipment A", status: "active" },
  { id: "2", name: "Shipment B", status: "draft" },
  { id: "3", name: "Shipment C", status: "active" },
];

describe("DataTable", () => {
  it("renders column headers", () => {
    render(<DataTable columns={columns} data={testData} />);
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("renders data rows", () => {
    render(<DataTable columns={columns} data={testData} />);
    expect(screen.getByText("Shipment A")).toBeInTheDocument();
    expect(screen.getByText("Shipment B")).toBeInTheDocument();
    expect(screen.getByText("Shipment C")).toBeInTheDocument();
  });

  it("shows empty state when no data", () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        emptyTitle="No shipments"
        emptyDescription="Create one to get started."
      />,
    );
    expect(screen.getByText("No shipments")).toBeInTheDocument();
    expect(screen.getByText("Create one to get started.")).toBeInTheDocument();
  });

  it("shows filter input when filterColumn is specified", () => {
    render(
      <DataTable
        columns={columns}
        data={testData}
        filterColumn="name"
        filterPlaceholder="Search shipments..."
      />,
    );
    expect(
      screen.getByPlaceholderText("Search shipments..."),
    ).toBeInTheDocument();
  });

  it("filters rows when typing in filter input", async () => {
    const user = userEvent.setup();
    render(
      <DataTable
        columns={columns}
        data={testData}
        filterColumn="name"
        filterPlaceholder="Search..."
      />,
    );

    await user.type(screen.getByPlaceholderText("Search..."), "Shipment A");

    expect(screen.getByText("Shipment A")).toBeInTheDocument();
    expect(screen.queryByText("Shipment B")).not.toBeInTheDocument();
    expect(screen.queryByText("Shipment C")).not.toBeInTheDocument();
  });

  it("renders pagination controls", () => {
    render(<DataTable columns={columns} data={testData} />);
    expect(screen.getByText(/row\(s\) selected/i)).toBeInTheDocument();
    expect(screen.getByText(/rows per page/i)).toBeInTheDocument();
  });
});
