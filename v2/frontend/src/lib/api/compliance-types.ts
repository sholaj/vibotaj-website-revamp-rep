// --- Compliance types (no React/PropelAuth dependencies) ---
// PRD-016: Enhanced Compliance Engine

/** Compliance decision for a shipment */
export type ComplianceDecision = "APPROVE" | "HOLD" | "REJECT";

/** Severity of a compliance rule */
export type RuleSeverity = "ERROR" | "WARNING" | "INFO";

/** Individual rule result */
export interface RuleResult {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  severity: RuleSeverity;
  message: string | null;
  field_path: string | null;
  document_type: string | null;
  checked_at: string | null;
  is_overridden?: boolean;
  override_reason?: string | null;
}

/** Summary counts for compliance report */
export interface ComplianceSummaryCount {
  total_rules: number;
  passed: number;
  failed: number;
  warnings: number;
}

/** Override information */
export interface ComplianceOverride {
  reason: string;
  overridden_by: string;
  overridden_at: string | null;
}

/** Full compliance report for a shipment */
export interface ComplianceReport {
  shipment_id: string;
  decision: ComplianceDecision;
  summary: ComplianceSummaryCount;
  results: RuleResult[];
  override: ComplianceOverride | null;
}

/** Single document state transition */
export interface DocumentTransition {
  id: string;
  document_id: string;
  from_state: string;
  to_state: string;
  actor_id: string | null;
  reason: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
}

/** Transition history for a shipment's documents */
export interface TransitionHistoryResponse {
  shipment_id: string;
  transitions: DocumentTransition[];
}

// --- Constants ---

/** Decision badge colors */
export const DECISION_COLORS: Record<ComplianceDecision, string> = {
  APPROVE: "bg-success/10 text-success border-success/20",
  HOLD: "bg-warning/10 text-warning border-warning/20",
  REJECT: "bg-destructive/10 text-destructive border-destructive/20",
};

/** Decision labels for display */
export const DECISION_LABELS: Record<ComplianceDecision, string> = {
  APPROVE: "Approved",
  HOLD: "On Hold",
  REJECT: "Rejected",
};

/** Severity colors */
export const SEVERITY_COLORS: Record<RuleSeverity, string> = {
  ERROR: "bg-destructive/10 text-destructive border-destructive/20",
  WARNING: "bg-warning/10 text-warning border-warning/20",
  INFO: "bg-muted text-muted-foreground border-muted",
};

/** Severity labels */
export const SEVERITY_LABELS: Record<RuleSeverity, string> = {
  ERROR: "Error",
  WARNING: "Warning",
  INFO: "Info",
};

/** Document state display labels */
export const STATE_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  UPLOADED: "Uploaded",
  VALIDATED: "Validated",
  COMPLIANCE_OK: "Compliance OK",
  COMPLIANCE_FAILED: "Compliance Failed",
  LINKED: "Linked",
  ARCHIVED: "Archived",
};

// --- Helpers ---

/** Get display label for a document state */
export function getStateLabel(state: string): string {
  return STATE_LABELS[state] ?? state;
}

/** Check if a decision is a passing state */
export function isDecisionPassing(decision: ComplianceDecision): boolean {
  return decision === "APPROVE";
}

/** Count failed rules (non-overridden) */
export function countActiveFailures(results: RuleResult[]): number {
  return results.filter((r) => !r.passed && !r.is_overridden).length;
}

/** Get color class for state */
export function getStateColor(state: string): string {
  switch (state) {
    case "DRAFT":
      return "text-muted-foreground";
    case "UPLOADED":
      return "text-warning";
    case "VALIDATED":
      return "text-info";
    case "COMPLIANCE_OK":
    case "LINKED":
      return "text-success";
    case "COMPLIANCE_FAILED":
      return "text-destructive";
    case "ARCHIVED":
      return "text-muted-foreground";
    default:
      return "text-foreground";
  }
}
