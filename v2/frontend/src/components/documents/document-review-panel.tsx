"use client";

import { useState } from "react";
import { Download, Trash2, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { StatusBadge } from "@/components/domain/status-badge";
import { ConfirmDialog } from "@/components/domain/confirm-dialog";
import type { DocumentStatus as BadgeDocumentStatus } from "@/components/domain/status-badge";
import { DOCUMENT_TYPE_LABELS, type Document } from "@/lib/api/document-types";
import { useReclassifyDocument } from "@/lib/api/classification";
import {
  METHOD_LABELS,
  METHOD_COLORS,
  formatClassificationConfidence,
  getDocTypeLabel,
  type ClassificationMethod,
} from "@/lib/api/classification-types";

interface DocumentReviewPanelProps {
  document: Document | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApprove: (documentId: string, notes?: string) => void;
  onReject: (documentId: string, reason: string) => void;
  onDelete: (documentId: string, reason: string) => void;
  onDownload: (doc: Document) => void;
  isApproving?: boolean;
  isRejecting?: boolean;
  isDeleting?: boolean;
  canApprove?: boolean;
  classificationMethod?: ClassificationMethod | null;
  classificationConfidence?: number | null;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function DocumentReviewPanel({
  document: doc,
  open,
  onOpenChange,
  onApprove,
  onReject,
  onDelete,
  onDownload,
  isApproving,
  isRejecting,
  isDeleting,
  canApprove = false,
  classificationMethod,
  classificationConfidence,
}: DocumentReviewPanelProps) {
  const [approvalNotes, setApprovalNotes] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [deleteReason, setDeleteReason] = useState("");
  const [showReject, setShowReject] = useState(false);
  const [showDelete, setShowDelete] = useState(false);

  const reclassifyMutation = useReclassifyDocument(doc?.id ?? "");

  if (!doc) return null;

  const canReview =
    canApprove &&
    (doc.status === "uploaded" || doc.status === "under_review");

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>
              {DOCUMENT_TYPE_LABELS[doc.document_type]}
            </SheetTitle>
          </SheetHeader>

          <div className="mt-6 space-y-6">
            {/* Document Info */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm">Status</span>
                <StatusBadge
                  variant="document"
                  status={doc.status as BadgeDocumentStatus}
                />
              </div>
              {doc.reference_number && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">
                    Reference
                  </span>
                  <span className="font-mono text-sm">
                    {doc.reference_number}
                  </span>
                </div>
              )}
              {doc.issue_date && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">
                    Issue Date
                  </span>
                  <span className="text-sm">{formatDate(doc.issue_date)}</span>
                </div>
              )}
              {doc.expiry_date && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">
                    Expiry Date
                  </span>
                  <span className="text-sm">{formatDate(doc.expiry_date)}</span>
                </div>
              )}
              {doc.issuer && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">Issuer</span>
                  <span className="text-sm">{doc.issuer}</span>
                </div>
              )}
              {doc.file_name && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">File</span>
                  <span className="text-sm">{doc.file_name}</span>
                </div>
              )}
              {classificationMethod && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground text-sm">
                    Classification
                  </span>
                  <div className="flex items-center gap-1.5">
                    <Badge
                      variant="outline"
                      className={METHOD_COLORS[classificationMethod]}
                    >
                      {METHOD_LABELS[classificationMethod]}
                    </Badge>
                    {classificationConfidence != null && (
                      <span className="text-xs text-muted-foreground">
                        {formatClassificationConfidence(classificationConfidence)}
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Reclassify */}
            {(doc.status === "uploaded" || doc.status === "under_review") && (
              <div>
                {reclassifyMutation.isSuccess && reclassifyMutation.data && (
                  <div className="mb-2 rounded-lg border bg-muted/30 p-3 text-sm">
                    <p className="font-medium">Reclassification Result</p>
                    <p className="mt-1 text-muted-foreground">
                      {getDocTypeLabel(reclassifyMutation.data.previous_type)}
                      {" → "}
                      {getDocTypeLabel(reclassifyMutation.data.new_type)}
                      {reclassifyMutation.data.auto_applied && (
                        <span className="ml-1 text-green-600">(auto-applied)</span>
                      )}
                    </p>
                  </div>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => reclassifyMutation.mutate()}
                  disabled={reclassifyMutation.isPending}
                >
                  <RefreshCw
                    className={`mr-2 h-4 w-4 ${reclassifyMutation.isPending ? "animate-spin" : ""}`}
                  />
                  {reclassifyMutation.isPending
                    ? "Reclassifying..."
                    : "Re-classify with AI"}
                </Button>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              {doc.file_path && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDownload(doc)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                className="text-destructive hover:text-destructive"
                onClick={() => setShowDelete(true)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </Button>
            </div>

            {/* Review Section */}
            {canReview && (
              <div className="border-t pt-4">
                <h3 className="mb-3 font-semibold">Review</h3>

                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label>Notes (optional)</Label>
                    <Textarea
                      value={approvalNotes}
                      onChange={(e) => setApprovalNotes(e.target.value)}
                      placeholder="Add approval notes..."
                      rows={2}
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => onApprove(doc.id, approvalNotes || undefined)}
                      disabled={isApproving}
                    >
                      <CheckCircle className="mr-2 h-4 w-4" />
                      {isApproving ? "Approving..." : "Approve"}
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setShowReject(true)}
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Reject
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Rejection Form */}
            {showReject && (
              <div className="rounded-lg border border-destructive/50 p-4">
                <h4 className="mb-2 text-sm font-semibold">Rejection Reason</h4>
                <Textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Provide a reason for rejection (required)..."
                  rows={3}
                />
                <div className="mt-3 flex gap-2">
                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={rejectionReason.length < 5 || isRejecting}
                    onClick={() => {
                      onReject(doc.id, rejectionReason);
                      setShowReject(false);
                      setRejectionReason("");
                    }}
                  >
                    {isRejecting ? "Rejecting..." : "Confirm Rejection"}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setShowReject(false);
                      setRejectionReason("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {/* Notes */}
            {doc.notes && (
              <div className="border-t pt-4">
                <h3 className="mb-2 text-sm font-semibold">Notes</h3>
                <p className="text-muted-foreground text-sm">{doc.notes}</p>
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={showDelete}
        onOpenChange={setShowDelete}
        title="Delete Document"
        description="This action cannot be undone. Please provide a reason."
        confirmLabel={isDeleting ? "Deleting..." : "Delete"}
        variant="destructive"
        isLoading={isDeleting}
        disabled={deleteReason.length < 5}
        onConfirm={() => {
          onDelete(doc.id, deleteReason);
          setShowDelete(false);
          setDeleteReason("");
        }}
      >
        <div className="space-y-2">
          <Label>Reason (min 5 characters)</Label>
          <Textarea
            value={deleteReason}
            onChange={(e) => setDeleteReason(e.target.value)}
            placeholder="Why is this document being deleted?"
            rows={2}
          />
        </div>
      </ConfirmDialog>
    </>
  );
}
