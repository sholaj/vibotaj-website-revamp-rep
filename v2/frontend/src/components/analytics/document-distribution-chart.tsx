"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { FileText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DOC_STATUS_LABELS,
  DOC_STATUS_COLORS,
  type DocumentDistributionItem,
} from "@/lib/api/analytics-types";

interface DocumentDistributionChartProps {
  data: DocumentDistributionItem[];
}

export function DocumentDistributionChart({ data }: DocumentDistributionChartProps) {
  const chartData = data
    .filter((item) => item.count > 0)
    .map((item) => ({
      name: DOC_STATUS_LABELS[item.status] ?? item.status,
      value: item.count,
      color: DOC_STATUS_COLORS[item.status] ?? "hsl(var(--muted-foreground))",
    }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <FileText className="h-5 w-5" />
          Document Status Distribution
        </CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="text-muted-foreground flex h-[250px] items-center justify-center">
            No document data available
          </div>
        ) : (
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
