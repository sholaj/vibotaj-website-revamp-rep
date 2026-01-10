// ============================================
// TraceHub Frontend Type Definitions
// Aligned with backend Pydantic schemas
// ============================================

export * from './organization'
export type { OrgPermission, OrgRole, OrganizationType } from './organization'
import type { OrgRole, OrganizationType } from './organization'

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

// User roles aligned with backend UserRole enum
export type UserRole = 'admin' | 'compliance' | 'logistics_agent' | 'buyer' | 'supplier' | 'viewer'

// Product types aligned with compliance matrix
export type ProductType =
  | 'horn_hoof'      // HS 0506, 0507 - Animal by-products (NO EUDR)
  | 'sweet_potato'   // HS 0714 - Sweet potato pellets (NO EUDR)
  | 'hibiscus'       // HS 0902 - Hibiscus flowers (NO EUDR)
  | 'ginger'         // HS 0910 - Dried ginger (NO EUDR)
  | 'cocoa'          // HS 1801 - Cocoa beans (EUDR APPLICABLE)
  | 'other'          // Other/unspecified

// Product type metadata for UI display
export const PRODUCT_TYPE_OPTIONS: Array<{
  value: ProductType
  label: string
  hsCode: string
  eudrRequired: boolean
}> = [
  { value: 'horn_hoof', label: 'Horn & Hoof', hsCode: '0506/0507', eudrRequired: false },
  { value: 'sweet_potato', label: 'Sweet Potato Pellets', hsCode: '0714', eudrRequired: false },
  { value: 'hibiscus', label: 'Hibiscus Flowers', hsCode: '0902', eudrRequired: false },
  { value: 'ginger', label: 'Dried Ginger', hsCode: '0910', eudrRequired: false },
  { value: 'cocoa', label: 'Cocoa Beans', hsCode: '1801', eudrRequired: true },
  { value: 'other', label: 'Other', hsCode: 'N/A', eudrRequired: false },
]

export interface User {
  username: string
  email: string
  full_name: string
  role?: UserRole
}

// Current user with full details and permissions
export interface CurrentUser {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  organization_id: string
  permissions: string[]
  // Organization-scoped permissions
  org_role?: OrgRole | null
  org_type?: OrganizationType | null
  org_permissions?: string[]
}

// User management types
export interface UserCreate {
  email: string
  full_name: string
  password: string
  role: UserRole
}

export interface UserUpdate {
  email?: string
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

export interface UserOrganizationInfo {
  organization_id: string
  organization_name: string
  organization_type: OrganizationType
  org_role: OrgRole
}

export interface UserResponse {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at?: string
  last_login?: string
  primary_organization?: UserOrganizationInfo
}

export interface UserListResponse {
  items: UserResponse[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface RoleInfo {
  value: UserRole
  name: string
  description: string
  can_assign: boolean
}

export interface RolesResponse {
  roles: RoleInfo[]
}

export interface PermissionsResponse {
  user_id: string
  role: UserRole
  permissions: string[]
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
  // Horn & Hoof specific documents (HS 0506/0507)
  | 'eu_traces_certificate'
  | 'veterinary_health_certificate'
  | 'export_declaration'
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
  document_types?: string[]  // Multiple document types when PDF contains several docs
  name: string
  file_name?: string
  file_path?: string
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
  // Multi-document PDF fields
  is_combined?: boolean
  content_count?: number
  page_count?: number
}

// Document content within a combined PDF
export interface DocumentContent {
  id: string
  document_type: DocumentType
  status: DocumentStatus
  page_start: number
  page_end: number
  reference_number?: string
  confidence: number
  detection_method: 'ai' | 'keyword' | 'manual'
  validated_at?: string
  validated_by?: string
  validation_notes?: string
  detected_fields?: Record<string, unknown>
}

export interface DocumentContentsResponse {
  document_id: string
  file_name: string
  is_combined: boolean
  page_count: number
  content_count: number
  contents: DocumentContent[]
}

export interface DetectedDocument {
  document_type: string
  page_start: number
  page_end: number
  reference_number?: string
  confidence: number
  detection_method: string
  detected_fields?: Record<string, unknown>
}

export interface DuplicateWarning {
  reference_number: string
  document_type: string
  existing_document_id: string
  first_seen_at?: string
}

export interface DocumentUploadResponse {
  id: string
  name: string
  type: DocumentType
  status: DocumentStatus
  message: string
  page_count: number
  is_combined: boolean
  content_count: number
  detection?: {
    detected_contents: DetectedDocument[]
    duplicates_found: DuplicateWarning[]
    ai_available: boolean
  }
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
  product_type?: ProductType  // Product category for compliance requirements
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
  buyer_organization_id?: string  // UUID of linked buyer organization
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
// Shipment Creation Types
// ============================================

// Request type for creating a shipment
export interface ShipmentCreateRequest {
  reference: string
  container_number: string
  product_type: ProductType  // Required - determines document requirements
  vessel_name?: string
  voyage_number?: string
  bl_number?: string
  booking_ref?: string
  carrier_code?: string
  carrier_name?: string
  etd?: string  // ISO date string
  eta?: string  // ISO date string
  pol_code?: string
  pol_name?: string
  pod_code?: string
  pod_name?: string
  incoterms?: string
  exporter_name?: string
  importer_name?: string
  buyer_organization_id?: string  // UUID string
  is_historical?: boolean
  notes?: string
}

// Buyer organization for dropdown
export interface BuyerOrganization {
  id: string
  name: string
  slug: string
  type: string
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
  document_types?: string[]  // Additional types if PDF contains multiple docs
  file: File
  reference_number?: string
  issue_date?: string
  expiry_date?: string
  issuing_authority?: string
}

// ============================================
// Document Workflow Types
// ============================================

export interface ValidationResult {
  is_valid: boolean
  errors: string[]
  warnings: string[]
  info: string[]
  total_issues: number
}

export interface RequiredField {
  field: string
  description: string
  required: boolean
  severity: 'error' | 'warning' | 'info'
}

export interface StatusInfo {
  status: string
  display: string
  color: string
  actions: string[]
}

export interface DocumentValidationResponse {
  document_id: string
  document_type: DocumentType
  current_status: DocumentStatus
  validation: ValidationResult
  required_fields: RequiredField[]
  status_info: StatusInfo
}

export interface DocumentTransitionsResponse {
  document_id: string
  current_status: DocumentStatus
  current_status_info: StatusInfo
  allowed_transitions: Array<{
    status: DocumentStatus
    info: StatusInfo
  }>
}

export interface TransitionResponse {
  message: string
  result: {
    success: boolean
    previous_status: DocumentStatus
    new_status: DocumentStatus
    transitioned_at: string
    transitioned_by: string
    validation?: ValidationResult
    error?: string
  }
}

export interface ExpiringDocument {
  document_id: string
  document_type: DocumentType
  name: string
  expiry_date: string
  days_until_expiry: number
  is_expired: boolean
  urgency: 'expired' | 'critical' | 'warning' | 'info'
}

export interface ExpiringDocumentsResponse {
  days_ahead: number
  total_expiring: number
  documents: ExpiringDocument[]
}

export interface DocumentRequirementsResponse {
  document_type: DocumentType
  required_fields: RequiredField[]
}

export interface WorkflowSummary {
  total: number
  by_status: Record<DocumentStatus, number>
  complete: number
  pending_review: number
  failed: number
  draft: number
  progress_percent: number
}

export interface WorkflowSummaryResponse {
  shipment_id: string
  workflow_summary: WorkflowSummary
  expiring_soon: number
  expiring_documents: ExpiringDocument[]
}

// ============================================
// Notification Types
// ============================================

export type NotificationType =
  | 'document_uploaded'
  | 'document_validated'
  | 'document_rejected'
  | 'eta_changed'
  | 'shipment_arrived'
  | 'shipment_departed'
  | 'shipment_delivered'
  | 'compliance_alert'
  | 'expiry_warning'
  | 'system_alert'

export interface Notification {
  id: string
  user_id: string
  type: NotificationType
  title: string
  message: string
  data: Record<string, unknown>
  read: boolean
  read_at: string | null
  created_at: string
}

export interface NotificationListResponse {
  notifications: Notification[]
  total: number
  unread_count: number
}

export interface UnreadCountResponse {
  unread_count: number
}

export interface NotificationTypeInfo {
  name: string
  description: string
  icon: string
  color: string
}

// ============================================
// Analytics Types
// ============================================

export interface DashboardStats {
  shipments: {
    total: number
    in_transit: number
    delivered_this_month: number
    with_delays: number
  }
  documents: {
    total: number
    pending_validation: number
    completion_rate: number
    expiring_soon: number
  }
  compliance: {
    rate: number
    eudr_coverage: number
    needing_attention: number
  }
  tracking: {
    events_today: number
    delays_detected: number
    containers_tracked: number
  }
  generated_at: string
}

export interface ShipmentStats {
  total: number
  by_status: Record<ShipmentStatus, number>
  avg_transit_days: number | null
  recent_shipments: number
  in_transit_count: number
  completed_this_month: number
  delayed_count: number
}

export interface DocumentStats {
  total: number
  by_status: Record<DocumentStatus, number>
  by_type: Record<DocumentType, number>
  completion_rate: number
  pending_validation: number
  expiring_soon: number
  recently_uploaded: number
}

export interface ComplianceMetrics {
  compliant_rate: number
  eudr_coverage: number
  shipments_needing_attention: number
  failed_documents: number
  issues_summary: {
    missing_documents: number
    failed_validation: number
    expiring_certificates: number
  }
}

export interface TrackingStats {
  total_events: number
  events_by_type: Record<EventType, number>
  delays_detected: number
  avg_delay_hours: number
  recent_events_24h: number
  api_calls_today: number
  containers_tracked: number
}

export interface ShipmentTrendData {
  date: string
  count: number
}

export interface ShipmentTrendsResponse {
  period_days: number
  group_by: string
  data: ShipmentTrendData[]
}

export interface DocumentDistribution {
  status: DocumentStatus
  count: number
}

export interface DocumentDistributionResponse {
  data: DocumentDistribution[]
}

export interface ActivityItem {
  id: string
  action: string
  username: string
  resource_type: string | null
  resource_id: string | null
  timestamp: string
  details: Record<string, unknown>
}

export interface RecentActivityResponse {
  activities: ActivityItem[]
}

// ============================================
// Health Check Types
// ============================================

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  version: string
  components: {
    api: {
      status: string
      uptime_seconds: number | null
    }
    database: {
      status: string
      latency_ms: number | null
    }
    tracking: {
      last_sync: string | null
    }
  }
}

// ============================================
// EUDR Compliance Types
// ============================================

export type RiskLevel = 'low' | 'medium' | 'high' | 'unknown'

export type EUDRValidationStatus = 'compliant' | 'non_compliant' | 'pending' | 'incomplete'

export type VerificationMethod =
  | 'document_review'
  | 'supplier_attestation'
  | 'on_site_inspection'
  | 'satellite_verification'
  | 'third_party_audit'
  | 'self_declaration'

export interface EUDRChecklistItem {
  item: string
  passed: boolean
  details: string
}

export interface EUDRValidationCheck {
  name: string
  passed: boolean
  message: string
  severity: 'error' | 'warning' | 'info'
}

export interface EUDROriginValidation {
  origin_id: string
  farm_plot_id: string
  country: string
  validation: {
    is_valid: boolean
    status: EUDRValidationStatus
    risk_level: RiskLevel
    risk_score: number
    checks: EUDRValidationCheck[]
    missing_fields: string[]
    warnings: string[]
    errors: string[]
    total_checks: number
    passed_checks: number
  }
  risk: EUDRRiskAssessment
}

export interface EUDRRiskAssessment {
  risk_level: RiskLevel
  country_risk: RiskLevel
  coordinates: {
    lat: number | null
    lng: number | null
  }
  satellite_check: {
    available: boolean
    provider: string | null
    last_checked: string | null
    forest_loss_detected: boolean | null
    message: string
  }
  recommendations: string[]
  eudr_article: string
  assessed_at: string
}

export interface EUDRComplianceSummary {
  total_origins: number
  compliant_origins: number
  has_eudr_document: boolean
  passed_checks: number
  total_checks: number
}

export interface EUDRStatusResponse {
  shipment_id: string
  shipment_reference: string
  overall_status: EUDRValidationStatus
  overall_risk_level: RiskLevel
  is_compliant: boolean
  checklist: EUDRChecklistItem[]
  summary: EUDRComplianceSummary
  origin_validations: EUDROriginValidation[]
  cutoff_date: string
  assessed_at: string
}

export interface EUDRActionItem {
  action: string
  details: string
  priority: 'high' | 'medium' | 'low'
}

export interface EUDRValidationResponse {
  shipment_id: string
  validation_result: EUDRStatusResponse
  action_items: EUDRActionItem[]
  validated_at: string
  validated_by: string
}

export interface EUDROriginVerificationRequest {
  farm_plot_identifier?: string
  geolocation_lat?: number
  geolocation_lng?: number
  country?: string
  region?: string
  district?: string
  production_start_date?: string
  production_end_date?: string
  supplier_attestation_date?: string
  supplier_attestation_reference?: string
  deforestation_free_statement?: string
  verification_method?: VerificationMethod
}

export interface EUDROriginValidationResponse {
  origin_id: string
  is_valid: boolean
  status: EUDRValidationStatus
  risk_level: RiskLevel
  risk_score: number
  checks: EUDRValidationCheck[]
  missing_fields: string[]
  warnings: string[]
  errors: string[]
}

export interface EUDRGeolocationCheckRequest {
  lat: number
  lng: number
  country: string
}

export interface EUDRGeolocationCheckResponse {
  coordinates: {
    lat: number
    lng: number
  }
  country: string
  validation: {
    is_valid: boolean
    status: EUDRValidationStatus
    risk_level: RiskLevel
    risk_score: number
    checks: EUDRValidationCheck[]
    missing_fields: string[]
    warnings: string[]
    errors: string[]
  }
  risk_assessment: EUDRRiskAssessment
}

export interface EUDRProductionDateCheckRequest {
  production_date: string
}

export interface EUDRProductionDateCheckResponse {
  production_date: string
  cutoff_date: string
  is_valid: boolean
  message: string
  days_after_cutoff: number | null
}

export interface EUDRCountryRiskLevels {
  risk_levels: Record<string, RiskLevel>
  risk_categories: {
    low: string[]
    medium: string[]
    high: string[]
  }
  source: string
  last_updated: string
}

export interface EUDRRegulationInfo {
  regulation: {
    name: string
    official_name: string
    short_name: string
    entry_into_force: string
    applicable_from_large_operators: string
    applicable_from_sme: string
  }
  key_dates: {
    cutoff_date: string
    cutoff_description: string
  }
  covered_commodities: Array<{
    name: string
    hs_codes: string[]
  }>
  requirements: {
    geolocation: string
    production_date: string
    due_diligence: string
    traceability: string
  }
  compliance_checklist: string[]
}

// ============================================
// Organization Management Types
// ============================================

export type OrganizationStatus = 'active' | 'suspended' | 'pending_setup'

export interface OrganizationAddress {
  street?: string
  city?: string
  postal_code?: string
  country: string
}

export interface Organization {
  id: string
  name: string
  slug: string
  type: OrganizationType
  status: OrganizationStatus
  contact_email: string
  contact_phone?: string
  address?: OrganizationAddress
  tax_id?: string
  registration_number?: string
  logo_url?: string
  member_count?: number
  shipment_count?: number
  created_at: string
  updated_at?: string
  created_by?: string
}

export interface OrganizationListItem {
  id: string
  name: string
  slug: string
  type: OrganizationType
  status: OrganizationStatus
  member_count: number
  created_at: string
}

export interface OrganizationListResponse {
  items: OrganizationListItem[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface OrganizationCreate {
  name: string
  slug: string
  type: OrganizationType
  contact_email: string
  contact_phone?: string
  address?: OrganizationAddress
  tax_id?: string
  registration_number?: string
}

export interface OrganizationUpdate {
  name?: string
  contact_email?: string
  contact_phone?: string
  address?: OrganizationAddress
  tax_id?: string
  registration_number?: string
  logo_url?: string
}

export type MembershipStatus = 'active' | 'suspended' | 'pending'

export interface OrganizationMember {
  id: string
  user_id: string
  organization_id: string
  email: string
  full_name: string
  org_role: OrgRole
  status: MembershipStatus
  is_primary: boolean
  joined_at: string
  last_active_at?: string
  invited_by?: string
}

export interface MembershipCreate {
  user_id: string
  org_role: OrgRole
}

export interface MembershipUpdate {
  org_role?: OrgRole
  status?: MembershipStatus
}

export interface MemberListResponse {
  items: OrganizationMember[]
  total: number
  page: number
  limit: number
  pages: number
}
