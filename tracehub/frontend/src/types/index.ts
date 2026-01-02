// ============================================
// TraceHub Frontend Type Definitions
// Aligned with backend Pydantic schemas
// ============================================

// ============================================
// Authentication Types
// ============================================

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface User {
  username: string
  email: string
  full_name: string
  role?: 'admin' | 'user' | 'buyer' | 'supplier'
}

// ============================================
// Party Types
// ============================================

export type PartyType = 'supplier' | 'buyer' | 'agent' | 'carrier'

export interface Party {
  id: string
  type: PartyType
  company_name: string
  contact_name?: string
  email?: string
  phone?: string
  address?: string
  city?: string
  country: string
}

// ============================================
// Product Types
// ============================================

export interface Product {
  id: string
  hs_code: string
  description: string
  quantity_net_kg: number
  quantity_gross_kg: number
  unit_of_measure: string
  packaging_type?: string
  packaging_count?: number
  batch_lot_number?: string
  quality_grade?: string
}

// ============================================
// Document Types
// Aligned with backend DocumentType enum
// ============================================

export type DocumentType =
  | 'bill_of_lading'
  | 'commercial_invoice'
  | 'packing_list'
  | 'certificate_of_origin'
  | 'phytosanitary_certificate'
  | 'fumigation_certificate'
  | 'sanitary_certificate'
  | 'insurance_certificate'
  | 'customs_declaration'
  | 'contract'
  | 'eudr_due_diligence'
  | 'quality_certificate'
  | 'other'

// Aligned with backend DocumentStatus enum
export type DocumentStatus =
  | 'draft'
  | 'uploaded'
  | 'validated'
  | 'compliance_ok'
  | 'compliance_failed'  // Fixed: backend uses 'compliance_failed' not 'compliance_fail'
  | 'linked'
  | 'archived'

export interface Document {
  id: string
  shipment_id: string
  document_type: DocumentType
  name: string
  file_name?: string
  file_size_bytes?: number
  mime_type?: string
  status: DocumentStatus
  required?: boolean
  reference_number?: string
  issue_date?: string
  expiry_date?: string
  issuing_authority?: string
  uploaded_by?: string
  uploaded_at?: string
  validated_at?: string
  validated_by?: string
  created_at?: string
  updated_at?: string
}

// ============================================
// Container Event Types
// Aligned with backend EventType enum
// ============================================

export type EventType =
  | 'booking_confirmed'
  | 'gate_in'
  | 'loaded'
  | 'departed'
  | 'transshipment'
  | 'arrived'
  | 'discharged'
  | 'gate_out'
  | 'delivered'
  | 'customs_hold'
  | 'customs_released'
  | 'empty_return'
  | 'unknown'  // Added: present in backend

export interface ContainerEvent {
  id: string
  event_type: EventType
  event_timestamp: string
  location_name?: string
  location_code?: string
  vessel_name?: string
  voyage_number?: string
  description?: string
  delay_hours?: number
  source?: string
}

// ============================================
// Shipment Types
// Aligned with backend ShipmentStatus enum
// ============================================

export type ShipmentStatus =
  | 'created'
  | 'docs_pending'
  | 'docs_complete'
  | 'in_transit'
  | 'arrived'
  | 'delivered'
  | 'closed'

export interface Shipment {
  id: string
  reference: string
  container_number: string
  bl_number?: string
  booking_reference?: string
  vessel_name?: string
  voyage_number?: string
  etd?: string
  eta?: string
  atd?: string
  ata?: string
  pol_code?: string
  pol_name?: string
  pod_code?: string
  pod_name?: string
  final_destination?: string
  incoterms?: string
  status: ShipmentStatus
  buyer?: Party
  supplier?: Party
  products?: Product[]
  documents?: Document[]
  container_events?: ContainerEvent[]
  created_at?: string
  updated_at?: string
}

// ============================================
// Live Tracking Types (from JSONCargo)
// ============================================

export interface VesselInfo {
  original_name?: string
  original_voyage?: string
  current_name?: string
  current_voyage?: string
}

export interface LocationInfo {
  port: string
  terminal?: string
  timestamp?: string
  eta?: string
}

export interface LiveTracking {
  container_number: string
  container_type?: string
  status: string
  carrier: string
  eta?: string
  eta_next?: string
  atd_origin?: string
  origin: LocationInfo
  destination: LocationInfo
  current_location: LocationInfo
  next_location: LocationInfo
  vessel: VesselInfo
  last_updated?: string
  events: ContainerEvent[]
}

// ============================================
// Compliance Types
// ============================================

export interface ComplianceStatus {
  is_compliant: boolean
  total_required: number
  total_present: number
  missing_documents: DocumentType[]
  pending_validation: string[]
  issues: string[]
}

// ============================================
// Document Summary Types (from backend schema)
// ============================================

export interface DocumentSummary {
  total_required: number
  total_uploaded: number
  complete: number
  missing: DocumentType[]
  pending_validation: number
  is_complete: boolean
}

// ============================================
// API Response Types
// ============================================

export interface ApiError {
  detail: string
  status_code?: number
}

export interface ContainerStatusResponse {
  container_number: string
  shipment_reference: string
  shipment_status: ShipmentStatus
  vessel?: string
  voyage?: string
  etd?: string
  eta?: string
  pol: { code?: string; name?: string }
  pod: { code?: string; name?: string }
  latest_event?: {
    type: EventType
    timestamp: string
    location?: string
  } | null
  live_tracking?: LiveTracking | null
}

export interface ShipmentEventsResponse {
  events: ContainerEvent[]
}

export interface ShipmentDocumentsResponse {
  documents: Document[]
  required_types: DocumentType[]
  summary: DocumentSummary
}

export interface TrackingRefreshResponse {
  message: string
  shipment_id: string
  container_number: string
  events_added: number
  live_status?: string
}

export interface ShipmentDetailResponse {
  shipment: Shipment
  latest_event?: ContainerEvent | null
  documents: Document[]
  document_summary: DocumentSummary
}

// ============================================
// Pagination Types
// ============================================

export interface PaginationParams {
  page?: number
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}

// ============================================
// Form/Request Types
// ============================================

export interface DocumentUploadRequest {
  shipment_id: string
  document_type: DocumentType
  file: File
  reference_number?: string
  issue_date?: string
  expiry_date?: string
  issuing_authority?: string
}
