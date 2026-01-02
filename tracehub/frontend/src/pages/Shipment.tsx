import { useState, useEffect } from 'react'
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
} from 'lucide-react'
import api from '../api/client'
import type { Shipment as ShipmentType, LiveTracking, ComplianceStatus as ComplianceStatusType, Document, ContainerEvent } from '../types'
import DocumentList from '../components/DocumentList'
import TrackingTimeline from '../components/TrackingTimeline'
import ComplianceStatusComponent from '../components/ComplianceStatus'
import { format, formatDistanceToNow } from 'date-fns'

// Mock data for demo
const MOCK_SHIPMENT: ShipmentType = {
  id: 'demo-1',
  reference: 'TEMIRA-2025-001',
  container_number: 'MRSU3452572',
  bl_number: '262495038',
  booking_reference: 'MAERSK-550N',
  vessel_name: 'RHINE MAERSK',
  voyage_number: '550N',
  etd: '2025-12-13T00:00:00Z',
  eta: '2026-01-04T19:00:00Z',
  pol_code: 'NGAPP',
  pol_name: 'Apapa, Lagos',
  pod_code: 'DEHAM',
  pod_name: 'Hamburg',
  final_destination: 'Stelle, Germany',
  incoterms: 'FOB',
  status: 'in_transit',
  buyer: {
    id: 'buyer-1',
    type: 'buyer',
    company_name: 'WITATRADE GMBH',
    address: '98A Duvendahl, Stelle, 21435',
    country: 'DE',
  },
  supplier: {
    id: 'supplier-1',
    type: 'supplier',
    company_name: 'TEMIRA INDUSTRIES NIGERIA LTD',
    city: 'Lagos',
    country: 'NG',
  },
  products: [
    {
      id: 'prod-1',
      hs_code: '0506.90.00',
      description: 'Crushed Cow Hooves & Horns',
      quantity_net_kg: 25000,
      quantity_gross_kg: 25200,
      unit_of_measure: 'KG',
      packaging_type: '1x40ft Container, 20 CBM',
    },
  ],
}

const MOCK_DOCUMENTS: Document[] = [
  { id: '1', shipment_id: 'demo-1', document_type: 'bill_of_lading', name: 'Bill of Lading - Maersk 262495038', status: 'validated', reference_number: '262495038', issue_date: '2025-12-13', uploaded_by: 'temira_exports', uploaded_at: '2025-12-10T10:00:00Z' },
  { id: '2', shipment_id: 'demo-1', document_type: 'certificate_of_origin', name: 'Certificate of Origin - 0029532', status: 'validated', reference_number: '0029532', issue_date: '2025-12-10', uploaded_by: 'temira_exports', uploaded_at: '2025-12-10T10:00:00Z' },
  { id: '3', shipment_id: 'demo-1', document_type: 'fumigation_certificate', name: 'Fumigation Certificate - 77091', status: 'validated', reference_number: '77091', issue_date: '2025-12-05', uploaded_by: 'temira_exports', uploaded_at: '2025-12-10T10:00:00Z' },
  { id: '4', shipment_id: 'demo-1', document_type: 'commercial_invoice', name: 'Commercial Invoice', status: 'validated', reference_number: 'TEMIRA-INV-2025-001', issue_date: '2025-12-10', uploaded_by: 'temira_exports', uploaded_at: '2025-12-10T10:00:00Z' },
  { id: '5', shipment_id: 'demo-1', document_type: 'packing_list', name: 'Packing List', status: 'validated', reference_number: 'TEMIRA-PL-2025-001', issue_date: '2025-12-10', uploaded_by: 'temira_exports', uploaded_at: '2025-12-10T10:00:00Z' },
  { id: '6', shipment_id: 'demo-1', document_type: 'phytosanitary_certificate', name: 'Federal Produce Inspection Certificate', status: 'validated', reference_number: 'FPIS-2025-TEMIRA', issue_date: '2025-12-08', uploaded_by: 'temira_exports', uploaded_at: '2025-12-10T10:00:00Z' },
]

const MOCK_EVENTS: ContainerEvent[] = [
  { id: '1', event_type: 'gate_in', event_timestamp: '2025-12-11T08:30:00Z', location_name: 'Apapa Container Terminal', location_code: 'NGAPP' },
  { id: '2', event_type: 'loaded', event_timestamp: '2025-12-12T14:00:00Z', location_name: 'Apapa, Lagos', location_code: 'NGAPP', vessel_name: 'RHINE MAERSK', voyage_number: '550N' },
  { id: '3', event_type: 'departed', event_timestamp: '2025-12-13T18:00:00Z', location_name: 'Apapa, Lagos', location_code: 'NGAPP', vessel_name: 'RHINE MAERSK', voyage_number: '550N' },
  { id: '4', event_type: 'transshipment', event_timestamp: '2025-12-23T06:23:00Z', location_name: 'PORT TANGIER MEDITERRANEE', location_code: 'MAPTM', vessel_name: 'OAKLAND EXPRESS', voyage_number: '547W' },
  { id: '5', event_type: 'departed', event_timestamp: '2025-12-28T07:03:00Z', location_name: 'PORT TANGIER MEDITERRANEE', location_code: 'MAPTM', vessel_name: 'OAKLAND EXPRESS', voyage_number: '547W' },
]

const MOCK_COMPLIANCE: ComplianceStatusType = {
  is_compliant: false,
  total_required: 9,
  total_present: 6,
  missing_documents: ['sanitary_certificate', 'insurance_certificate', 'eudr_declaration'],
  pending_validation: [],
  issues: [],
}

export default function Shipment() {
  const { id } = useParams<{ id: string }>()
  const [shipment, setShipment] = useState<ShipmentType | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [events, setEvents] = useState<ContainerEvent[]>([])
  const [compliance, setCompliance] = useState<ComplianceStatusType | null>(null)
  const [liveTracking, setLiveTracking] = useState<LiveTracking | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState<'documents' | 'tracking'>('documents')

  const fetchData = async () => {
    setIsLoading(true)
    try {
      // Try to fetch from API
      const shipmentData = await api.getShipment(id!)
      setShipment(shipmentData)
      // ... fetch other data
    } catch (err) {
      // Use mock data for demo
      setShipment(MOCK_SHIPMENT)
      setDocuments(MOCK_DOCUMENTS)
      setEvents(MOCK_EVENTS)
      setCompliance(MOCK_COMPLIANCE)
    } finally {
      setIsLoading(false)
    }
  }

  const refreshTracking = async () => {
    if (!shipment) return
    setIsRefreshing(true)
    try {
      const tracking = await api.getLiveTracking(shipment.container_number)
      setLiveTracking(tracking)
    } catch (err) {
      // Ignore errors for demo
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [id])

  if (isLoading || !shipment) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      created: 'badge-info',
      docs_pending: 'badge-warning',
      docs_complete: 'badge-success',
      in_transit: 'badge-info',
      arrived: 'badge-success',
      delivered: 'badge-success',
      closed: 'bg-gray-100 text-gray-600',
    }
    const labels: Record<string, string> = {
      created: 'Created',
      docs_pending: 'Docs Pending',
      docs_complete: 'Docs Complete',
      in_transit: 'In Transit',
      arrived: 'Arrived',
      delivered: 'Delivered',
      closed: 'Closed',
    }
    return (
      <span className={`${styles[status] || 'badge-info'} text-sm px-3 py-1`}>
        {labels[status] || status}
      </span>
    )
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
          <button className="btn-primary">
            <Download className="h-4 w-4 mr-2" />
            Download Audit Pack
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
                  <p className="font-medium">{shipment.vessel_name} / {shipment.voyage_number}</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <FileText className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">B/L Number</p>
                  <p className="font-medium font-mono">{shipment.bl_number}</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <MapPin className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Route</p>
                  <p className="font-medium">{shipment.pol_name} → {shipment.pod_name}</p>
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
            <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 gap-4">
              <div className="flex items-start space-x-3">
                <Building className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Shipper</p>
                  <p className="font-medium">{shipment.supplier?.company_name}</p>
                  <p className="text-sm text-gray-500">{shipment.supplier?.city}, {shipment.supplier?.country}</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <Building className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Consignee</p>
                  <p className="font-medium">{shipment.buyer?.company_name}</p>
                  <p className="text-sm text-gray-500">{shipment.buyer?.address}</p>
                </div>
              </div>
            </div>

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
                        HS: {product.hs_code} | {product.quantity_net_kg.toLocaleString()} KG | {product.packaging_type}
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
                />
              ) : (
                <TrackingTimeline events={events} />
              )}
            </div>
          </div>
        </div>

        {/* Right Column - Compliance & Live Status */}
        <div className="space-y-6">
          {/* Compliance Card */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Status</h2>
            {compliance && <ComplianceStatusComponent compliance={compliance} />}
          </div>

          {/* Live Tracking Card */}
          {liveTracking && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Live Status</h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Status</span>
                  <span className="font-medium">{liveTracking.status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Current Vessel</span>
                  <span className="font-medium">{liveTracking.vessel.current_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Location</span>
                  <span className="font-medium">{liveTracking.current_location.port}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">ETA</span>
                  <span className="font-medium">{liveTracking.eta}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Last Updated</span>
                  <span className="text-gray-600">{liveTracking.last_updated}</span>
                </div>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button className="btn-secondary w-full justify-start">
                <FileText className="h-4 w-4 mr-2" />
                Upload Document
              </button>
              <button
                onClick={refreshTracking}
                disabled={isRefreshing}
                className="btn-secondary w-full justify-start"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Sync Live Tracking
              </button>
              <button className="btn-primary w-full justify-start">
                <Download className="h-4 w-4 mr-2" />
                Download Audit Pack
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
