import {
  FileArchive,
  Download,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  File,
  MapPin,
  Database,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type {
  AuditPackStatus,
  AuditPackContent,
} from "@/lib/api/audit-pack-types";
import {
  PACK_STATUS_LABELS,
  PACK_STATUS_COLORS,
  formatGeneratedAt,
} from "@/lib/api/audit-pack-types";

interface AuditPackCardProps {
  status: AuditPackStatus;
  generatedAt: string | null;
  documentCount: number;
  contents: AuditPackContent[];
  isOutdated: boolean;
  complianceDecision: string | null;
  onDownload?: () => void;
  onRegenerate?: () => void;
  isDownloading?: boolean;
  isRegenerating?: boolean;
}

function StatusIcon({ status }: { status: AuditPackStatus }) {
  switch (status) {
    case "ready":
      return <CheckCircle2 className="h-4 w-4 text-green-600" />;
    case "generating":
      return <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />;
    case "outdated":
      return <AlertCircle className="h-4 w-4 text-amber-600" />;
    case "none":
      return <Clock className="h-4 w-4 text-gray-400" />;
    default:
      return <FileArchive className="h-4 w-4 text-gray-400" />;
  }
}

function ContentIcon({ type }: { type: string }) {
  switch (type) {
    case "index":
      return <FileText className="h-3.5 w-3.5 text-muted-foreground" />;
    case "document":
      return <File className="h-3.5 w-3.5 text-muted-foreground" />;
    case "tracking":
      return <MapPin className="h-3.5 w-3.5 text-muted-foreground" />;
    case "metadata":
      return <Database className="h-3.5 w-3.5 text-muted-foreground" />;
    default:
      return <File className="h-3.5 w-3.5 text-muted-foreground" />;
  }
}

export function AuditPackCard({
  status,
  generatedAt,
  documentCount,
  contents,
  isOutdated,
  complianceDecision,
  onDownload,
  onRegenerate,
  isDownloading = false,
  isRegenerating = false,
}: AuditPackCardProps) {
  const isLoading = isDownloading || isRegenerating;

  return (
    <Card data-testid="audit-pack-card">
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            <FileArchive className="h-5 w-5" />
            Audit Pack
          </div>
          <Badge
            variant="outline"
            className={cn("text-xs", PACK_STATUS_COLORS[status])}
            data-testid="pack-status-badge"
          >
            <StatusIcon status={status} />
            <span className="ml-1">{PACK_STATUS_LABELS[status]}</span>
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Generation info */}
        <div className="text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Generated</span>
            <span data-testid="generated-at">
              {formatGeneratedAt(generatedAt)}
            </span>
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-muted-foreground">Documents</span>
            <span data-testid="document-count">{documentCount}</span>
          </div>
          {complianceDecision && (
            <div className="flex justify-between mt-1">
              <span className="text-muted-foreground">Compliance</span>
              <span data-testid="compliance-decision">
                {complianceDecision}
              </span>
            </div>
          )}
        </div>

        {/* Outdated warning */}
        {isOutdated && status !== "none" && (
          <div
            className="rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-700"
            data-testid="outdated-warning"
          >
            Documents have changed since last generation. Regenerate for latest
            version.
          </div>
        )}

        {/* Contents list */}
        {contents.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              Contents
            </p>
            <ul
              className="space-y-0.5 text-xs"
              data-testid="contents-list"
            >
              {contents.map((item) => (
                <li
                  key={item.name}
                  className="flex items-center gap-1.5"
                >
                  <ContentIcon type={item.type} />
                  <span className="truncate">{item.name}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2">
          <Button
            variant="default"
            size="sm"
            className="flex-1"
            onClick={onDownload}
            disabled={isLoading}
            data-testid="download-btn"
          >
            {isDownloading ? (
              <RefreshCw className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Download className="mr-1 h-3.5 w-3.5" />
            )}
            {isDownloading ? "Generating..." : "Download"}
          </Button>
          {(isOutdated || status === "none") && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRegenerate}
              disabled={isLoading}
              data-testid="regenerate-btn"
            >
              <RefreshCw
                className={cn(
                  "mr-1 h-3.5 w-3.5",
                  isRegenerating && "animate-spin",
                )}
              />
              {isRegenerating ? "Regenerating..." : "Regenerate"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
