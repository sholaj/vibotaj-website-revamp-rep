"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { IntegrationLog } from "@/lib/api/integration-types";
import { METHOD_LABELS } from "@/lib/api/integration-types";

interface IntegrationLogTableProps {
  logs: IntegrationLog[];
}

const STATUS_BADGE_VARIANT: Record<
  string,
  "default" | "destructive" | "secondary" | "outline"
> = {
  success: "default",
  error: "destructive",
  timeout: "secondary",
};

export function IntegrationLogTable({ logs }: IntegrationLogTableProps) {
  if (logs.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-6">
        No recent activity
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Method</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Provider</TableHead>
          <TableHead className="text-right">Time (ms)</TableHead>
          <TableHead>Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {logs.map((log) => (
          <TableRow key={log.id}>
            <TableCell className="text-sm">
              {METHOD_LABELS[log.method] ?? log.method}
            </TableCell>
            <TableCell>
              <Badge variant={STATUS_BADGE_VARIANT[log.status] ?? "outline"}>
                {log.status}
              </Badge>
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {log.provider}
            </TableCell>
            <TableCell className="text-right text-sm">
              {log.response_time_ms ?? "—"}
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {new Date(log.created_at).toLocaleString()}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
