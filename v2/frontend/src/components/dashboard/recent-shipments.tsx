import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/domain/status-badge";
import type { Shipment } from "@/lib/api/shipment-types";
import type { ShipmentStatus as BadgeShipmentStatus } from "@/components/domain/status-badge";

interface RecentShipmentsProps {
  shipments: Shipment[];
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function RecentShipments({ shipments }: RecentShipmentsProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Recent Shipments</CardTitle>
        <Link
          href="/shipments"
          className="text-primary text-sm font-medium hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Reference</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Destination</TableHead>
              <TableHead>ETA</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {shipments.map((s) => (
              <TableRow key={s.id}>
                <TableCell className="font-medium">
                  <Link
                    href={`/shipments/${s.id}`}
                    className="hover:text-primary hover:underline"
                  >
                    {s.reference}
                  </Link>
                </TableCell>
                <TableCell>
                  <StatusBadge
                    variant="shipment"
                    status={s.status as BadgeShipmentStatus}
                  />
                </TableCell>
                <TableCell>
                  {s.pod_name ?? s.pod_code ?? "—"}
                </TableCell>
                <TableCell>{formatDate(s.eta)}</TableCell>
              </TableRow>
            ))}
            {shipments.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="text-muted-foreground py-8 text-center"
                >
                  No shipments yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
