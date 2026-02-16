"use client";

import { useState, useCallback, useEffect } from "react";
import { Upload, X, FileText, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { DOCUMENT_TYPE_LABELS, type DocumentType } from "@/lib/api/document-types";
import { useClassifyDocument } from "@/lib/api/classification";
import {
  type ClassificationResponse,
  METHOD_LABELS,
  getClassificationConfidenceLevel,
  formatClassificationConfidence,
  getDocTypeLabel,
} from "@/lib/api/classification-types";

const ACCEPTED_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const ACCEPTED_EXTENSIONS = ".pdf,.jpg,.jpeg,.png,.doc,.docx";
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

interface DocumentUploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpload: (file: File, type: DocumentType, referenceNumber?: string) => void;
  isUploading?: boolean;
}

const CONFIDENCE_BADGE_COLORS: Record<string, string> = {
  high: "bg-green-50 text-green-700 border-green-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  low: "bg-red-50 text-red-700 border-red-200",
};

export function DocumentUploadModal({
  open,
  onOpenChange,
  onUpload,
  isUploading,
}: DocumentUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<DocumentType | "">("");
  const [referenceNumber, setReferenceNumber] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoDetect, setAutoDetect] = useState(true);
  const [classification, setClassification] =
    useState<ClassificationResponse | null>(null);

  const classifyMutation = useClassifyDocument();

  const resetForm = useCallback(() => {
    setFile(null);
    setDocumentType("");
    setReferenceNumber("");
    setError(null);
    setClassification(null);
    classifyMutation.reset();
  }, [classifyMutation]);

  const handleClose = useCallback(
    (isOpen: boolean) => {
      if (!isOpen) resetForm();
      onOpenChange(isOpen);
    },
    [onOpenChange, resetForm],
  );

  const validateFile = useCallback((f: File): string | null => {
    if (!ACCEPTED_TYPES.includes(f.type)) {
      return "Invalid file type. Accepted: PDF, JPEG, PNG, DOC, DOCX";
    }
    if (f.size > MAX_FILE_SIZE) {
      return "File too large. Maximum size is 50MB.";
    }
    return null;
  }, []);

  const handleFileChange = useCallback(
    (f: File) => {
      const err = validateFile(f);
      if (err) {
        setError(err);
        setFile(null);
        setClassification(null);
      } else {
        setError(null);
        setFile(f);
        setClassification(null);
      }
    },
    [validateFile],
  );

  // Auto-classify when file is selected and autoDetect is on
  useEffect(() => {
    if (file && autoDetect && !classification && !classifyMutation.isPending) {
      classifyMutation.mutate(file, {
        onSuccess: (result) => {
          setClassification(result);
          // Auto-apply if high confidence and user hasn't manually selected
          if (result.confidence >= 0.7 && !documentType) {
            setDocumentType(result.document_type as DocumentType);
            if (result.reference_number) {
              setReferenceNumber(result.reference_number);
            }
          }
        },
      });
    }
  }, [file, autoDetect]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) handleFileChange(dropped);
    },
    [handleFileChange],
  );

  const handleSubmit = useCallback(() => {
    if (!file || !documentType) return;
    onUpload(file, documentType, referenceNumber || undefined);
  }, [file, documentType, referenceNumber, onUpload]);

  const handleAcceptSuggestion = useCallback(() => {
    if (!classification) return;
    setDocumentType(classification.document_type as DocumentType);
    if (classification.reference_number) {
      setReferenceNumber(classification.reference_number);
    }
  }, [classification]);

  const docTypes = Object.entries(DOCUMENT_TYPE_LABELS) as [DocumentType, string][];

  const confidenceLevel = classification
    ? getClassificationConfidenceLevel(classification.confidence)
    : null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Auto-detect toggle */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-blue-600" />
              <Label htmlFor="auto-detect" className="text-sm">
                AI Auto-detect Type
              </Label>
            </div>
            <Switch
              id="auto-detect"
              checked={autoDetect}
              onCheckedChange={setAutoDetect}
              size="sm"
            />
          </div>

          {/* Drop zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
              dragActive
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25"
            }`}
          >
            {file ? (
              <div className="flex items-center gap-3">
                <FileText className="text-primary h-8 w-8" />
                <div>
                  <p className="text-sm font-medium">{file.name}</p>
                  <p className="text-muted-foreground text-xs">
                    {(file.size / 1024).toFixed(0)} KB
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => {
                    setFile(null);
                    setClassification(null);
                    classifyMutation.reset();
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <>
                <Upload className="text-muted-foreground mb-2 h-8 w-8" />
                <p className="text-sm">
                  Drag & drop or{" "}
                  <label className="text-primary cursor-pointer font-medium hover:underline">
                    browse
                    <input
                      type="file"
                      className="hidden"
                      accept={ACCEPTED_EXTENSIONS}
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleFileChange(f);
                      }}
                    />
                  </label>
                </p>
                <p className="text-muted-foreground mt-1 text-xs">
                  PDF, JPEG, PNG, DOC, DOCX (max 50MB)
                </p>
              </>
            )}
          </div>

          {error && (
            <p className="text-destructive text-sm">{error}</p>
          )}

          {/* AI Classification Result */}
          {autoDetect && file && (
            <div className="rounded-lg border bg-muted/30 p-3">
              {classifyMutation.isPending && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing document...
                </div>
              )}
              {classifyMutation.isError && (
                <p className="text-sm text-muted-foreground">
                  Auto-detect unavailable. Please select type manually.
                </p>
              )}
              {classification && confidenceLevel && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">AI Suggestion</span>
                    <div className="flex items-center gap-1.5">
                      <Badge
                        variant="outline"
                        className={CONFIDENCE_BADGE_COLORS[confidenceLevel]}
                      >
                        {formatClassificationConfidence(classification.confidence)}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {METHOD_LABELS[classification.method]}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">
                      {getDocTypeLabel(classification.document_type)}
                    </span>
                    {documentType !== classification.document_type && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={handleAcceptSuggestion}
                      >
                        Accept
                      </Button>
                    )}
                    {documentType === classification.document_type && (
                      <span className="text-xs text-green-600">Applied</span>
                    )}
                  </div>
                  {classification.alternatives.length > 0 && (
                    <div className="border-t pt-2">
                      <p className="mb-1 text-xs text-muted-foreground">
                        Alternatives:
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {classification.alternatives.map((alt) => (
                          <button
                            key={alt.document_type}
                            type="button"
                            className="rounded border px-2 py-0.5 text-xs hover:bg-accent"
                            onClick={() =>
                              setDocumentType(alt.document_type as DocumentType)
                            }
                          >
                            {getDocTypeLabel(alt.document_type)}{" "}
                            ({Math.round(alt.confidence * 100)}%)
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Document type */}
          <div className="space-y-2">
            <Label htmlFor="doc-type">Document Type</Label>
            <Select
              value={documentType}
              onValueChange={(v) => setDocumentType(v as DocumentType)}
            >
              <SelectTrigger id="doc-type">
                <SelectValue placeholder="Select type..." />
              </SelectTrigger>
              <SelectContent>
                {docTypes.map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Reference number */}
          <div className="space-y-2">
            <Label htmlFor="ref-number">Reference Number (optional)</Label>
            <Input
              id="ref-number"
              value={referenceNumber}
              onChange={(e) => setReferenceNumber(e.target.value)}
              placeholder="e.g. INV-2026-001"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleClose(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!file || !documentType || isUploading}
          >
            {isUploading ? "Uploading..." : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
