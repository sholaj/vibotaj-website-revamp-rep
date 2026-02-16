"use client";

import {
  ArrowRight,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  SYNC_FIELD_LABELS,
  countUpdates,
  countPlaceholders,
} from "@/lib/api/bol-types";
import type {
  BolSyncPreviewResponse,
  SyncChange,
  CrossValidationIssue,
} from "@/lib/api/bol-types";

interface BolSyncPreviewProps {
  preview: BolSyncPreviewResponse;
  crossValidation?: CrossValidationIssue[];
  onApplySync?: () => void;
  isSyncing?: boolean;
  syncSuccess?: boolean;
}

function ChangeRow({ change }: { change: SyncChange }) {
  const label = SYNC_FIELD_LABELS[change.field] ?? change.field;

  return (
    <div
      className={cn(
        "flex items-center justify-between rounded-md border p-3",
        change.will_update && "border-blue-200 bg-blue-50/50",
      )}
      data-testid={`sync-change-${change.field}`}
    >
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{label}</span>
          {change.is_placeholder && (
            <Badge
              variant="outline"
              className="border-amber-200 bg-amber-50 text-xs text-amber-700"
            >
              Placeholder
            </Badge>
          )}
          {change.will_update && (
            <Badge
              variant="outline"
              className="border-blue-200 bg-blue-50 text-xs text-blue-700"
            >
              Will update
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground truncate">
            {change.current ?? <span className="italic">Empty</span>}
          </span>
          <ArrowRight className="h-3 w-3 shrink-0 text-blue-500" />
          <span className="truncate font-medium">{change.new_value}</span>
        </div>
      </div>
    </div>
  );
}

function ValidationIssueRow({ issue }: { issue: CrossValidationIssue }) {
  const Icon = issue.severity === "ERROR" ? AlertTriangle : AlertTriangle;

  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-md border p-3",
        issue.severity === "ERROR" && "border-red-200 bg-red-50/50",
        issue.severity === "WARNING" && "border-amber-200 bg-amber-50/50",
      )}
      data-testid={`validation-issue-${issue.rule_id}`}
    >
      <Icon
        className={cn(
          "mt-0.5 h-4 w-4 shrink-0",
          issue.severity === "ERROR" && "text-red-600",
          issue.severity === "WARNING" && "text-amber-600",
        )}
      />
      <div>
        <span className="text-sm font-medium">{issue.rule_name}</span>
        <p className="text-muted-foreground text-xs">{issue.message}</p>
      </div>
    </div>
  );
}

export function BolSyncPreview({
  preview,
  crossValidation,
  onApplySync,
  isSyncing,
  syncSuccess,
}: BolSyncPreviewProps) {
  const updates = countUpdates(preview.changes);
  const placeholders = countPlaceholders(preview.changes);
  const hasIssues = crossValidation && crossValidation.length > 0;

  return (
    <Card data-testid="bol-sync-preview">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="text-base">Sync Preview</CardTitle>
          {preview.shipment_reference && (
            <p className="text-muted-foreground mt-0.5 text-xs">
              Shipment: {preview.shipment_reference}
            </p>
          )}
        </div>
        {updates > 0 && (
          <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700">
            {updates} update{updates !== 1 ? "s" : ""}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        {preview.changes.length > 0 ? (
          <div className="space-y-4">
            {/* Auto-synced notice */}
            {preview.auto_synced && (
              <div className="rounded-md border border-green-200 bg-green-50 p-2 text-center text-xs text-green-700">
                <CheckCircle className="mr-1 inline h-3 w-3" />
                These fields were auto-synced from the parsed BoL
              </div>
            )}

            {/* Placeholder summary */}
            {placeholders > 0 && (
              <p className="text-muted-foreground text-xs">
                {placeholders} placeholder{placeholders !== 1 ? "s" : ""} will be
                replaced with parsed BoL data.
              </p>
            )}

            {/* Change list */}
            <div className="space-y-2">
              {preview.changes.map((change) => (
                <ChangeRow key={change.field} change={change} />
              ))}
            </div>

            {/* Cross-validation issues */}
            {hasIssues && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Cross-Document Validation</h4>
                {crossValidation.map((issue) => (
                  <ValidationIssueRow key={issue.rule_id} issue={issue} />
                ))}
              </div>
            )}

            {/* Apply button */}
            {onApplySync && !preview.auto_synced && updates > 0 && (
              <div className="pt-2">
                {syncSuccess ? (
                  <div className="flex items-center gap-2 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700">
                    <CheckCircle className="h-4 w-4" />
                    Sync applied successfully
                  </div>
                ) : (
                  <Button
                    onClick={onApplySync}
                    disabled={isSyncing}
                    className="w-full"
                    size="sm"
                  >
                    <RefreshCw className={cn("mr-2 h-4 w-4", isSyncing && "animate-spin")} />
                    {isSyncing ? "Syncing..." : `Apply ${updates} Update${updates !== 1 ? "s" : ""}`}
                  </Button>
                )}
              </div>
            )}
          </div>
        ) : (
          <p className="text-muted-foreground py-4 text-center text-sm">
            No changes to sync
          </p>
        )}
      </CardContent>
    </Card>
  );
}
