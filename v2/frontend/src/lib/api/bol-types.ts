// --- BoL parse types (no React/PropelAuth dependencies) ---
// PRD-018: BoL Parser + Auto-Enrichment Pipeline

import type { ComplianceDecision } from "./compliance-types";

/** Parse status of a BoL document */
export type BolParseStatus = "parsed" | "pending" | "failed" | "not_bol";

/** Single extracted field with confidence */
export interface BolField {
  value: string | null;
  confidence: number;
}

/** Compliance result from BoL check */
export interface BolComplianceResult {
  decision: ComplianceDecision;
  rules_passed: number;
  rules_failed: number;
  rules_total: number;
}

/** Full parsed BoL response from API */
export interface BolParsedResponse {
  document_id: string;
  parse_status: BolParseStatus;
  parsed_at: string | null;
  confidence_score: number;
  fields: Record<string, BolField>;
  compliance: BolComplianceResult | null;
  auto_synced: boolean;
}

/** Single field change in sync preview */
export interface SyncChange {
  field: string;
  current: string | null;
  new_value: string | null;
  is_placeholder: boolean;
  will_update: boolean;
}

/** Sync preview response */
export interface BolSyncPreviewResponse {
  document_id: string;
  shipment_id: string;
  shipment_reference: string;
  changes: SyncChange[];
  auto_synced: boolean;
}

/** Cross-validation issue */
export interface CrossValidationIssue {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  severity: "ERROR" | "WARNING" | "INFO";
  message: string;
}

// --- Constants ---

export const PARSE_STATUS_LABELS: Record<BolParseStatus, string> = {
  parsed: "Parsed",
  pending: "Pending",
  failed: "Failed",
  not_bol: "Not a BoL",
};

export const PARSE_STATUS_COLORS: Record<BolParseStatus, string> = {
  parsed: "text-green-700 bg-green-50 border-green-200",
  pending: "text-amber-700 bg-amber-50 border-amber-200",
  failed: "text-red-700 bg-red-50 border-red-200",
  not_bol: "text-gray-500 bg-gray-50 border-gray-200",
};

/** Labels for BoL field names */
export const BOL_FIELD_LABELS: Record<string, string> = {
  bol_number: "B/L Number",
  shipper: "Shipper",
  consignee: "Consignee",
  container_number: "Container",
  vessel_name: "Vessel",
  voyage_number: "Voyage",
  port_of_loading: "Port of Loading",
  port_of_discharge: "Port of Discharge",
};

/** Sync field labels (shipment field names) */
export const SYNC_FIELD_LABELS: Record<string, string> = {
  bl_number: "B/L Number",
  container_number: "Container Number",
  vessel_name: "Vessel Name",
  voyage_number: "Voyage Number",
  pol_code: "Port of Loading",
  pod_code: "Port of Discharge",
};

// --- Helpers ---

/** Check if parse was successful */
export function isParsed(status: BolParseStatus): boolean {
  return status === "parsed";
}

/** Check if document is a BoL */
export function isBol(status: BolParseStatus): boolean {
  return status !== "not_bol";
}

/** Get confidence level category */
export function getConfidenceLevel(
  confidence: number,
): "high" | "medium" | "low" {
  if (confidence >= 0.8) return "high";
  if (confidence >= 0.5) return "medium";
  return "low";
}

/** Get confidence color class */
export function getConfidenceColor(confidence: number): string {
  const level = getConfidenceLevel(confidence);
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
export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

/** Count fields that will update in sync preview */
export function countUpdates(changes: SyncChange[]): number {
  return changes.filter((c) => c.will_update).length;
}

/** Count placeholder replacements in sync preview */
export function countPlaceholders(changes: SyncChange[]): number {
  return changes.filter((c) => c.is_placeholder).length;
}

/** Get ordered field keys for display */
export function getOrderedFieldKeys(
  fields: Record<string, BolField>,
): string[] {
  const order = [
    "bol_number",
    "shipper",
    "consignee",
    "container_number",
    "vessel_name",
    "voyage_number",
    "port_of_loading",
    "port_of_discharge",
  ];
  return order.filter((key) => key in fields);
}
