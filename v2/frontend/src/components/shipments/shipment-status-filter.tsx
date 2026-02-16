"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ShipmentStatus } from "@/lib/api/shipment-types";

const STATUSES: { value: ShipmentStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "draft", label: "Draft" },
  { value: "docs_pending", label: "Docs Pending" },
  { value: "docs_complete", label: "Docs Complete" },
  { value: "in_transit", label: "In Transit" },
  { value: "arrived", label: "Arrived" },
  { value: "customs", label: "Customs" },
  { value: "delivered", label: "Delivered" },
  { value: "archived", label: "Archived" },
];

interface ShipmentStatusFilterProps {
  value: ShipmentStatus | "all";
  onChange: (status: ShipmentStatus | "all") => void;
  counts?: Record<string, number>;
}

export function ShipmentStatusFilter({
  value,
  onChange,
  counts,
}: ShipmentStatusFilterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {STATUSES.map((s) => (
        <Button
          key={s.value}
          variant={value === s.value ? "default" : "outline"}
          size="sm"
          className={cn("h-8")}
          onClick={() => onChange(s.value)}
        >
          {s.label}
          {counts?.[s.value] !== undefined && (
            <Badge
              variant="secondary"
              className="ml-1.5 min-w-[1.25rem] px-1"
            >
              {counts[s.value]}
            </Badge>
          )}
        </Button>
      ))}
    </div>
  );
}
