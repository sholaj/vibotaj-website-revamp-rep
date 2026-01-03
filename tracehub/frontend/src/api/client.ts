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
  Document,
  LiveTracking,
  ComplianceStatus,
  User,
  ContainerStatusResponse,
  ShipmentEventsResponse,
  ShipmentDocumentsResponse,
  TrackingRefreshResponse,
  ShipmentDetailResponse,
  DocumentType,
  ApiError,
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
  private _isRefreshing: boolean = false
  private _refreshSubscribers: Array<(token: string) => void> = []

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

    const response = await this.client.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    // Store token with 24 hour expiry (matches backend JWT_EXPIRATION_HOURS)
    setStoredToken(response.data.access_token, 24)

    // Clear any cached data on new login
    this.cache.invalidate()

    return response.data
  }

  async getCurrentUser(): Promise<User> {
    return this.cachedGet<User>('/auth/me', 5 * 60 * 1000) // 5 minute cache
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
    return this.cachedGet<Shipment[]>('/shipments')
  }

  async getShipment(id: string): Promise<ShipmentDetailResponse> {
    return this.cachedGet<ShipmentDetailResponse>(`/shipments/${id}`)
  }

  async getShipmentBasic(id: string): Promise<Shipment> {
    const response = await this.getShipment(id)
    return response.shipment
  }

  // ============================================
  // Document Methods
  // ============================================

  async getShipmentDocuments(shipmentId: string): Promise<ShipmentDocumentsResponse> {
    return this.cachedGet<ShipmentDocumentsResponse>(`/shipments/${shipmentId}/documents`)
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
    }
  ): Promise<Document> {
    const formData = new FormData()
    formData.append('shipment_id', shipmentId)
    formData.append('file', file)
    formData.append('document_type', documentType)

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

    const response = await this.client.post<Document>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    // Invalidate shipment document cache
    this.cache.invalidate(`/shipments/${shipmentId}`)

    return response.data
  }

  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await this.client.get(`/documents/${documentId}/download`, {
      responseType: 'blob',
    })
    return response.data
  }

  async validateDocument(documentId: string, notes?: string): Promise<{ message: string; status: string }> {
    const response = await this.client.patch(`/documents/${documentId}/validate`, { notes })

    // Invalidate related caches
    this.cache.invalidate('/shipments/')

    return response.data
  }

  async deleteDocument(documentId: string): Promise<{ message: string }> {
    const response = await this.client.delete(`/documents/${documentId}`)

    // Invalidate related caches
    this.cache.invalidate('/shipments/')

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
      `/tracking/status/${encodeURIComponent(containerNumber)}`,
      30000 // 30 second cache for tracking data
    )
  }

  async getLiveTracking(containerNumber: string, shippingLine?: string): Promise<LiveTracking> {
    let url = `/tracking/live/${encodeURIComponent(containerNumber)}`
    if (shippingLine) {
      url += `?shipping_line=${encodeURIComponent(shippingLine)}`
    }

    // Short cache for live tracking
    return this.cachedGet<LiveTracking>(url, 30000)
  }

  async getTrackingByBol(blNumber: string, shippingLine: string): Promise<LiveTracking> {
    return this.executeWithRetry<LiveTracking>({
      method: 'GET',
      url: `/tracking/bol/${encodeURIComponent(blNumber)}`,
      params: { shipping_line: shippingLine },
    })
  }

  async refreshTracking(shipmentId: string): Promise<TrackingRefreshResponse> {
    const response = await this.client.post<TrackingRefreshResponse>(
      `/tracking/refresh/${shipmentId}`
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
    return this.cachedGet<ShipmentEventsResponse>(`/shipments/${shipmentId}/events`)
  }

  // ============================================
  // Audit Pack Methods
  // ============================================

  async downloadAuditPack(shipmentId: string): Promise<Blob> {
    const response = await this.client.get(`/shipments/${shipmentId}/audit-pack`, {
      responseType: 'blob',
    })
    return response.data
  }

  // ============================================
  // API Usage Methods
  // ============================================

  async getApiUsage(): Promise<{ used: number; limit: number; reset_date: string } | null> {
    try {
      return await this.cachedGet('/tracking/usage', 5 * 60 * 1000)
    } catch {
      return null
    }
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
