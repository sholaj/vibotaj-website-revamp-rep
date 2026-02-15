/**
 * TraceHub API Client
 *
 * Production-ready API client with:
 * - Automatic retry logic for transient failures
 * - Token refresh handling
 * - Request/response interceptors
 * - Proper error handling
 * - Request timeout configuration
 * - In-memory caching for GET requests
 */

import axios, {
  AxiosInstance,
  AxiosError,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  Shipment,
  ShipmentCreateRequest,
  Document,
  LiveTracking,
  ComplianceStatus,
  User,
  CurrentUser,
  UserCreate,
  UserUpdate,
  UserResponse,
  UserListResponse,
  RolesResponse,
  PermissionsResponse,
  ContainerStatusResponse,
  ShipmentEventsResponse,
  ShipmentDocumentsResponse,
  TrackingRefreshResponse,
  ShipmentDetailResponse,
  DocumentType,
  ApiError,
  DocumentValidationResponse,
  DocumentTransitionsResponse,
  TransitionResponse,
  ExpiringDocumentsResponse,
  DocumentRequirementsResponse,
  WorkflowSummaryResponse,
  NotificationListResponse,
  UnreadCountResponse,
  DashboardStats,
  ShipmentStats,
  ShipmentTrendsResponse,
  DocumentStats,
  DocumentDistributionResponse,
  ComplianceMetrics,
  TrackingStats,
  RecentActivityResponse,
  HealthStatus,
  EUDRStatusResponse,
  EUDRValidationResponse,
  EUDROriginVerificationRequest,
  EUDROriginValidationResponse,
  EUDRRiskAssessment,
  EUDRGeolocationCheckRequest,
  EUDRGeolocationCheckResponse,
  EUDRProductionDateCheckRequest,
  EUDRProductionDateCheckResponse,
  EUDRCountryRiskLevels,
  EUDRRegulationInfo,
  UserRole,
  BuyerOrganization,
  Organization,
  OrganizationCreate,
  OrganizationUpdate,
  OrganizationListResponse,
  OrganizationDeleteResponse,
  OrganizationMember,
  MembershipCreate,
  MembershipUpdate,
  MemberListResponse,
  OrgRole,
  // Invitation types
  InvitationStatus,
  InvitationCreateRequest,
  InvitationCreateResponse,
  InvitationListResponse,
  ResendInvitationResponse,
  // Invitation acceptance types (public endpoints)
  InvitationAcceptInfo,
  AcceptInvitationRequest,
  AcceptedInvitationResponse,
  // Bill of Lading compliance types
  BolParseResponse,
  BolComplianceResponse,
  BolComplianceResultsResponse,
  BolSyncPreviewResponse,
  BolSyncResponse,
  // Shipment validation rules engine types
  ShipmentValidationReport,
  ValidationRulesResponse,
  ValidationOverrideRequest,
  // Document validation issue types
  DocumentIssuesResponse,
  IssueOverrideResponse,
  DocumentVersionsResponse,
  SetPrimaryVersionResponse,
  // Document deletion and audit status types
  DocumentDeleteRequest,
  DocumentDeleteResponse,
  ShipmentAuditStatusResponse,
  // User deletion types
  UserDeleteRequest,
  UserDeleteResponse,
  UserRestoreResponse,
  DeletedUsersListResponse,
} from '../types'

// ============================================
// Configuration
// ============================================

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'
const REQUEST_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second base delay
const CACHE_TTL = 60000 // 1 minute cache TTL

// HTTP status codes that should trigger a retry
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]

// ============================================
// Cache Implementation
// ============================================

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

class SimpleCache {
  private cache: Map<string, CacheEntry<unknown>> = new Map()

  set<T>(key: string, data: T, ttl: number = CACHE_TTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    })
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null

    const isExpired = Date.now() - entry.timestamp > entry.ttl
    if (isExpired) {
      this.cache.delete(key)
      return null
    }

    return entry.data as T
  }

  invalidate(pattern?: string): void {
    if (!pattern) {
      this.cache.clear()
      return
    }

    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key)
      }
    }
  }

  invalidateByKey(key: string): void {
    this.cache.delete(key)
  }
}

// ============================================
// Error Classes
// ============================================

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string,
    public originalError?: Error
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

export class AuthenticationError extends ApiClientError {
  constructor(message: string = 'Authentication failed') {
    super(message, 401)
    this.name = 'AuthenticationError'
  }
}

export class NetworkError extends ApiClientError {
  constructor(message: string = 'Network error') {
    super(message, 0)
    this.name = 'NetworkError'
  }
}

// ============================================
// Token Management — PropelAuth (PRD-008)
// ============================================
// v1 JWT localStorage tokens replaced by PropelAuth SDK tokens.
// Token retrieval is async via auth-bridge.ts.

import { getAccessToken } from './auth-bridge'

// Keep a synchronous cache of the last-known token for the interceptor.
// Updated by the async token refresh in the response interceptor.
let _cachedToken: string | null = null

/**
 * Update the cached token (called from AuthContext on PropelAuth state change).
 */
export function setCachedToken(token: string | null): void {
  _cachedToken = token
}

// ============================================
// Retry Logic
// ============================================

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function shouldRetry(error: AxiosError, retryCount: number): boolean {
  if (retryCount >= MAX_RETRIES) return false

  // Network errors
  if (!error.response) return true

  // Retryable HTTP status codes
  if (RETRYABLE_STATUS_CODES.includes(error.response.status)) return true

  return false
}

function getRetryDelay(retryCount: number): number {
  // Exponential backoff with jitter
  const exponentialDelay = RETRY_DELAY * Math.pow(2, retryCount)
  const jitter = Math.random() * 1000
  return Math.min(exponentialDelay + jitter, 30000) // Cap at 30 seconds
}

// ============================================
// API Client Class
// ============================================

class ApiClient {
  private client: AxiosInstance
  private cache: SimpleCache

  constructor() {
    this.cache = new SimpleCache()
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: REQUEST_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    // Request interceptor - add PropelAuth token (PRD-008)
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (_cachedToken) {
          config.headers.Authorization = `Bearer ${_cachedToken}`
        }

        // Log request in development
        if (import.meta.env.DEV) {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
        }

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => {
        // Log response in development
        if (import.meta.env.DEV) {
          console.log(`[API] Response ${response.status} from ${response.config.url}`)
        }
        return response
      },
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

        // Handle 401 - Unauthorized (PropelAuth token expired/invalid)
        if (error.response?.status === 401 && !originalRequest._retry) {
          _cachedToken = null
          this.cache.invalidate()

          // Try to refresh the PropelAuth token asynchronously
          try {
            const newToken = await getAccessToken()
            if (newToken) {
              _cachedToken = newToken
              originalRequest._retry = true
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              return this.client(originalRequest)
            }
          } catch {
            // Token refresh failed — PropelAuth will handle redirect
          }

          return Promise.reject(new AuthenticationError())
        }

        // Handle network errors
        if (!error.response) {
          return Promise.reject(
            new NetworkError('Unable to connect to the server. Please check your internet connection.')
          )
        }

        // Format error message - handle both string and array/object detail
        const detail = error.response.data?.detail as unknown
        let errorMessage: string
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          // FastAPI validation errors return an array of {loc, msg, type}
          // Include field name for better UX: "field_name: error message"
          errorMessage = detail.map((e: { loc?: string[]; msg?: string }) => {
            const field = e.loc?.slice(-1)[0] // Get last element (field name)
            const msg = e.msg || 'Validation error'
            return field && field !== '__root__' ? `${field}: ${msg}` : msg
          }).join(', ')
        } else if (detail && typeof detail === 'object') {
          errorMessage = JSON.stringify(detail)
        } else {
          errorMessage = error.message || 'An unexpected error occurred'
        }
        return Promise.reject(
          new ApiClientError(errorMessage, error.response.status, typeof detail === 'string' ? detail : errorMessage)
        )
      }
    )
  }

  /**
   * Execute request with retry logic
   */
  private async executeWithRetry<T>(
    config: AxiosRequestConfig,
    retryCount: number = 0
  ): Promise<T> {
    try {
      const response = await this.client.request<T>(config)
      return response.data
    } catch (error) {
      if (error instanceof AxiosError && shouldRetry(error, retryCount)) {
        const delay = getRetryDelay(retryCount)
        console.warn(`[API] Retrying request (attempt ${retryCount + 1}/${MAX_RETRIES}) after ${delay}ms`)
        await sleep(delay)
        return this.executeWithRetry<T>(config, retryCount + 1)
      }
      throw error
    }
  }

  /**
   * Execute GET request with caching
   */
  private async cachedGet<T>(url: string, ttl: number = CACHE_TTL): Promise<T> {
    const cacheKey = `GET:${url}`
    const cached = this.cache.get<T>(cacheKey)

    if (cached) {
      if (import.meta.env.DEV) {
        console.log(`[API] Cache hit for ${url}`)
      }
      return cached
    }

    const data = await this.executeWithRetry<T>({ method: 'GET', url })
    this.cache.set(cacheKey, data, ttl)
    return data
  }

  // ============================================
  // Authentication Methods
  // ============================================

  /**
   * Login is now handled by PropelAuth (redirect-based).
   * This method is kept for backward compatibility but is a no-op.
   * The token comes from PropelAuth SDK, not from this endpoint.
   *
   * @deprecated Use PropelAuth login flow instead (PRD-008)
   */
  async login(_credentials: LoginRequest): Promise<LoginResponse> {
    throw new Error(
      'Direct login is disabled. Use PropelAuth login flow instead.'
    )
  }

  async getCurrentUser(): Promise<User> {
    return this.cachedGet<User>('auth/me', 5 * 60 * 1000) // 5 minute cache
  }

  async getCurrentUserFull(): Promise<CurrentUser> {
    return this.cachedGet<CurrentUser>('/auth/me/full', 5 * 60 * 1000) // 5 minute cache
  }

  async getMyPermissions(): Promise<PermissionsResponse> {
    return this.cachedGet<PermissionsResponse>('/auth/permissions', 5 * 60 * 1000)
  }

  async verifyToken(): Promise<boolean> {
    try {
      await this.getCurrentUser()
      return true
    } catch {
      return false
    }
  }

  logout(): void {
    _cachedToken = null
    this.cache.invalidate()
  }

  isAuthenticated(): boolean {
    return !!_cachedToken
  }

  // ============================================
  // Shipment Methods
  // ============================================

  async getShipments(): Promise<Shipment[]> {
    return this.cachedGet<Shipment[]>('shipments')
  }

  async getShipment(id: string): Promise<ShipmentDetailResponse> {
    return this.cachedGet<ShipmentDetailResponse>(`shipments/${id}`)
  }

  async getShipmentBasic(id: string): Promise<Shipment> {
    const response = await this.getShipment(id)
    return response.shipment
  }

  /**
   * Create a new shipment
   */
  async createShipment(data: ShipmentCreateRequest): Promise<Shipment> {
    const response = await this.client.post<Shipment>('shipments', data)
    this.cache.invalidate('shipments')
    return response.data
  }

  /**
   * Update an existing shipment
   */
  async updateShipment(id: string, data: Partial<ShipmentCreateRequest>): Promise<Shipment> {
    const response = await this.client.patch<Shipment>(`shipments/${id}`, data)
    this.cache.invalidate('shipments')
    this.cache.invalidate(`shipments/${id}`)
    return response.data
  }

  /**
   * Update shipment container number (typically from AI-extracted Bill of Lading data)
   */
  async updateShipmentContainer(shipmentId: string, containerNumber: string): Promise<Shipment> {
    const response = await this.client.patch<Shipment>(`shipments/${shipmentId}/container`, {
      container_number: containerNumber,
    })
    this.cache.invalidate('shipments')
    this.cache.invalidate(`shipments/${shipmentId}`)
    return response.data
  }

  /**
   * Delete a shipment (admin only)
   */
  async deleteShipment(id: string): Promise<void> {
    await this.client.delete(`shipments/${id}`)
    this.cache.invalidate('shipments')
  }

  // ============================================
  // Organization Methods
  // ============================================

  /**
   * Get list of buyer organizations for dropdown
   */
  async getBuyerOrganizations(): Promise<BuyerOrganization[]> {
    return this.cachedGet<BuyerOrganization[]>('organizations/buyers', 5 * 60 * 1000)
  }

  /**
   * Get paginated list of all organizations (admin only)
   */
  async getOrganizations(params?: {
    page?: number
    limit?: number
    type?: string
    status?: string
    search?: string
  }): Promise<OrganizationListResponse> {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.type) queryParams.append('type', params.type)
    if (params?.status) queryParams.append('status', params.status)
    if (params?.search) queryParams.append('search', params.search)

    const queryString = queryParams.toString()
    const url = queryString ? `organizations?${queryString}` : 'organizations'

    const response = await this.client.get<OrganizationListResponse>(url)
    return response.data
  }

  /**
   * Get organization details by ID (admin only)
   */
  async getOrganization(id: string): Promise<Organization> {
    const response = await this.client.get<Organization>(`organizations/${id}`)
    return response.data
  }

  /**
   * Create a new organization (admin only)
   */
  async createOrganization(data: OrganizationCreate): Promise<Organization> {
    const response = await this.client.post<Organization>('organizations', data)
    this.cache.invalidate('organizations')
    this.cache.invalidate('organizations/buyers')
    return response.data
  }

  /**
   * Update an organization (admin only)
   */
  async updateOrganization(id: string, data: OrganizationUpdate): Promise<Organization> {
    const response = await this.client.patch<Organization>(`organizations/${id}`, data)
    this.cache.invalidate('organizations')
    this.cache.invalidate(`organizations/${id}`)
    return response.data
  }

  /**
   * Delete (soft) an organization (admin only)
   * Sets organization status to 'suspended' and deactivates all memberships
   * @param id - The organization ID
   * @param reason - Required reason for deletion (min 10 chars)
   */
  async deleteOrganization(id: string, reason: string): Promise<OrganizationDeleteResponse> {
    const response = await this.client.delete<OrganizationDeleteResponse>(
      `organizations/${id}?reason=${encodeURIComponent(reason)}`
    )
    this.cache.invalidate('organizations')
    this.cache.invalidate(`organizations/${id}`)
    this.cache.invalidate('organizations/buyers')
    return response.data
  }

  /**
   * Get members of an organization (admin only)
   */
  async getOrganizationMembers(orgId: string, params?: {
    page?: number
    limit?: number
  }): Promise<MemberListResponse> {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())

    const queryString = queryParams.toString()
    const url = queryString ? `organizations/${orgId}/members?${queryString}` : `organizations/${orgId}/members`

    const response = await this.client.get<MemberListResponse>(url)
    return response.data
  }

  /**
   * Add a user to an organization (admin only)
   */
  async addOrganizationMember(orgId: string, data: MembershipCreate): Promise<OrganizationMember> {
    const response = await this.client.post<OrganizationMember>(`organizations/${orgId}/members`, data)
    this.cache.invalidate(`organizations/${orgId}`)
    return response.data
  }

  /**
   * Update a member's role or status (admin only)
   */
  async updateOrganizationMember(
    orgId: string,
    userId: string,
    data: MembershipUpdate
  ): Promise<OrganizationMember> {
    const response = await this.client.patch<OrganizationMember>(
      `organizations/${orgId}/members/${userId}`,
      data
    )
    return response.data
  }

  /**
   * Remove a user from an organization (admin only)
   */
  async removeOrganizationMember(orgId: string, userId: string): Promise<void> {
    await this.client.delete(`organizations/${orgId}/members/${userId}`)
    this.cache.invalidate(`organizations/${orgId}`)
  }

  // ============================================
  // Document Methods
  // ============================================

  async getShipmentDocuments(shipmentId: string): Promise<ShipmentDocumentsResponse> {
    return this.cachedGet<ShipmentDocumentsResponse>(`shipments/${shipmentId}/documents`)
  }

  async uploadDocument(
    shipmentId: string,
    file: File,
    documentType: DocumentType,
    metadata?: {
      reference_number?: string
      document_date?: string  // TICKET-002: Renamed from issue_date
      expiry_date?: string
      issuer?: string  // TICKET-002: Renamed from issuing_authority
      auto_detect?: boolean
    }
  ): Promise<Document> {
    const formData = new FormData()
    formData.append('shipment_id', shipmentId)
    formData.append('file', file)
    formData.append('document_type', documentType)

    // Enable auto-detection if explicitly requested or if document type is "other"
    const autoDetect = metadata?.auto_detect ?? (documentType === 'other')
    formData.append('auto_detect', autoDetect.toString())

    if (metadata?.reference_number) {
      formData.append('reference_number', metadata.reference_number)
    }
    if (metadata?.document_date) {
      formData.append('document_date', metadata.document_date)
    }
    if (metadata?.expiry_date) {
      formData.append('expiry_date', metadata.expiry_date)
    }
    if (metadata?.issuer) {
      formData.append('issuer', metadata.issuer)
    }

    const response = await this.client.post<Document>('documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 minutes for large file uploads with OCR processing
    })

    // Invalidate shipment document cache
    this.cache.invalidate(`shipments/${shipmentId}`)

    return response.data
  }

  /**
   * Download a document. Returns a signed URL (Supabase Storage) or falls back to blob.
   * PRD-008: Updated for Supabase Storage signed URLs.
   */
  async downloadDocument(documentId: string): Promise<string | Blob> {
    // Try JSON response first (signed URL from Supabase Storage)
    try {
      const response = await this.client.get(`documents/${documentId}/download`)
      if (response.data?.url) {
        return response.data.url as string
      }
    } catch {
      // Fall through to blob download
    }
    // Fallback: blob download (v1 local file storage)
    const response = await this.client.get(`documents/${documentId}/download`, {
      responseType: 'blob',
    })
    return response.data
  }

  async validateDocument(documentId: string, notes?: string): Promise<{ message: string; status: string }> {
    const response = await this.client.patch(`documents/${documentId}/validate`, { notes })

    // Invalidate related caches
    this.cache.invalidate('shipments')

    return response.data
  }

  async deleteDocument(documentId: string, reason: string): Promise<DocumentDeleteResponse> {
    const response = await this.client.delete(`documents/${documentId}`, {
      data: { reason } as DocumentDeleteRequest,
    })

    // Invalidate related caches
    this.cache.invalidate('shipments')

    return response.data
  }

  async deleteAllShipmentDocuments(
    shipmentId: string
  ): Promise<{ message: string; deleted_count: number }> {
    const response = await this.client.delete(
      `documents/shipment/${shipmentId}/all`
    )

    // Invalidate related caches
    this.cache.invalidate('shipments')

    return response.data
  }

  // ============================================
  // Document Workflow Methods
  // ============================================

  async getDocumentValidation(documentId: string): Promise<DocumentValidationResponse> {
    return this.executeWithRetry<DocumentValidationResponse>({
      method: 'GET',
      url: `documents/${documentId}/validation`,
    })
  }

  async getDocumentTransitions(documentId: string): Promise<DocumentTransitionsResponse> {
    return this.executeWithRetry<DocumentTransitionsResponse>({
      method: 'GET',
      url: `documents/${documentId}/transitions`,
    })
  }

  async transitionDocument(
    documentId: string,
    targetStatus: string,
    notes?: string
  ): Promise<TransitionResponse> {
    const response = await this.client.post(`documents/${documentId}/transition`, {
      target_status: targetStatus,
      notes,
    })

    // Invalidate related caches
    this.cache.invalidate('shipments')
    this.cache.invalidate('documents')

    return response.data
  }

  async approveDocument(documentId: string, notes?: string): Promise<TransitionResponse> {
    const response = await this.client.post(`documents/${documentId}/approve`, { notes })

    this.cache.invalidate('shipments')
    this.cache.invalidate('documents')

    return response.data
  }

  async rejectDocument(documentId: string, notes: string): Promise<TransitionResponse> {
    const response = await this.client.post(`documents/${documentId}/reject`, { notes })

    this.cache.invalidate('shipments')
    this.cache.invalidate('documents')

    return response.data
  }

  async updateDocumentMetadata(
    documentId: string,
    metadata: {
      reference_number?: string
      document_date?: string  // TICKET-002: Renamed from issue_date
      expiry_date?: string
      issuer?: string  // TICKET-002: Renamed from issuing_authority
      extra_data?: Record<string, unknown>
    }
  ): Promise<{ message: string; document_id: string }> {
    const response = await this.client.patch(`documents/${documentId}/metadata`, metadata)

    this.cache.invalidate('shipments')
    this.cache.invalidate('documents')

    return response.data
  }

  async getExpiringDocuments(days: number = 30, shipmentId?: string): Promise<ExpiringDocumentsResponse> {
    const params = new URLSearchParams({ days: days.toString() })
    if (shipmentId) {
      params.append('shipment_id', shipmentId)
    }

    return this.executeWithRetry<ExpiringDocumentsResponse>({
      method: 'GET',
      url: `documents/expiring?${params.toString()}`,
    })
  }

  async getDocumentTypeRequirements(documentType: string): Promise<DocumentRequirementsResponse> {
    return this.cachedGet<DocumentRequirementsResponse>(
      `documents/types/${documentType}/requirements`,
      5 * 60 * 1000 // 5 minute cache
    )
  }

  async getWorkflowSummary(shipmentId: string): Promise<WorkflowSummaryResponse> {
    return this.executeWithRetry<WorkflowSummaryResponse>({
      method: 'GET',
      url: `documents/workflow/summary?shipment_id=${shipmentId}`,
    })
  }

  // ============================================
  // Document Validation Issues Methods
  // PRP: Document Validation & Compliance Enhancement
  // ============================================

  /**
   * Get validation issues for a document
   */
  async getDocumentIssues(documentId: string): Promise<DocumentIssuesResponse> {
    return this.executeWithRetry<DocumentIssuesResponse>({
      method: 'GET',
      url: `documents/${documentId}/issues`,
    })
  }

  /**
   * Override a validation issue with a reason
   */
  async overrideDocumentIssue(
    documentId: string,
    issueId: string,
    reason: string
  ): Promise<IssueOverrideResponse> {
    const response = await this.client.post(
      `documents/${documentId}/issues/${issueId}/override`,
      { reason }
    )

    // Invalidate related caches
    this.cache.invalidate('shipments')
    this.cache.invalidate('documents')

    return response.data
  }

  /**
   * Get all versions of a document (for duplicate handling)
   */
  async getDocumentVersions(
    shipmentId: string,
    documentType: string
  ): Promise<DocumentVersionsResponse> {
    return this.executeWithRetry<DocumentVersionsResponse>({
      method: 'GET',
      url: `shipments/${shipmentId}/documents/versions?document_type=${documentType}`,
    })
  }

  /**
   * Set a specific document version as primary
   */
  async setPrimaryDocumentVersion(
    documentId: string
  ): Promise<SetPrimaryVersionResponse> {
    const response = await this.client.post(
      `documents/${documentId}/set-primary`
    )

    // Invalidate related caches
    this.cache.invalidate('shipments')
    this.cache.invalidate('documents')

    return response.data
  }

  // ============================================
  // Document Contents Methods (Multi-Document PDFs)
  // ============================================

  /**
   * Get document contents (individual documents within a combined PDF)
   */
  async getDocumentContents(documentId: string): Promise<{
    document_id: string
    file_name: string
    is_combined: boolean
    page_count: number
    content_count: number
    contents: Array<{
      id: string
      document_type: string
      status: string
      page_start: number
      page_end: number
      reference_number?: string
      confidence: number
      detection_method: string
      validated_at?: string
      validated_by?: string
      validation_notes?: string
      detected_fields?: Record<string, unknown>
    }>
  }> {
    return this.executeWithRetry({
      method: 'GET',
      url: `documents/${documentId}/contents`,
    })
  }

  /**
   * Validate a specific content within a combined PDF
   */
  async validateDocumentContent(
    documentId: string,
    contentId: string,
    notes?: string
  ): Promise<{ message: string; content_id: string; status: string; all_contents_validated: boolean }> {
    const response = await this.client.post(`documents/${documentId}/contents/${contentId}/validate`, notes)
    this.cache.invalidate('documents')
    this.cache.invalidate('shipments')
    return response.data
  }

  /**
   * Reject a specific content within a combined PDF
   */
  async rejectDocumentContent(
    documentId: string,
    contentId: string,
    notes: string
  ): Promise<{ message: string; content_id: string; status: string }> {
    const response = await this.client.post(`documents/${documentId}/contents/${contentId}/reject`, { notes })
    this.cache.invalidate('documents')
    this.cache.invalidate('shipments')
    return response.data
  }

  /**
   * Analyze a document to detect contained document types
   */
  async analyzeDocument(documentId: string): Promise<{
    document_id: string
    file_name: string
    page_count: number
    detected_sections: Array<{
      document_type: string
      page_start: number
      page_end: number
      reference_number?: string
      confidence: number
      detection_method: string
      detected_fields?: Record<string, unknown>
    }>
    ai_available: boolean
  }> {
    return this.executeWithRetry({
      method: 'GET',
      url: `documents/${documentId}/analyze`,
    })
  }

  /**
   * Check for duplicate documents in a shipment
   */
  async getShipmentDuplicates(shipmentId: string): Promise<{
    shipment_id: string
    total_references: number
    duplicate_count: number
    duplicates: Array<{
      reference_number: string
      document_type: string
      occurrences: Array<{
        document_id: string
        content_id?: string
        first_seen_at?: string
      }>
    }>
  }> {
    return this.executeWithRetry({
      method: 'GET',
      url: `documents/shipments/${shipmentId}/duplicates`,
    })
  }

  /**
   * Generic GET method for components
   */
  async get<T>(url: string): Promise<T> {
    return this.executeWithRetry<T>({ method: 'GET', url })
  }

  /**
   * Generic POST method for components
   */
  async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  // ============================================
  // Compliance Methods
  // ============================================

  async getComplianceStatus(shipmentId: string): Promise<ComplianceStatus> {
    // Compliance status is part of shipment detail, extract it
    const detail = await this.getShipment(shipmentId)
    return {
      is_compliant: detail.document_summary.is_complete,
      total_required: detail.document_summary.total_required,
      total_present: detail.document_summary.total_uploaded,
      missing_documents: detail.document_summary.missing,
      pending_validation: [],
      issues: [],
    }
  }

  // ============================================
  // Bill of Lading Compliance Methods
  // ============================================

  /**
   * Parse a Bill of Lading document and extract structured data.
   * Optionally sync the extracted data to the shipment.
   */
  async parseBol(
    documentId: string,
    autoSyncShipment: boolean = false
  ): Promise<BolParseResponse> {
    const response = await this.client.post<BolParseResponse>(
      `documents/${documentId}/bol/parse?auto_sync_shipment=${autoSyncShipment}`
    )
    this.cache.invalidate('documents')
    this.cache.invalidate('shipments')
    return response.data
  }

  /**
   * Run compliance checks on a Bill of Lading document.
   * Returns compliance decision: APPROVE, HOLD, or REJECT.
   */
  async checkBolCompliance(
    documentId: string,
    options: {
      storeResults?: boolean
      autoSyncShipment?: boolean
    } = {}
  ): Promise<BolComplianceResponse> {
    const { storeResults = true, autoSyncShipment = false } = options
    const params = new URLSearchParams()
    params.append('store_results', storeResults.toString())
    params.append('auto_sync_shipment', autoSyncShipment.toString())

    const response = await this.client.post<BolComplianceResponse>(
      `documents/${documentId}/bol/check-compliance?${params.toString()}`
    )
    this.cache.invalidate('documents')
    this.cache.invalidate('shipments')
    return response.data
  }

  /**
   * Get stored compliance results for a Bill of Lading document.
   */
  async getBolComplianceResults(documentId: string): Promise<BolComplianceResultsResponse> {
    return this.executeWithRetry<BolComplianceResultsResponse>({
      method: 'GET',
      url: `documents/${documentId}/bol/compliance-results`,
    })
  }

  /**
   * Preview what changes would be made to the shipment from BoL data.
   */
  async previewBolSync(documentId: string): Promise<BolSyncPreviewResponse> {
    return this.executeWithRetry<BolSyncPreviewResponse>({
      method: 'GET',
      url: `documents/${documentId}/bol/sync-preview`,
    })
  }

  /**
   * Sync BoL data to the shipment.
   */
  async syncBolToShipment(documentId: string): Promise<BolSyncResponse> {
    const response = await this.client.post<BolSyncResponse>(
      `documents/${documentId}/bol/sync`
    )
    this.cache.invalidate('documents')
    this.cache.invalidate('shipments')
    return response.data
  }

  // ============================================
  // Container Tracking Methods
  // ============================================

  async getContainerStatus(containerNumber: string): Promise<ContainerStatusResponse> {
    return this.cachedGet<ContainerStatusResponse>(
      `tracking/status/${encodeURIComponent(containerNumber)}`,
      30000 // 30 second cache for tracking data
    )
  }

  async getLiveTracking(containerNumber: string, shippingLine?: string): Promise<LiveTracking> {
    let url = `tracking/live/${encodeURIComponent(containerNumber)}`
    if (shippingLine) {
      url += `?shipping_line=${encodeURIComponent(shippingLine)}`
    }

    // Short cache for live tracking
    return this.cachedGet<LiveTracking>(url, 30000)
  }

  async getTrackingByBol(blNumber: string, shippingLine: string): Promise<LiveTracking> {
    return this.executeWithRetry<LiveTracking>({
      method: 'GET',
      url: `tracking/bol/${encodeURIComponent(blNumber)}`,
      params: { shipping_line: shippingLine },
    })
  }

  async refreshTracking(shipmentId: string): Promise<TrackingRefreshResponse> {
    const response = await this.client.post<TrackingRefreshResponse>(
      `tracking/refresh/${shipmentId}`
    )

    // Invalidate tracking caches
    this.cache.invalidate('tracking')
    this.cache.invalidate(`shipments/${shipmentId}`)

    return response.data
  }

  // ============================================
  // Container Events Methods
  // ============================================

  async getContainerEvents(shipmentId: string): Promise<ShipmentEventsResponse> {
    return this.cachedGet<ShipmentEventsResponse>(`shipments/${shipmentId}/events`)
  }

  // ============================================
  // Audit Pack Methods
  // ============================================

  /**
   * Download audit pack. Returns signed URL or blob.
   * PRD-008: Updated for Supabase Storage signed URLs.
   */
  async downloadAuditPack(shipmentId: string): Promise<string | Blob> {
    try {
      const response = await this.client.get(`shipments/${shipmentId}/audit-pack`)
      if (response.data?.url) {
        return response.data.url as string
      }
    } catch {
      // Fall through to blob download
    }
    const response = await this.client.get(`shipments/${shipmentId}/audit-pack`, {
      responseType: 'blob',
    })
    return response.data
  }

  /**
   * Get document audit pack inclusion status for a shipment.
   * Shows which documents will be included in the audit pack download.
   */
  async getShipmentAuditStatus(shipmentId: string): Promise<ShipmentAuditStatusResponse> {
    return this.executeWithRetry<ShipmentAuditStatusResponse>({
      method: 'GET',
      url: `documents/shipment/${shipmentId}/audit-status`,
    })
  }

  // ============================================
  // API Usage Methods
  // ============================================

  async getApiUsage(): Promise<{ used: number; limit: number; reset_date: string } | null> {
    try {
      return await this.cachedGet('tracking/usage', 5 * 60 * 1000)
    } catch {
      return null
    }
  }

  // ============================================
  // Notification Methods
  // ============================================

  async getNotifications(
    unreadOnly: boolean = false,
    limit: number = 50,
    offset: number = 0
  ): Promise<NotificationListResponse> {
    const params = new URLSearchParams({
      unread_only: unreadOnly.toString(),
      limit: limit.toString(),
      offset: offset.toString(),
    })
    return this.executeWithRetry<NotificationListResponse>({
      method: 'GET',
      url: `notifications?${params.toString()}`,
    })
  }

  async getUnreadNotificationCount(): Promise<number> {
    const response = await this.executeWithRetry<UnreadCountResponse>({
      method: 'GET',
      url: 'notifications/unread-count',
    })
    return response.unread_count
  }

  async markNotificationRead(notificationId: string): Promise<void> {
    await this.client.patch(`notifications/${notificationId}/read`)
  }

  async markAllNotificationsRead(): Promise<{ marked_count: number }> {
    const response = await this.client.post('notifications/read-all')
    return response.data
  }

  async deleteNotification(notificationId: string): Promise<void> {
    await this.client.delete(`notifications/${notificationId}`)
  }

  // ============================================
  // Analytics Methods
  // ============================================

  async getDashboardStats(): Promise<DashboardStats> {
    return this.cachedGet<DashboardStats>('analytics/dashboard', 60000) // 1 minute cache
  }

  async getShipmentStats(): Promise<ShipmentStats> {
    return this.cachedGet<ShipmentStats>('analytics/shipments', 60000)
  }

  async getShipmentTrends(days: number = 30, groupBy: string = 'day'): Promise<ShipmentTrendsResponse> {
    return this.cachedGet<ShipmentTrendsResponse>(
      `analytics/shipments/trends?days=${days}&group_by=${groupBy}`,
      60000
    )
  }

  async getDocumentStats(): Promise<DocumentStats> {
    return this.cachedGet<DocumentStats>('analytics/documents', 60000)
  }

  async getDocumentDistribution(): Promise<DocumentDistributionResponse> {
    return this.cachedGet<DocumentDistributionResponse>('analytics/documents/distribution', 60000)
  }

  async getComplianceMetrics(): Promise<ComplianceMetrics> {
    return this.cachedGet<ComplianceMetrics>('analytics/compliance', 60000)
  }

  async getTrackingStats(): Promise<TrackingStats> {
    return this.cachedGet<TrackingStats>('analytics/tracking', 60000)
  }

  async getRecentActivity(limit: number = 20): Promise<RecentActivityResponse> {
    return this.cachedGet<RecentActivityResponse>(
      `audit-log/recent?limit=${limit}`,
      30000 // 30 second cache for activity
    )
  }

  async getHealthStatus(): Promise<HealthStatus> {
    // Health check doesn't require auth, so use a direct call
    const response = await this.client.get<HealthStatus>('health')
    return response.data
  }

  // ============================================
  // EUDR Compliance Methods
  // ============================================

  /**
   * Get EUDR compliance status for a shipment
   */
  async getEUDRStatus(shipmentId: string): Promise<EUDRStatusResponse> {
    return this.cachedGet<EUDRStatusResponse>(
      `eudr/shipment/${shipmentId}/status`,
      30000 // 30 second cache
    )
  }

  /**
   * Run full EUDR validation on a shipment
   */
  async validateEUDR(shipmentId: string): Promise<EUDRValidationResponse> {
    const response = await this.client.post<EUDRValidationResponse>(
      `eudr/shipment/${shipmentId}/validate`
    )

    // Invalidate status cache after validation
    this.cache.invalidate(`eudr/shipment/${shipmentId}`)

    return response.data
  }

  /**
   * Generate EUDR compliance report
   */
  async getEUDRReport(shipmentId: string, format: 'json' | 'pdf' = 'json'): Promise<unknown> {
    if (format === 'pdf') {
      const response = await this.client.get(`eudr/shipment/${shipmentId}/report?format=pdf`, {
        responseType: 'blob',
      })
      return response.data
    }

    return this.executeWithRetry<unknown>({
      method: 'GET',
      url: `eudr/shipment/${shipmentId}/report?format=json`,
    })
  }

  /**
   * Download EUDR report as PDF
   */
  /**
   * Download EUDR report as PDF. Returns signed URL or blob.
   * PRD-008: Updated for Supabase Storage signed URLs.
   */
  async downloadEUDRReport(shipmentId: string): Promise<string | Blob> {
    try {
      const response = await this.client.get(`eudr/shipment/${shipmentId}/report?format=pdf`)
      if (response.data?.url) {
        return response.data.url as string
      }
    } catch {
      // Fall through to blob download
    }
    const response = await this.client.get(`eudr/shipment/${shipmentId}/report?format=pdf`, {
      responseType: 'blob',
    })
    return response.data
  }

  /**
   * Verify origin data for EUDR compliance
   */
  async verifyOrigin(
    originId: string,
    verification?: EUDROriginVerificationRequest
  ): Promise<EUDROriginValidationResponse> {
    const response = await this.client.post<EUDROriginValidationResponse>(
      `eudr/origin/${originId}/verify`,
      verification
    )

    // Invalidate related caches
    this.cache.invalidate('eudr')

    return response.data
  }

  /**
   * Get deforestation risk assessment for an origin
   */
  async getOriginRisk(originId: string): Promise<EUDRRiskAssessment> {
    return this.cachedGet<EUDRRiskAssessment>(`eudr/origin/${originId}/risk`, 60000)
  }

  /**
   * Check if geolocation coordinates are valid and within country
   */
  async checkGeolocation(request: EUDRGeolocationCheckRequest): Promise<EUDRGeolocationCheckResponse> {
    const response = await this.client.post<EUDRGeolocationCheckResponse>(
      'eudr/check/geolocation',
      request
    )
    return response.data
  }

  /**
   * Check if production date meets EUDR requirements
   */
  async checkProductionDate(request: EUDRProductionDateCheckRequest): Promise<EUDRProductionDateCheckResponse> {
    const response = await this.client.post<EUDRProductionDateCheckResponse>(
      'eudr/check/production-date',
      request
    )
    return response.data
  }

  /**
   * Get country risk levels for EUDR
   */
  async getCountryRiskLevels(): Promise<EUDRCountryRiskLevels> {
    return this.cachedGet<EUDRCountryRiskLevels>('eudr/countries/risk-levels', 5 * 60 * 1000) // 5 min cache
  }

  /**
   * Get EUDR regulation information
   */
  async getEUDRRegulationInfo(): Promise<EUDRRegulationInfo> {
    return this.cachedGet<EUDRRegulationInfo>('eudr/regulation/info', 60 * 60 * 1000) // 1 hour cache
  }

  // ============================================
  // User Management Methods
  // ============================================

  /**
   * Get list of users (admin only)
   */
  async getUsers(params?: {
    page?: number
    limit?: number
    role?: UserRole
    is_active?: boolean
    search?: string
  }): Promise<UserListResponse> {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.role) queryParams.append('role', params.role)
    if (params?.is_active !== undefined) queryParams.append('is_active', params.is_active.toString())
    if (params?.search) queryParams.append('search', params.search)

    const url = `users?${queryParams.toString()}`
    return this.executeWithRetry<UserListResponse>({ method: 'GET', url })
  }

  /**
   * Get a single user by ID
   */
  async getUser(userId: string): Promise<UserResponse> {
    return this.executeWithRetry<UserResponse>({ method: 'GET', url: `users/${userId}` })
  }

  /**
   * Create a new user (admin only)
   */
  async createUser(user: UserCreate): Promise<UserResponse> {
    const response = await this.client.post<UserResponse>('users', user)
    this.cache.invalidate('users')
    return response.data
  }

  /**
   * Update a user
   */
  async updateUser(userId: string, update: UserUpdate): Promise<UserResponse> {
    const response = await this.client.patch<UserResponse>(`users/${userId}`, update)
    this.cache.invalidate('users')
    return response.data
  }

  /**
   * Delete a user (soft or hard delete)
   * @param userId - The ID of the user to delete
   * @param reason - Required reason for deletion (10-500 chars)
   * @param hardDelete - If true, permanently delete the user
   */
  async deleteUser(
    userId: string,
    reason: string,
    hardDelete: boolean = false
  ): Promise<UserDeleteResponse> {
    const response = await this.client.request<UserDeleteResponse>({
      method: 'DELETE',
      url: `users/${userId}`,
      data: { reason, hard_delete: hardDelete } as UserDeleteRequest,
    })
    this.cache.invalidate('users')
    return response.data
  }

  /**
   * Restore a soft-deleted user
   */
  async restoreUser(userId: string): Promise<UserRestoreResponse> {
    const response = await this.client.post<UserRestoreResponse>(`users/${userId}/restore`)
    this.cache.invalidate('users')
    return response.data
  }

  /**
   * Get list of deleted users
   */
  async getDeletedUsers(params?: {
    limit?: number
    offset?: number
  }): Promise<DeletedUsersListResponse> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())

    const queryString = queryParams.toString()
    const url = queryString ? `users/deleted?${queryString}` : 'users/deleted'

    const response = await this.client.get<DeletedUsersListResponse>(url)
    return response.data
  }

  /**
   * Deactivate a user (legacy - use deleteUser for new code)
   * @deprecated Use deleteUser instead
   */
  async deactivateUser(userId: string): Promise<{ message: string }> {
    const response = await this.client.delete(`users/${userId}`, {
      data: { reason: 'Deactivated via legacy endpoint', hard_delete: false },
    })
    this.cache.invalidate('users')
    return { message: response.data.message || 'User deactivated successfully' }
  }

  /**
   * Activate a user
   */
  async activateUser(userId: string): Promise<{ message: string }> {
    const response = await this.client.post(`users/${userId}/activate`)
    this.cache.invalidate('users')
    return response.data
  }

  /**
   * Get available roles
   */
  async getRoles(): Promise<RolesResponse> {
    return this.cachedGet<RolesResponse>('users/roles', 5 * 60 * 1000) // 5 min cache
  }

  /**
   * Admin reset user password
   */
  async adminResetPassword(userId: string, newPassword: string): Promise<{ message: string }> {
    const response = await this.client.post(`users/${userId}/reset-password?new_password=${encodeURIComponent(newPassword)}`)
    return response.data
  }

  // ============================================
  // Invitation Management Methods
  // ============================================

  /**
   * Create an invitation to join an organization
   */
  async createInvitation(
    orgId: string,
    data: InvitationCreateRequest
  ): Promise<InvitationCreateResponse> {
    const response = await this.client.post<InvitationCreateResponse>(
      `invitations/organizations/${orgId}/invitations`,
      data
    )
    this.cache.invalidate(`invitations/organizations/${orgId}`)
    return response.data
  }

  /**
   * Get paginated list of invitations for an organization
   */
  async getInvitations(
    orgId: string,
    params?: { status?: InvitationStatus; limit?: number; offset?: number }
  ): Promise<InvitationListResponse> {
    const queryParams = new URLSearchParams()
    if (params?.status) queryParams.append('status', params.status)
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())

    const queryString = queryParams.toString()
    const url = queryString
      ? `invitations/organizations/${orgId}/invitations?${queryString}`
      : `invitations/organizations/${orgId}/invitations`

    const response = await this.client.get<InvitationListResponse>(url)
    return response.data
  }

  /**
   * Revoke a pending invitation
   */
  async revokeInvitation(orgId: string, invitationId: string): Promise<void> {
    await this.client.delete(
      `invitations/organizations/${orgId}/invitations/${invitationId}`
    )
    this.cache.invalidate(`invitations/organizations/${orgId}`)
  }

  /**
   * Resend an invitation with a new token
   */
  async resendInvitation(
    orgId: string,
    invitationId: string
  ): Promise<ResendInvitationResponse> {
    const response = await this.client.post<ResendInvitationResponse>(
      `invitations/organizations/${orgId}/invitations/${invitationId}/resend`
    )
    this.cache.invalidate(`invitations/organizations/${orgId}`)
    return response.data
  }

  /**
   * Update a member's role in an organization
   */
  async updateMemberRole(
    orgId: string,
    userId: string,
    data: { org_role: OrgRole }
  ): Promise<OrganizationMember> {
    const response = await this.client.patch<OrganizationMember>(
      `organizations/${orgId}/members/${userId}`,
      data
    )
    this.cache.invalidate(`organizations/${orgId}`)
    return response.data
  }

  /**
   * Remove a member from an organization
   */
  async removeMember(orgId: string, userId: string): Promise<void> {
    await this.client.delete(`organizations/${orgId}/members/${userId}`)
    this.cache.invalidate(`organizations/${orgId}`)
  }

  // ============================================
  // Invitation Acceptance Methods (Public - No Auth Required)
  // ============================================

  /**
   * Get invitation details by token (public endpoint - no auth required)
   * Used to display invitation info on the acceptance page.
   */
  async getInvitationByToken(token: string): Promise<InvitationAcceptInfo> {
    const response = await axios.get<InvitationAcceptInfo>(
      `${API_BASE_URL}/invitations/accept/${token}`
    )
    return response.data
  }

  /**
   * Accept an invitation (public endpoint - no auth required)
   * For new users: full_name and password are required.
   * For existing users: no additional data needed.
   * Returns an access_token for new users to auto-login.
   */
  async acceptInvitation(
    token: string,
    data?: AcceptInvitationRequest
  ): Promise<AcceptedInvitationResponse> {
    const response = await axios.post<AcceptedInvitationResponse>(
      `${API_BASE_URL}/invitations/accept/${token}`,
      data || {},
      {
        headers: { 'Content-Type': 'application/json' },
      }
    )

    // If new user with access token, update cached token for auto-login
    if (response.data.access_token) {
      setCachedToken(response.data.access_token)
      this.cache.invalidate()
    }

    return response.data
  }

  // ============================================
  // Shipment Validation Rules Engine Methods
  // ============================================

  /**
   * Get all available validation rules
   */
  async getValidationRules(): Promise<ValidationRulesResponse> {
    return this.cachedGet<ValidationRulesResponse>('validation/rules')
  }

  /**
   * Get validation rules filtered by product type
   */
  async getValidationRulesForProductType(
    productType: string
  ): Promise<ValidationRulesResponse> {
    return this.cachedGet<ValidationRulesResponse>(
      `validation/rules?product_type=${productType}`
    )
  }

  /**
   * Validate a shipment against all applicable rules
   */
  async validateShipment(shipmentId: string): Promise<ShipmentValidationReport> {
    const response = await this.client.post<ShipmentValidationReport>(
      `validation/shipments/${shipmentId}/validate`
    )
    this.cache.invalidate(`validation/shipments/${shipmentId}`)
    this.cache.invalidate(`shipments/${shipmentId}`)
    return response.data
  }

  /**
   * Get the latest validation report for a shipment
   */
  async getShipmentValidationReport(
    shipmentId: string
  ): Promise<ShipmentValidationReport | null> {
    try {
      return await this.cachedGet<ShipmentValidationReport>(
        `validation/shipments/${shipmentId}`
      )
    } catch (error) {
      // 404 means no validation report yet
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null
      }
      throw error
    }
  }

  /**
   * Override validation status for a shipment (admin only)
   */
  async overrideShipmentValidation(
    shipmentId: string,
    data: ValidationOverrideRequest
  ): Promise<ShipmentValidationReport> {
    const response = await this.client.post<ShipmentValidationReport>(
      `validation/shipments/${shipmentId}/override`,
      data
    )
    this.cache.invalidate(`validation/shipments/${shipmentId}`)
    this.cache.invalidate(`shipments/${shipmentId}`)
    return response.data
  }

  /**
   * Clear validation override for a shipment (admin only)
   */
  async clearValidationOverride(
    shipmentId: string
  ): Promise<ShipmentValidationReport> {
    const response = await this.client.delete<ShipmentValidationReport>(
      `validation/shipments/${shipmentId}/override`
    )
    this.cache.invalidate(`validation/shipments/${shipmentId}`)
    this.cache.invalidate(`shipments/${shipmentId}`)
    return response.data
  }

  // ============================================
  // Utility Methods
  // ============================================

  /**
   * Clear all cached data
   */
  clearCache(): void {
    this.cache.invalidate()
  }

  /**
   * Invalidate cache for a specific pattern
   */
  invalidateCache(pattern: string): void {
    this.cache.invalidate(pattern)
  }
}

// Export singleton instance
export const api = new ApiClient()
export default api

// Also export for testing/mocking
export { ApiClient }
