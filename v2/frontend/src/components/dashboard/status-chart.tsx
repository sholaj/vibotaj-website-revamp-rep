"use client";

import {
  Bar,
  BarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ShipmentStatus } from "@/lib/api/shipment-types";

const STATUS_COLORS: Record<ShipmentStatus, string> = {
  draft: "hsl(var(--info))",
  docs_pending: "hsl(var(--warning))",
  docs_complete: "hsl(var(--success))",
  in_transit: "hsl(var(--info))",
  arrived: "hsl(var(--success))",
  customs: "hsl(var(--warning))",
  delivered: "hsl(var(--success))",
  archived: "hsl(var(--muted-foreground))",
};

const STATUS_LABELS: Record<ShipmentStatus, string> = {
  draft: "Draft",
  docs_pending: "Docs Pending",
  docs_complete: "Docs Complete",
  in_transit: "In Transit",
  arrived: "Arrived",
  customs: "Customs",
  delivered: "Delivered",
  archived: "Archived",
};

interface StatusChartProps {
  data: { status: ShipmentStatus; count: number }[];
}

export function StatusChart({ data }: StatusChartProps) {
  const chartData = data.map((d) => ({
    name: STATUS_LABELS[d.status],
    value: d.count,
    status: d.status,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Shipment Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <XAxis type="number" allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="name"
                width={100}
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map((entry) => (
                  <Cell
                    key={entry.status}
                    fill={STATUS_COLORS[entry.status]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
