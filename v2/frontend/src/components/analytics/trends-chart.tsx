"use client";

import { useState } from "react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  formatTrendDate,
  type ShipmentTrendPoint,
  type TrendGroupBy,
} from "@/lib/api/analytics-types";

interface TrendsChartProps {
  data: ShipmentTrendPoint[];
  groupBy: TrendGroupBy;
  onGroupByChange: (groupBy: TrendGroupBy) => void;
}

const GROUP_OPTIONS: { value: TrendGroupBy; label: string }[] = [
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
];

export function TrendsChart({ data, groupBy, onGroupByChange }: TrendsChartProps) {
  const chartData = data.map((item) => ({
    date: formatTrendDate(item.date, groupBy),
    count: item.count,
  }));

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-lg">
          <TrendingUp className="h-5 w-5" />
          Shipments Over Time
        </CardTitle>
        <div className="flex gap-1">
          {GROUP_OPTIONS.map((opt) => (
            <Button
              key={opt.value}
              variant={groupBy === opt.value ? "default" : "outline"}
              size="sm"
              onClick={() => onGroupByChange(opt.value)}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="text-muted-foreground flex h-[250px] items-center justify-center">
            No shipment data available for the selected period
          </div>
        ) : (
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={{ fill: "hsl(var(--primary))", r: 4 }}
                  name="Shipments"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
