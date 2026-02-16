// --- Audit pack types (no React/PropelAuth dependencies) ---
// PRD-017: Audit Pack v2

import type { ComplianceDecision } from "./compliance-types";

/** Status of the audit pack */
export type AuditPackStatus = "ready" | "generating" | "outdated" | "none";

/** Individual item in the audit pack contents */
export interface AuditPackContent {
  name: string;
  type: "index" | "document" | "tracking" | "metadata";
  document_type?: string | null;
}

/** Full audit pack status response from the API */
export interface AuditPackStatusResponse {
  shipment_id: string;
  status: AuditPackStatus;
  generated_at: string | null;
  download_url: string | null;
  expires_at: string | null;
  contents: AuditPackContent[];
  compliance_decision: ComplianceDecision | null;
  document_count: number;
  is_outdated: boolean;
}

// --- Constants ---

export const PACK_STATUS_LABELS: Record<AuditPackStatus, string> = {
  ready: "Ready",
  generating: "Generating...",
  outdated: "Outdated",
  none: "Not Generated",
};

export const PACK_STATUS_COLORS: Record<AuditPackStatus, string> = {
  ready: "text-green-700 bg-green-50 border-green-200",
  generating: "text-blue-700 bg-blue-50 border-blue-200",
  outdated: "text-amber-700 bg-amber-50 border-amber-200",
  none: "text-gray-500 bg-gray-50 border-gray-200",
};

export const CONTENT_TYPE_ICONS: Record<string, string> = {
  index: "FileText",
  document: "File",
  tracking: "MapPin",
  metadata: "Database",
};

// --- Helpers ---

export function isPackReady(status: AuditPackStatus): boolean {
  return status === "ready";
}

export function isPackActionable(status: AuditPackStatus): boolean {
  return status !== "generating";
}

export function getDocumentContentCount(contents: AuditPackContent[]): number {
  return contents.filter((c) => c.type === "document").length;
}

export function formatGeneratedAt(isoDate: string | null): string {
  if (!isoDate) return "Never";
  const date = new Date(isoDate);
  return date.toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
