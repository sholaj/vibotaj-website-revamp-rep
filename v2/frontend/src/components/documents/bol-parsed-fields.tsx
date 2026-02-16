"use client";

import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  FileSearch,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  PARSE_STATUS_LABELS,
  PARSE_STATUS_COLORS,
  BOL_FIELD_LABELS,
  formatConfidence,
  getConfidenceColor,
  getConfidenceLevel,
  getOrderedFieldKeys,
  isParsed,
} from "@/lib/api/bol-types";
import type {
  BolParsedResponse,
  BolField,
  BolComplianceResult,
} from "@/lib/api/bol-types";
import { DECISION_LABELS } from "@/lib/api/compliance-types";

interface BolParsedFieldsProps {
  data: BolParsedResponse;
  onReparse?: () => void;
  isReparsing?: boolean;
}

function ConfidenceIndicator({ confidence }: { confidence: number }) {
  const level = getConfidenceLevel(confidence);
  const Icon =
    level === "high"
      ? CheckCircle
      : level === "medium"
        ? AlertTriangle
        : XCircle;

  return (
    <span
      className={cn("flex items-center gap-1 text-xs", getConfidenceColor(confidence))}
      title={`Confidence: ${formatConfidence(confidence)}`}
    >
      <Icon className="h-3 w-3" />
      {formatConfidence(confidence)}
    </span>
  );
}

function FieldRow({ fieldKey, field }: { fieldKey: string; field: BolField }) {
  const label = BOL_FIELD_LABELS[fieldKey] ?? fieldKey;

  return (
    <div className="flex items-center justify-between py-2" data-testid={`bol-field-${fieldKey}`}>
      <div className="space-y-0.5">
        <span className="text-muted-foreground text-sm">{label}</span>
        <p className="text-sm font-medium">
          {field.value ?? <span className="text-muted-foreground italic">Not found</span>}
        </p>
      </div>
      <ConfidenceIndicator confidence={field.confidence} />
    </div>
  );
}

function ComplianceSummary({ compliance }: { compliance: BolComplianceResult }) {
  return (
    <div className="rounded-md border p-3" data-testid="bol-compliance-summary">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Compliance</span>
        <Badge
          variant="outline"
          className={cn(
            compliance.decision === "APPROVE" && "border-green-200 bg-green-50 text-green-700",
            compliance.decision === "HOLD" && "border-amber-200 bg-amber-50 text-amber-700",
            compliance.decision === "REJECT" && "border-red-200 bg-red-50 text-red-700",
          )}
        >
          {DECISION_LABELS[compliance.decision]}
        </Badge>
      </div>
      <p className="text-muted-foreground mt-1 text-xs">
        {compliance.rules_passed}/{compliance.rules_total} rules passed
        {compliance.rules_failed > 0 && (
          <span className="text-destructive ml-1">
            ({compliance.rules_failed} failed)
          </span>
        )}
      </p>
    </div>
  );
}

export function BolParsedFields({
  data,
  onReparse,
  isReparsing,
}: BolParsedFieldsProps) {
  const parsed = isParsed(data.parse_status);
  const fieldKeys = parsed ? getOrderedFieldKeys(data.fields) : [];

  return (
    <Card data-testid="bol-parsed-fields">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <FileSearch className="text-muted-foreground h-4 w-4" />
          <CardTitle className="text-base">BoL Parse Results</CardTitle>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className={cn(PARSE_STATUS_COLORS[data.parse_status])}
          >
            {PARSE_STATUS_LABELS[data.parse_status]}
          </Badge>
          {onReparse && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={onReparse}
              disabled={isReparsing}
              title="Re-parse"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", isReparsing && "animate-spin")} />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {parsed ? (
          <div className="space-y-1">
            {/* Overall confidence */}
            <div className="mb-3 flex items-center justify-between rounded-md border p-3">
              <span className="text-sm font-medium">Overall Confidence</span>
              <span
                className={cn(
                  "text-sm font-semibold",
                  getConfidenceColor(data.confidence_score),
                )}
              >
                {formatConfidence(data.confidence_score)}
              </span>
            </div>

            {/* Auto-sync badge */}
            {data.auto_synced && (
              <div className="mb-3 rounded-md border border-green-200 bg-green-50 p-2 text-center text-xs text-green-700">
                Auto-synced to shipment
              </div>
            )}

            {/* Field list */}
            <div className="divide-y">
              {fieldKeys.map((key) => {
                const field = data.fields[key];
                if (!field) return null;
                return <FieldRow key={key} fieldKey={key} field={field} />;
              })}
            </div>

            {/* Compliance summary */}
            {data.compliance && (
              <div className="mt-3">
                <ComplianceSummary compliance={data.compliance} />
              </div>
            )}
          </div>
        ) : data.parse_status === "pending" ? (
          <p className="text-muted-foreground py-4 text-center text-sm">
            Waiting for parse to complete...
          </p>
        ) : data.parse_status === "failed" ? (
          <div className="py-4 text-center">
            <p className="text-destructive mb-2 text-sm">
              Failed to extract data from this document.
            </p>
            {onReparse && (
              <Button
                variant="outline"
                size="sm"
                onClick={onReparse}
                disabled={isReparsing}
              >
                <RefreshCw className={cn("mr-2 h-3.5 w-3.5", isReparsing && "animate-spin")} />
                Try Again
              </Button>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
