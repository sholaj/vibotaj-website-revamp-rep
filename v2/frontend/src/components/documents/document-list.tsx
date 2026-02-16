"use client";

import { Download, Upload, XCircle, Clock, FileSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/domain/status-badge";
import type { DocumentStatus as BadgeDocumentStatus } from "@/components/domain/status-badge";
import { cn } from "@/lib/utils";
import {
  DOCUMENT_TYPE_LABELS,
  type Document,
  type DocumentType,
} from "@/lib/api/document-types";
import {
  PARSE_STATUS_LABELS,
  PARSE_STATUS_COLORS,
} from "@/lib/api/bol-types";
import type { BolParseStatus } from "@/lib/api/bol-types";

interface DocumentListProps {
  documents: Document[];
  missingTypes: DocumentType[];
  bolParseStatuses?: Record<string, BolParseStatus>;
  onUpload: () => void;
  onSelect: (doc: Document) => void;
  onDownload: (doc: Document) => void;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function DocumentList({
  documents,
  missingTypes,
  bolParseStatuses,
  onUpload,
  onSelect,
  onDownload,
}: DocumentListProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">
            Documents ({documents.length})
          </CardTitle>
          <Button size="sm" onClick={onUpload}>
            <Upload className="mr-2 h-4 w-4" />
            Upload
          </Button>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((doc) => {
                const bolStatus =
                  doc.document_type === "bill_of_lading"
                    ? bolParseStatuses?.[doc.id]
                    : undefined;
                return (
                <TableRow
                  key={doc.id}
                  className="cursor-pointer"
                  onClick={() => onSelect(doc)}
                >
                  <TableCell className="font-medium">
                    <span className="flex items-center gap-2">
                      {DOCUMENT_TYPE_LABELS[doc.document_type]}
                      {bolStatus && (
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-xs",
                            PARSE_STATUS_COLORS[bolStatus],
                          )}
                        >
                          <FileSearch className="mr-1 h-3 w-3" />
                          {PARSE_STATUS_LABELS[bolStatus]}
                        </Badge>
                      )}
                    </span>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {doc.reference_number ?? "—"}
                  </TableCell>
                  <TableCell>
                    <StatusBadge
                      variant="document"
                      status={doc.status as BadgeDocumentStatus}
                    />
                  </TableCell>
                  <TableCell>{formatDate(doc.issue_date)}</TableCell>
                  <TableCell>
                    {doc.file_path && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDownload(doc);
                        }}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
                );
              })}
              {documents.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="text-muted-foreground py-8 text-center"
                  >
                    No documents uploaded yet
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {missingTypes.length > 0 && (
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2 text-base">
              <XCircle className="h-4 w-4" />
              Missing Documents ({missingTypes.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {missingTypes.map((type) => (
                <li
                  key={type}
                  className="text-muted-foreground flex items-center gap-2 text-sm"
                >
                  <Clock className="h-3.5 w-3.5 text-destructive" />
                  {DOCUMENT_TYPE_LABELS[type]}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
