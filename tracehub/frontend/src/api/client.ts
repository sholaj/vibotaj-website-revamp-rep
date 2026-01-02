import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  Shipment,
  Document,
  LiveTracking,
  ComplianceStatus,
  User,
} from '../types'

const API_BASE_URL = '/api'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await this.client.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me')
    return response.data
  }

  // Shipments
  async getShipments(): Promise<Shipment[]> {
    const response = await this.client.get<Shipment[]>('/shipments')
    return response.data
  }

  async getShipment(id: string): Promise<Shipment> {
    const response = await this.client.get<Shipment>(`/shipments/${id}`)
    return response.data
  }

  // Documents
  async getShipmentDocuments(shipmentId: string): Promise<Document[]> {
    const response = await this.client.get<Document[]>(`/shipments/${shipmentId}/documents`)
    return response.data
  }

  async uploadDocument(shipmentId: string, file: File, documentType: string): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)

    const response = await this.client.post<Document>(
      `/shipments/${shipmentId}/documents`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  }

  // Compliance
  async getComplianceStatus(shipmentId: string): Promise<ComplianceStatus> {
    const response = await this.client.get<ComplianceStatus>(`/shipments/${shipmentId}/compliance`)
    return response.data
  }

  // Tracking
  async getContainerStatus(containerNumber: string): Promise<{
    shipment_reference: string
    shipment_status: string
    vessel: string
    voyage: string
    etd: string
    eta: string
    pol: { code: string; name: string }
    pod: { code: string; name: string }
    latest_event: { type: string; timestamp: string; location: string } | null
    live_tracking: LiveTracking | null
  }> {
    const response = await this.client.get(`/tracking/status/${containerNumber}`)
    return response.data
  }

  async getLiveTracking(containerNumber: string): Promise<LiveTracking> {
    const response = await this.client.get<LiveTracking>(`/tracking/live/${containerNumber}`)
    return response.data
  }

  async refreshTracking(shipmentId: string): Promise<{ events_added: number }> {
    const response = await this.client.post(`/tracking/refresh/${shipmentId}`)
    return response.data
  }

  // Container Events
  async getContainerEvents(shipmentId: string): Promise<{ events: Array<{
    event_type: string
    event_timestamp: string
    location_name: string
    location_code: string
    vessel_name: string | null
    voyage_number: string | null
  }> }> {
    const response = await this.client.get(`/shipments/${shipmentId}/events`)
    return response.data
  }

  // Audit Pack
  async downloadAuditPack(shipmentId: string): Promise<Blob> {
    const response = await this.client.get(`/shipments/${shipmentId}/audit-pack`, {
      responseType: 'blob',
    })
    return response.data
  }
}

export const api = new ApiClient()
export default api
