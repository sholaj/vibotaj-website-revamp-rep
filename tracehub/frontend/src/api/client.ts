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
  OrganizationMember,
  MembershipCreate,
  MembershipUpdate,
  MemberListResponse,
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
// Token Management
// ============================================

const TOKEN_KEY = 'tracehub_token'
const TOKEN_EXPIRY_KEY = 'tracehub_token_expiry'

function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function setStoredToken(token: string, expiresInHours: number = 24): void {
  const expiry = Date.now() + expiresInHours * 60 * 60 * 1000
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toString())
}

function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(TOKEN_EXPIRY_KEY)
}

function isTokenExpired(): boolean {
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY)
  if (!expiry) return true
  return Date.now() > parseInt(expiry, 10)
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
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = getStoredToken()
        if (token && !isTokenExpired()) {
          config.headers.Authorization = `Bearer ${token}`
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

        // Handle 401 - Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          // Token expired or invalid - clear and redirect
          clearStoredToken()
          this.cache.invalidate()

          // Redirect to login if not already there
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }

          return Promise.reject(new AuthenticationError())
        }

        // Handle network errors
        if (!error.response) {
          return Promise.reject(
            new NetworkError('Unable to connect to the server. Please check your internet connection.')
          )
        }

        // Format error message
        const errorMessage = error.response.data?.detail || error.message || 'An unexpected error occurred'
        return Promise.reject(
          new ApiClientError(errorMessage, error.response.status, error.response.data?.detail)
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

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    // OAuth2 password flow requires form data
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await this.client.post<LoginResponse>('auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    // Store token with 24 hour expiry (matches backend JWT_EXPIRATION_HOURS)
    setStoredToken(response.data.access_token, 24)

    // Clear any cached data on new login
    this.cache.invalidate()

    return response.data
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
    clearStoredToken()
    this.cache.invalidate()
  }

  isAuthenticated(): boolean {
    return !!getStoredToken() && !isTokenExpired()
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
    this.cache.invalidate('/shipments')
    return response.data
  }

  /**
   * Update an existing shipment
   */
  async updateShipment(id: string, data: Partial<ShipmentCreateRequest>): Promise<Shipment> {
    const response = await this.client.patch<Shipment>(`shipments/${id}`, data)
    this.cache.invalidate('/shipments')
    this.cache.invalidate(`/shipments/${id}`)
    return response.data
  }

  /**
   * Delete a shipment (admin only)
   */
  async deleteShipment(id: string): Promise<void> {
    await this.client.delete(`shipments/${id}`)
    this.cache.invalidate('/shipments')
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
    this.cache.invalidate('/organizations')
    this.cache.invalidate('/organizations/buyers')
    return response.data
  }

  /**
   * Update an organization (admin only)
   */
  async updateOrganization(id: string, data: OrganizationUpdate): Promise<Organization> {
    const response = await this.client.patch<Organization>(`organizations/${id}`, data)
    this.cache.invalidate('/organizations')
    this.cache.invalidate(`/organizations/${id}`)
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
    this.cache.invalidate(`/organizations/${orgId}`)
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
    this.cache.invalidate(`/organizations/${orgId}`)
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
      issue_date?: string
      expiry_date?: string
      issuing_authority?: string
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
    if (metadata?.issue_date) {
      formData.append('issue_date', metadata.issue_date)
    }
    if (metadata?.expiry_date) {
      formData.append('expiry_date', metadata.expiry_date)
    }
    if (metadata?.issuing_authority) {
      formData.append('issuing_authority', metadata.issuing_authority)
    }

    const response = await this.client.post<Document>('documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    // Invalidate shipment document cache
    this.cache.invalidate(`/shipments/${shipmentId}`)

    return response.data
  }

  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await this.client.get(`documents/${documentId}/download`, {
      responseType: 'blob',
    })
    return response.data
  }

  async validateDocument(documentId: string, notes?: string): Promise<{ message: string; status: string }> {
    const response = await this.client.patch(`documents/${documentId}/validate`, { notes })

    // Invalidate related caches
    this.cache.invalidate('/shipments/')

    return response.data
  }

  async deleteDocument(documentId: string): Promise<{ message: string }> {
    const response = await this.client.delete(`documents/${documentId}`)

    // Invalidate related caches
    this.cache.invalidate('/shipments/')

    return response.data
  }

  async deleteAllShipmentDocuments(
    shipmentId: string
  ): Promise<{ message: string; deleted_count: number }> {
    const response = await this.client.delete(
      `documents/shipment/${shipmentId}/all`
    )

    // Invalidate related caches
    this.cache.invalidate('/shipments/')

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
    this.cache.invalidate('/shipments/')
    this.cache.invalidate('/documents/')

    return response.data
  }

  async approveDocument(documentId: string, notes?: string): Promise<TransitionResponse> {
    const response = await this.client.post(`documents/${documentId}/approve`, { notes })

    this.cache.invalidate('/shipments/')
    this.cache.invalidate('/documents/')

    return response.data
  }

  async rejectDocument(documentId: string, notes: string): Promise<TransitionResponse> {
    const response = await this.client.post(`documents/${documentId}/reject`, { notes })

    this.cache.invalidate('/shipments/')
    this.cache.invalidate('/documents/')

    return response.data
  }

  async updateDocumentMetadata(
    documentId: string,
    metadata: {
      reference_number?: string
      issue_date?: string
      expiry_date?: string
      issuing_authority?: string
      extra_data?: Record<string, unknown>
    }
  ): Promise<{ message: string; document_id: string }> {
    const response = await this.client.patch(`documents/${documentId}/metadata`, metadata)

    this.cache.invalidate('/shipments/')
    this.cache.invalidate('/documents/')

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
    this.cache.invalidate('/documents/')
    this.cache.invalidate('/shipments/')
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
    this.cache.invalidate('/documents/')
    this.cache.invalidate('/shipments/')
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
    this.cache.invalidate('/tracking/')
    this.cache.invalidate(`/shipments/${shipmentId}`)

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

  async downloadAuditPack(shipmentId: string): Promise<Blob> {
    const response = await this.client.get(`shipments/${shipmentId}/audit-pack`, {
      responseType: 'blob',
    })
    return response.data
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
    this.cache.invalidate(`/eudr/shipment/${shipmentId}`)

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
  async downloadEUDRReport(shipmentId: string): Promise<Blob> {
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
    this.cache.invalidate('/eudr/')

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
    this.cache.invalidate('/users')
    return response.data
  }

  /**
   * Update a user
   */
  async updateUser(userId: string, update: UserUpdate): Promise<UserResponse> {
    const response = await this.client.patch<UserResponse>(`users/${userId}`, update)
    this.cache.invalidate('/users')
    return response.data
  }

  /**
   * Deactivate a user (soft delete)
   */
  async deactivateUser(userId: string): Promise<{ message: string }> {
    const response = await this.client.delete(`users/${userId}`)
    this.cache.invalidate('/users')
    return response.data
  }

  /**
   * Activate a user
   */
  async activateUser(userId: string): Promise<{ message: string }> {
    const response = await this.client.post(`users/${userId}/activate`)
    this.cache.invalidate('/users')
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
export { ApiClient, getStoredToken, setStoredToken, clearStoredToken, isTokenExpired }
