import { Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressRing } from "@/components/domain/progress-ring";
import type { ComplianceMetrics } from "@/lib/api/analytics-types";

interface CompliancePanelProps {
  metrics: ComplianceMetrics;
}

export function CompliancePanel({ metrics }: CompliancePanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Shield className="h-5 w-5" />
          Compliance Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-around py-4">
          <ProgressRing
            value={metrics.compliant_rate}
            label="Overall Compliance"
            color={
              metrics.compliant_rate >= 80
                ? "hsl(var(--success))"
                : "hsl(var(--warning))"
            }
          />
          <ProgressRing
            value={metrics.eudr_coverage}
            label="EUDR Coverage"
            color="hsl(var(--info))"
          />
        </div>
        <div className="border-border mt-4 space-y-2 border-t pt-4">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Shipments needing attention</span>
            <span className="font-medium">
              {metrics.shipments_needing_attention}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Failed documents</span>
            <span className="font-medium">{metrics.failed_documents}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
