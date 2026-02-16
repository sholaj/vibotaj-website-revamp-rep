import { Package, FileText, Ship, CheckCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { DashboardStats } from "@/lib/api/shipment-types";

interface KpiCardsProps {
  stats: DashboardStats;
}

const kpis = [
  {
    key: "totalShipments" as const,
    label: "Total Shipments",
    icon: Package,
    color: "text-info",
    bgColor: "bg-info/10",
  },
  {
    key: "docsPending" as const,
    label: "Docs Pending",
    icon: FileText,
    color: "text-warning",
    bgColor: "bg-warning/10",
  },
  {
    key: "inTransit" as const,
    label: "In Transit",
    icon: Ship,
    color: "text-info",
    bgColor: "bg-info/10",
  },
  {
    key: "complianceRate" as const,
    label: "Compliance Rate",
    icon: CheckCircle,
    color: "text-success",
    bgColor: "bg-success/10",
    suffix: "%",
  },
] as const;

export function KpiCards({ stats }: KpiCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map((kpi) => {
        const Icon = kpi.icon;
        const value = stats[kpi.key];
        return (
          <Card key={kpi.key}>
            <CardContent className="flex items-center gap-4 p-6">
              <div className={`rounded-lg p-2.5 ${kpi.bgColor}`}>
                <Icon className={`h-5 w-5 ${kpi.color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {value}
                  {"suffix" in kpi ? kpi.suffix : ""}
                </p>
                <p className="text-muted-foreground text-sm">{kpi.label}</p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
