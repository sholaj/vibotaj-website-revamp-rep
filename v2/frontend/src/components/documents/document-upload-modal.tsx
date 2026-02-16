"use client";

import { useState, useCallback } from "react";
import { Upload, X, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
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
import { DOCUMENT_TYPE_LABELS, type DocumentType } from "@/lib/api/document-types";

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

  const resetForm = useCallback(() => {
    setFile(null);
    setDocumentType("");
    setReferenceNumber("");
    setError(null);
  }, []);

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
      } else {
        setError(null);
        setFile(f);
      }
    },
    [validateFile],
  );

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

  const docTypes = Object.entries(DOCUMENT_TYPE_LABELS) as [DocumentType, string][];

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
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
                  onClick={() => setFile(null)}
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
