"use client";

import { type ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import { StatusBadge } from "@/components/domain/status-badge";
import { DataTableColumnHeader } from "@/components/domain/data-table-column-header";
import type { Shipment } from "@/lib/api/shipment-types";
import type { ShipmentStatus as BadgeShipmentStatus } from "@/components/domain/status-badge";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export const shipmentColumns: ColumnDef<Shipment>[] = [
  {
    accessorKey: "reference",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Reference" />
    ),
    cell: ({ row }) => (
      <Link
        href={`/shipments/${row.original.id}`}
        className="text-primary font-medium hover:underline"
      >
        {row.getValue("reference")}
      </Link>
    ),
  },
  {
    accessorKey: "status",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Status" />
    ),
    cell: ({ row }) => (
      <StatusBadge
        variant="shipment"
        status={row.getValue("status") as BadgeShipmentStatus}
      />
    ),
    filterFn: (row, _id, value: string[]) => {
      return value.includes(row.getValue("status"));
    },
  },
  {
    accessorKey: "container_number",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Container" />
    ),
    cell: ({ row }) => (
      <span className="font-mono text-sm">
        {row.getValue("container_number") ?? "—"}
      </span>
    ),
  },
  {
    accessorKey: "pod_name",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Destination" />
    ),
    cell: ({ row }) =>
      row.original.pod_name ?? row.original.pod_code ?? "—",
  },
  {
    accessorKey: "eta",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="ETA" />
    ),
    cell: ({ row }) => formatDate(row.getValue("eta")),
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Created" />
    ),
    cell: ({ row }) => formatDate(row.getValue("created_at")),
  },
];
