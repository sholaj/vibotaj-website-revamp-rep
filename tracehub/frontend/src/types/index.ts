// Authentication
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
  email?: string
  role?: string
}

// Parties
export interface Party {
  id: string
  type: 'supplier' | 'buyer' | 'agent' | 'carrier'
  company_name: string
  contact_name?: string
  email?: string
  phone?: string
  address?: string
  city?: string
  country: string
}

// Products
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

// Documents
export type DocumentType =
  | 'bill_of_lading'
  | 'commercial_invoice'
  | 'packing_list'
  | 'certificate_of_origin'
  | 'phytosanitary_certificate'
  | 'fumigation_certificate'
  | 'sanitary_certificate'
  | 'insurance_certificate'
  | 'eudr_declaration'
  | 'customs_declaration'
  | 'other'

export type DocumentStatus =
  | 'draft'
  | 'uploaded'
  | 'validated'
  | 'compliance_ok'
  | 'compliance_fail'
  | 'linked'
  | 'archived'

export interface Document {
  id: string
  shipment_id: string
  document_type: DocumentType
  name: string
  status: DocumentStatus
  reference_number?: string
  issue_date?: string
  expiry_date?: string
  issuing_authority?: string
  file_path?: string
  file_size?: number
  uploaded_by: string
  uploaded_at: string
  validated_at?: string
  validated_by?: string
}

// Container Events
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

export interface ContainerEvent {
  id: string
  event_type: EventType
  event_timestamp: string
  location_name?: string
  location_code?: string
  vessel_name?: string
  voyage_number?: string
  description?: string
}

// Shipments
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
}

// Live Tracking (from JSONCargo)
export interface LiveTracking {
  container_number: string
  container_type?: string
  status: string
  carrier: string
  eta?: string
  eta_next?: string
  atd_origin?: string
  origin: {
    port: string
    terminal?: string
  }
  destination: {
    port: string
    terminal?: string
  }
  current_location: {
    port: string
    terminal?: string
    timestamp?: string
  }
  next_location: {
    port: string
    terminal?: string
    eta?: string
  }
  vessel: {
    original_name?: string
    original_voyage?: string
    current_name?: string
    current_voyage?: string
  }
  last_updated?: string
  events: ContainerEvent[]
}

// Compliance
export interface ComplianceStatus {
  is_compliant: boolean
  total_required: number
  total_present: number
  missing_documents: DocumentType[]
  pending_validation: string[]
  issues: string[]
}

// API Responses
export interface ShipmentDetailResponse {
  shipment: Shipment
  compliance: ComplianceStatus
  live_tracking?: LiveTracking
}
