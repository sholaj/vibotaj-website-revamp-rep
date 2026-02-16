// --- Document types (no React/PropelAuth dependencies) ---

export type DocumentType =
  | "bill_of_lading"
  | "commercial_invoice"
  | "packing_list"
  | "certificate_of_origin"
  | "phytosanitary_certificate"
  | "fumigation_certificate"
  | "sanitary_certificate"
  | "insurance_certificate"
  | "customs_declaration"
  | "contract"
  | "eudr_due_diligence"
  | "quality_certificate"
  | "eu_traces_certificate"
  | "veterinary_health_certificate"
  | "export_declaration"
  | "other";

export type DocumentStatus =
  | "pending"
  | "uploaded"
  | "under_review"
  | "approved"
  | "rejected"
  | "expired";

export interface Document {
  id: string;
  shipment_id: string;
  document_type: DocumentType;
  status: DocumentStatus;
  file_path: string | null;
  file_name: string | null;
  file_size: number | null;
  reference_number: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  issuer: string | null;
  notes: string | null;
  uploaded_by: string | null;
  reviewed_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentSummary {
  total_required: number;
  total_present: number;
  missing_types: DocumentType[];
  pending_validation: DocumentType[];
}

export interface ValidationIssue {
  id: string;
  severity: "error" | "warning";
  message: string;
  field: string | null;
  overridable: boolean;
  overridden: boolean;
  override_reason: string | null;
}

export interface ShipmentDocumentsResponse {
  documents: Document[];
  required_types: DocumentType[];
  summary: DocumentSummary;
}

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  bill_of_lading: "Bill of Lading",
  commercial_invoice: "Commercial Invoice",
  packing_list: "Packing List",
  certificate_of_origin: "Certificate of Origin",
  phytosanitary_certificate: "Phytosanitary Certificate",
  fumigation_certificate: "Fumigation Certificate",
  sanitary_certificate: "Sanitary Certificate",
  insurance_certificate: "Insurance Certificate",
  customs_declaration: "Customs Declaration",
  contract: "Contract",
  eudr_due_diligence: "EUDR Due Diligence",
  quality_certificate: "Quality Certificate",
  eu_traces_certificate: "EU TRACES Certificate",
  veterinary_health_certificate: "Veterinary Health Certificate",
  export_declaration: "Export Declaration",
  other: "Other",
};

export function getComplianceProgress(summary: DocumentSummary): number {
  if (summary.total_required === 0) return 100;
  return Math.round((summary.total_present / summary.total_required) * 100);
}

export function isDocumentComplete(summary: DocumentSummary): boolean {
  return (
    summary.missing_types.length === 0 &&
    summary.pending_validation.length === 0
  );
}
