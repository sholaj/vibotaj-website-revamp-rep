// --- Classification types (no React/PropelAuth dependencies) ---
// PRD-019: AI Document Classification v2

import type { DocumentType } from "./document-types";
import { DOCUMENT_TYPE_LABELS } from "./document-types";

/** Classification method used */
export type ClassificationMethod = "ai" | "keyword" | "manual";

/** Single alternative classification */
export interface ClassificationAlternative {
  document_type: string;
  confidence: number;
}

/** Full classification result from the API */
export interface ClassificationResponse {
  document_type: string;
  confidence: number;
  method: ClassificationMethod;
  provider: string;
  reference_number: string | null;
  key_fields: Record<string, string>;
  reasoning: string;
  alternatives: ClassificationAlternative[];
}

/** Classification info embedded in upload response */
export interface ClassificationInUpload {
  suggested_type: string;
  confidence: number;
  method: string;
  auto_applied: boolean;
}

/** Reclassification result */
export interface ReclassifyResponse {
  document_id: string;
  previous_type: string;
  new_type: string;
  classification: ClassificationResponse;
  auto_applied: boolean;
}

// --- Constants ---

export const METHOD_LABELS: Record<ClassificationMethod, string> = {
  ai: "AI Detected",
  keyword: "Keyword Match",
  manual: "Manual",
};

export const METHOD_COLORS: Record<ClassificationMethod, string> = {
  ai: "text-blue-700 bg-blue-50 border-blue-200",
  keyword: "text-amber-700 bg-amber-50 border-amber-200",
  manual: "text-gray-500 bg-gray-50 border-gray-200",
};

// --- Helpers ---

/** Get confidence level category */
export function getClassificationConfidenceLevel(
  confidence: number,
): "high" | "medium" | "low" {
  if (confidence >= 0.8) return "high";
  if (confidence >= 0.5) return "medium";
  return "low";
}

/** Get confidence color class */
export function getClassificationConfidenceColor(confidence: number): string {
  const level = getClassificationConfidenceLevel(confidence);
  switch (level) {
    case "high":
      return "text-green-700";
    case "medium":
      return "text-amber-700";
    case "low":
      return "text-red-700";
  }
}

/** Format confidence as percentage */
export function formatClassificationConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

/** Get a human-readable label for a document type string */
export function getDocTypeLabel(docType: string): string {
  return DOCUMENT_TYPE_LABELS[docType as DocumentType] ?? docType;
}

/** Check if the classification confidence is actionable */
export function isConfidenceActionable(confidence: number): boolean {
  return confidence >= 0.5;
}
