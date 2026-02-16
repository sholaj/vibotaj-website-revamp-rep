import { Shield, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type {
  ComplianceDecision,
  ComplianceSummaryCount,
  ComplianceOverride,
} from "@/lib/api/compliance-types";
import { DECISION_COLORS, DECISION_LABELS } from "@/lib/api/compliance-types";

interface ShipmentComplianceCardProps {
  decision: ComplianceDecision;
  summary: ComplianceSummaryCount;
  override: ComplianceOverride | null;
  onOverride?: () => void;
  canOverride?: boolean;
}

function DecisionIcon({ decision }: { decision: ComplianceDecision }) {
  switch (decision) {
    case "APPROVE":
      return <ShieldCheck className="h-5 w-5 text-success" />;
    case "HOLD":
      return <ShieldAlert className="h-5 w-5 text-warning" />;
    case "REJECT":
      return <ShieldX className="h-5 w-5 text-destructive" />;
    default:
      return <Shield className="h-5 w-5 text-muted-foreground" />;
  }
}

export function ShipmentComplianceCard({
  decision,
  summary,
  override,
  onOverride,
  canOverride = false,
}: ShipmentComplianceCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <DecisionIcon decision={decision} />
            Compliance
          </div>
          <Badge
            variant="outline"
            className={cn(DECISION_COLORS[decision])}
            data-testid="decision-badge"
          >
            {DECISION_LABELS[decision]}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary counts */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-muted-foreground">Total Rules</p>
            <p className="text-lg font-semibold" data-testid="total-rules">
              {summary.total_rules}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Passed</p>
            <p className="text-lg font-semibold text-success" data-testid="passed-count">
              {summary.passed}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Failed</p>
            <p className="text-lg font-semibold text-destructive" data-testid="failed-count">
              {summary.failed}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Warnings</p>
            <p className="text-lg font-semibold text-warning" data-testid="warning-count">
              {summary.warnings}
            </p>
          </div>
        </div>

        {/* Override info */}
        {override && (
          <div className="rounded-md border border-warning/20 bg-warning/5 p-3">
            <p className="text-xs font-medium text-warning">Compliance Override Active</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {override.reason}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              By: {override.overridden_by}
            </p>
          </div>
        )}

        {/* Override button */}
        {canOverride && !override && decision !== "APPROVE" && onOverride && (
          <button
            onClick={onOverride}
            className="w-full rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-xs font-medium text-warning hover:bg-warning/20 transition-colors"
          >
            Override Compliance
          </button>
        )}
      </CardContent>
    </Card>
  );
}
