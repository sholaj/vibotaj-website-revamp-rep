/**
 * Shipment Detail Page Component
 *
 * Displays detailed shipment information with:
 * - Shipment metadata
 * - Document management
 * - Live tracking
 * - Compliance status
 * - Audit pack download
 */

import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Package,
  Ship,
  MapPin,
  Calendar,
  FileText,
  RefreshCw,
  Download,
  Clock,
  Building,
  AlertCircle,
} from 'lucide-react'
import api, { ApiClientError, NetworkError } from '../api/client'
import type {
  Shipment as ShipmentType,
  LiveTracking,
  ComplianceStatus as ComplianceStatusType,
  Document,
  ContainerEvent,
  ShipmentStatus,
  DocumentSummary,
} from '../types'
import DocumentList from '../components/DocumentList'
import TrackingTimeline from '../components/TrackingTimeline'
import ComplianceStatusComponent from '../components/ComplianceStatus'
import DocumentUploadModal from '../components/DocumentUploadModal'
import DocumentReviewPanel from '../components/DocumentReviewPanel'
import EUDRStatusCard from '../components/EUDRStatusCard'
import { format, formatDistanceToNow } from 'date-fns'
import { isHornHoofProduct } from '../utils/compliance'

// Check if shipment contains Horn & Hoof products (exempt from EUDR)
function isHornHoofShipment(shipment: ShipmentType | null): boolean {
  if (!shipment?.products || shipment.products.length === 0) {
    return false
  }
  return shipment.products.some(product => isHornHoofProduct(product.hs_code || ''))
}

// TICKET-001: Status badge configuration (aligned with backend ShipmentStatus enum)
const STATUS_CONFIG: Record<ShipmentStatus, { style: string; label: string }> = {
  draft: { style: 'badge-info', label: 'Draft' },  // Was 'created'
  docs_pending: { style: 'badge-warning', label: 'Docs Pending' },
  docs_complete: { style: 'badge-success', label: 'Docs Complete' },
  in_transit: { style: 'badge-info', label: 'In Transit' },
  arrived: { style: 'badge-success', label: 'Arrived' },
  customs: { style: 'badge-warning', label: 'At Customs' },  // Added - was missing
  delivered: { style: 'badge-success', label: 'Delivered' },
  archived: { style: 'bg-gray-100 text-gray-600', label: 'Archived' },  // Was 'closed'
}

function getStatusBadge(status: ShipmentStatus) {
  const config = STATUS_CONFIG[status] || { style: 'badge-info', label: status }
  return (
    <span className={`${config.style} text-sm px-3 py-1`}>
      {config.label}
    </span>
  )
}

// Loading skeleton
function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center space-x-4">
        <div className="h-8 w-8 bg-gray-200 rounded"></div>
        <div className="h-8 w-64 bg-gray-200 rounded"></div>
      </div>
      <div className="card p-6">
        <div className="h-6 w-48 bg-gray-200 rounded mb-4"></div>
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Error display
function ErrorDisplay({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="bg-danger-50 border border-danger-200 rounded-lg p-6 text-center">
      <AlertCircle className="h-12 w-12 text-danger-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-danger-800 mb-2">Failed to Load Shipment</h3>
      <p className="text-danger-600 mb-4">{message}</p>
      <div className="flex justify-center gap-3">
        <Link to="/dashboard" className="btn-secondary">
          Back to Dashboard
        </Link>
        <button onClick={onRetry} className="btn-primary">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </button>
      </div>
    </div>
  )
}

export default function Shipment() {
  const { id } = useParams<{ id: string }>()
  const [shipment, setShipment] = useState<ShipmentType | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [documentSummary, setDocumentSummary] = useState<DocumentSummary | null>(null)
  const [events, setEvents] = useState<ContainerEvent[]>([])
  const [liveTracking, setLiveTracking] = useState<LiveTracking | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'documents' | 'tracking'>('documents')
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [isReviewPanelOpen, setIsReviewPanelOpen] = useState(false)
  const [trackingError, setTrackingError] = useState<string | null>(null)

  // Fetch shipment data
  const fetchData = useCallback(async () => {
    if (!id) return

    setIsLoading(true)
    setError(null)

    try {
      // Fetch shipment detail (includes documents and latest event)
      const detail = await api.getShipment(id)
      setShipment(detail.shipment)
      setDocuments(detail.documents || [])
      setDocumentSummary(detail.document_summary)

      // Fetch container events
      const eventsResponse = await api.getContainerEvents(id)
      setEvents(eventsResponse.events || [])
    } catch (err) {
      console.error('Failed to fetch shipment:', err)

      if (err instanceof NetworkError) {
        setError('Unable to connect to the server. Please check your internet connection.')
      } else if (err instanceof ApiClientError) {
        if (err.statusCode === 404) {
          setError('Shipment not found.')
        } else {
          setError(err.message || 'Failed to load shipment')
        }
      } else {
        setError('An unexpected error occurred')
      }
    } finally {
      setIsLoading(false)
    }
  }, [id])

  // Refresh live tracking
  const refreshTracking = useCallback(async () => {
    if (!shipment?.container_number || !id) return

    setIsRefreshing(true)
    setTrackingError(null)

    try {
      // First, try to refresh from carrier API
      const refreshResult = await api.refreshTracking(id)
      console.log('Tracking refreshed:', refreshResult)

      // Then fetch live tracking status
      const tracking = await api.getLiveTracking(shipment.container_number)
      setLiveTracking(tracking)

      // Reload events to get any new ones
      const eventsResponse = await api.getContainerEvents(id)
      setEvents(eventsResponse.events || [])
    } catch (err) {
      console.error('Failed to refresh tracking:', err)
      // Show user-friendly error message
      if (err instanceof ApiClientError) {
        setTrackingError(err.message || 'Failed to refresh tracking data')
      } else {
        setTrackingError('Unable to fetch live tracking. The container may not be tracked yet.')
      }
    } finally {
      setIsRefreshing(false)
    }
  }, [shipment?.container_number, id])

  // Download audit pack
  const downloadAuditPack = useCallback(async () => {
    if (!id || !shipment) return

    setIsDownloading(true)

    try {
      const blob = await api.downloadAuditPack(id)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${shipment.reference}-audit-pack.zip`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download audit pack:', err)
      // Could show a toast notification here
    } finally {
      setIsDownloading(false)
    }
  }, [id, shipment])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Fetch live tracking when shipment is loaded
  useEffect(() => {
    const fetchLiveTracking = async () => {
      if (!shipment?.container_number) return

      try {
        const tracking = await api.getLiveTracking(shipment.container_number)
        setLiveTracking(tracking)
        setTrackingError(null)
      } catch (err) {
        console.log('Live tracking not available:', err)
        // Don't show error on initial load - user can click refresh
      }
    }

    fetchLiveTracking()
  }, [shipment?.container_number])

  // Create compliance status from document summary
  const compliance: ComplianceStatusType | null = documentSummary
    ? {
        is_compliant: documentSummary.is_complete,
        total_required: documentSummary.total_required,
        total_present: documentSummary.total_uploaded,
        missing_documents: documentSummary.missing,
        pending_validation: [],
        issues: [],
      }
    : null

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchData} />
  }

  if (!shipment) {
    return <ErrorDisplay message="Shipment not found" onRetry={fetchData} />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/dashboard" className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <ArrowLeft className="h-5 w-5 text-gray-600" />
          </Link>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-gray-900">{shipment.reference}</h1>
              {getStatusBadge(shipment.status)}
            </div>
            <p className="text-gray-600 mt-1">
              Container: <span className="font-mono">{shipment.container_number}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={refreshTracking}
            disabled={isRefreshing}
            className="btn-secondary"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Refreshing...' : 'Refresh Tracking'}
          </button>
          <button
            onClick={downloadAuditPack}
            disabled={isDownloading}
            className="btn-primary"
          >
            <Download className={`h-4 w-4 mr-2 ${isDownloading ? 'animate-pulse' : ''}`} />
            {isDownloading ? 'Downloading...' : 'Download Audit Pack'}
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Shipment Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Shipment Info Card */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Shipment Details</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-start space-x-3">
                <Ship className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Vessel / Voyage</p>
                  <p className="font-medium">
                    {shipment.vessel_name || 'TBD'} / {shipment.voyage_number || 'TBD'}
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <FileText className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">B/L Number</p>
                  <p className="font-medium font-mono">{shipment.bl_number || 'N/A'}</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <MapPin className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Route</p>
                  <p className="font-medium">
                    {shipment.pol_name || shipment.pol_code || 'Origin'} →{' '}
                    {shipment.pod_name || shipment.pod_code || 'Destination'}
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">ETD / ETA</p>
                  <p className="font-medium">
                    {shipment.etd ? format(new Date(shipment.etd), 'MMM d') : '-'} →{' '}
                    {shipment.eta ? format(new Date(shipment.eta), 'MMM d, yyyy') : '-'}
                  </p>
                  {shipment.eta && (
                    <p className="text-xs text-gray-500">
                      {formatDistanceToNow(new Date(shipment.eta), { addSuffix: true })}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Parties */}
            {(shipment.buyer || shipment.supplier) && (
              <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 gap-4">
                {shipment.supplier && (
                  <div className="flex items-start space-x-3">
                    <Building className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Shipper</p>
                      <p className="font-medium">{shipment.supplier.company_name}</p>
                      <p className="text-sm text-gray-500">
                        {shipment.supplier.city && `${shipment.supplier.city}, `}
                        {shipment.supplier.country}
                      </p>
                    </div>
                  </div>
                )}

                {shipment.buyer && (
                  <div className="flex items-start space-x-3">
                    <Building className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Consignee</p>
                      <p className="font-medium">{shipment.buyer.company_name}</p>
                      <p className="text-sm text-gray-500">{shipment.buyer.address}</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Cargo */}
            {shipment.products && shipment.products.length > 0 && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Cargo</h3>
                {shipment.products.map((product) => (
                  <div key={product.id} className="flex items-start space-x-3">
                    <Package className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="font-medium">{product.description}</p>
                      <p className="text-sm text-gray-500">
                        HS: {product.hs_code}
                        {product.quantity_net_kg && ` | ${product.quantity_net_kg.toLocaleString()} KG`}
                        {product.packaging_type && ` | ${product.packaging_type}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Tabs for Documents/Tracking */}
          <div className="card overflow-hidden">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                <button
                  onClick={() => setActiveTab('documents')}
                  className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'documents'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <FileText className="h-4 w-4 inline mr-2" />
                  Documents ({documents.length})
                </button>
                <button
                  onClick={() => setActiveTab('tracking')}
                  className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'tracking'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Clock className="h-4 w-4 inline mr-2" />
                  Tracking ({events.length} events)
                </button>
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'documents' ? (
                <DocumentList
                  documents={documents}
                  missingDocuments={compliance?.missing_documents}
                  onDocumentClick={(doc) => {
                    setSelectedDocument(doc)
                    setIsReviewPanelOpen(true)
                  }}
                />
              ) : (
                <TrackingTimeline events={events} />
              )}
            </div>
          </div>
        </div>

        {/* Right Column - Compliance & Live Status */}
        <div className="space-y-6">
          {/* EUDR Compliance Card - Only show for non-Horn & Hoof products */}
          {id && !isHornHoofShipment(shipment) && (
            <EUDRStatusCard
              shipmentId={id}
              onValidationComplete={fetchData}
            />
          )}

          {/* Document Compliance Card */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Document Status</h2>
            {compliance && <ComplianceStatusComponent compliance={compliance} />}
          </div>

          {/* Live Tracking Card */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Live Status</h2>
            {trackingError ? (
              <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-warning-500 mt-0.5 mr-3 flex-shrink-0" />
                  <div>
                    <p className="text-sm text-warning-800">{trackingError}</p>
                    <button
                      onClick={refreshTracking}
                      disabled={isRefreshing}
                      className="mt-2 text-sm text-warning-700 hover:text-warning-800 underline"
                    >
                      Try again
                    </button>
                  </div>
                </div>
              </div>
            ) : liveTracking ? (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Status</span>
                  <span className="font-medium">{liveTracking.status}</span>
                </div>
                {liveTracking.vessel?.current_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Current Vessel</span>
                    <span className="font-medium">{liveTracking.vessel.current_name}</span>
                  </div>
                )}
                {liveTracking.current_location?.port && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Location</span>
                    <span className="font-medium">{liveTracking.current_location.port}</span>
                  </div>
                )}
                {liveTracking.eta && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">ETA</span>
                    <span className="font-medium">{liveTracking.eta}</span>
                  </div>
                )}
                {liveTracking.last_updated && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Last Updated</span>
                    <span className="text-gray-600">{liveTracking.last_updated}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <Ship className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">Click "Sync Live Tracking" to fetch latest data</p>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => setIsUploadModalOpen(true)}
                className="btn-secondary w-full justify-start"
              >
                <FileText className="h-4 w-4 mr-2" />
                Upload Document
              </button>
              <button
                onClick={refreshTracking}
                disabled={isRefreshing}
                className="btn-secondary w-full justify-start"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Syncing...' : 'Sync Live Tracking'}
              </button>
              <button
                onClick={downloadAuditPack}
                disabled={isDownloading}
                className="btn-primary w-full justify-start"
              >
                <Download className={`h-4 w-4 mr-2 ${isDownloading ? 'animate-pulse' : ''}`} />
                {isDownloading ? 'Downloading...' : 'Download Audit Pack'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Document Upload Modal */}
      <DocumentUploadModal
        shipmentId={id || ''}
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadComplete={fetchData}
      />

      {/* Document Review Panel */}
      {isReviewPanelOpen && selectedDocument && (
        <DocumentReviewPanel
          document={selectedDocument}
          onClose={() => {
            setIsReviewPanelOpen(false)
            setSelectedDocument(null)
          }}
          onUpdate={() => {
            setIsReviewPanelOpen(false)
            setSelectedDocument(null)
            fetchData()
          }}
        />
      )}
    </div>
  )
}
