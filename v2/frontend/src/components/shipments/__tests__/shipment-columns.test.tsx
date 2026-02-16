import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { flexRender } from "@tanstack/react-table";
import { shipmentColumns } from "../shipment-columns";
import type { Shipment } from "@/lib/api/shipment-types";

const mockShipments: Shipment[] = [
  {
    id: "s1",
    reference: "SH-001",
    container_number: "ABCU1234567",
    status: "in_transit",
    product_type: "horn",
    vessel_name: "MV Test",
    voyage_number: "V001",
    pol_code: "NGAPP",
    pol_name: "Apapa",
    pod_code: "BEANR",
    pod_name: "Antwerp",
    eta: "2026-03-01T00:00:00Z",
    etd: "2026-02-10T00:00:00Z",
    created_at: "2026-01-15T00:00:00Z",
    updated_at: "2026-01-15T00:00:00Z",
    organization_id: "org-1",
  },
];

function TestTable({ data }: { data: Shipment[] }) {
  const table = useReactTable({
    data,
    columns: shipmentColumns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map((headerGroup) => (
          <TableRow key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <TableHead key={header.id}>
                {header.isPlaceholder
                  ? null
                  : flexRender(
                      header.column.columnDef.header,
                      header.getContext(),
                    )}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.map((row) => (
          <TableRow key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <TableCell key={cell.id}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

describe("shipmentColumns", () => {
  it("renders reference as a link", () => {
    render(<TestTable data={mockShipments} />);
    const link = screen.getByText("SH-001");
    expect(link).toBeInTheDocument();
    expect(link.closest("a")).toHaveAttribute("href", "/shipments/s1");
  });

  it("renders container number in monospace", () => {
    render(<TestTable data={mockShipments} />);
    const container = screen.getByText("ABCU1234567");
    expect(container).toHaveClass("font-mono");
  });

  it("renders destination from pod_name", () => {
    render(<TestTable data={mockShipments} />);
    expect(screen.getByText("Antwerp")).toBeInTheDocument();
  });

  it("renders formatted ETA", () => {
    render(<TestTable data={mockShipments} />);
    expect(screen.getByText("1 Mar 2026")).toBeInTheDocument();
  });

  it("renders formatted created date", () => {
    render(<TestTable data={mockShipments} />);
    expect(screen.getByText("15 Jan 2026")).toBeInTheDocument();
  });

  it("renders all column headers", () => {
    render(<TestTable data={mockShipments} />);
    expect(screen.getByText("Reference")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Container")).toBeInTheDocument();
    expect(screen.getByText("Destination")).toBeInTheDocument();
    expect(screen.getByText("ETA")).toBeInTheDocument();
    expect(screen.getByText("Created")).toBeInTheDocument();
  });
});
