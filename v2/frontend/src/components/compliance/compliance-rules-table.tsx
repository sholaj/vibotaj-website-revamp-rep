import { CheckCircle, XCircle, AlertTriangle, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { RuleResult, RuleSeverity } from "@/lib/api/compliance-types";
import { SEVERITY_COLORS, SEVERITY_LABELS } from "@/lib/api/compliance-types";

interface ComplianceRulesTableProps {
  results: RuleResult[];
  onOverride?: (ruleId: string) => void;
}

function SeverityBadge({ severity }: { severity: RuleSeverity }) {
  return (
    <Badge variant="outline" className={cn("gap-0.5", SEVERITY_COLORS[severity])}>
      {SEVERITY_LABELS[severity]}
    </Badge>
  );
}

function StatusIcon({ passed, isOverridden }: { passed: boolean; isOverridden?: boolean }) {
  if (isOverridden) {
    return <AlertTriangle className="h-4 w-4 text-warning" />;
  }
  if (passed) {
    return <CheckCircle className="h-4 w-4 text-success" />;
  }
  return <XCircle className="h-4 w-4 text-destructive" />;
}

export function ComplianceRulesTable({ results, onOverride }: ComplianceRulesTableProps) {
  if (results.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Compliance Rules</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Info className="h-4 w-4" />
            No compliance rules have been evaluated yet.
          </div>
        </CardContent>
      </Card>
    );
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed && !r.is_overridden).length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          Compliance Rules
          <span className="text-sm font-normal text-muted-foreground">
            {passed} passed, {failed} failed
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">Status</TableHead>
              <TableHead>Rule</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Message</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {results.map((rule) => (
              <TableRow key={rule.rule_id} data-testid={`rule-${rule.rule_id}`}>
                <TableCell>
                  <StatusIcon passed={rule.passed} isOverridden={rule.is_overridden} />
                </TableCell>
                <TableCell>
                  <div>
                    <span className="font-medium">{rule.rule_name}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      {rule.rule_id}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <SeverityBadge severity={rule.severity} />
                </TableCell>
                <TableCell className="max-w-xs truncate text-sm text-muted-foreground">
                  {rule.is_overridden ? (
                    <span className="italic">Overridden: {rule.override_reason}</span>
                  ) : (
                    rule.message ?? "\u2014"
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
