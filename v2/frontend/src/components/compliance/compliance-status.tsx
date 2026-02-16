import { CheckCircle, XCircle, Clock, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  DOCUMENT_TYPE_LABELS,
  getComplianceProgress,
  isDocumentComplete,
  type DocumentSummary,
  type DocumentType,
} from "@/lib/api/document-types";

interface ComplianceStatusProps {
  summary: DocumentSummary;
}

export function ComplianceStatus({ summary }: ComplianceStatusProps) {
  const progress = getComplianceProgress(summary);
  const complete = isDocumentComplete(summary);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          Document Status
          {complete ? (
            <Badge className="bg-success/10 text-success border-success/20 gap-1" variant="outline">
              <CheckCircle className="h-3 w-3" />
              Complete
            </Badge>
          ) : (
            <Badge className="bg-destructive/10 text-destructive border-destructive/20 gap-1" variant="outline">
              <AlertTriangle className="h-3 w-3" />
              Incomplete
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              {summary.total_present} / {summary.total_required} documents
            </span>
            <span className="font-medium">{progress}%</span>
          </div>
          <Progress
            value={progress}
            className={complete ? "[&>div]:bg-success" : "[&>div]:bg-warning"}
          />
        </div>

        {summary.missing_types.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium">
              <XCircle className="text-destructive h-3.5 w-3.5" />
              Missing
            </h4>
            <ul className="space-y-1">
              {summary.missing_types.map((type: DocumentType) => (
                <li
                  key={type}
                  className="text-muted-foreground text-xs"
                >
                  {DOCUMENT_TYPE_LABELS[type]}
                </li>
              ))}
            </ul>
          </div>
        )}

        {summary.pending_validation.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium">
              <Clock className="text-warning h-3.5 w-3.5" />
              Pending Validation
            </h4>
            <ul className="space-y-1">
              {summary.pending_validation.map((type: DocumentType) => (
                <li
                  key={type}
                  className="text-muted-foreground text-xs"
                >
                  {DOCUMENT_TYPE_LABELS[type]}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
