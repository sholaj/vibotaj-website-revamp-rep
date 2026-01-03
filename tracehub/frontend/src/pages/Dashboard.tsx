/**
 * Dashboard Page Component
 *
 * Displays list of shipments with:
 * - Proper error handling
 * - Loading states
 * - Refresh functionality
 * - Status filtering (future)
 */

import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Package, Ship, MapPin, Calendar, ChevronRight, RefreshCw, AlertCircle } from 'lucide-react'
import api, { ApiClientError, NetworkError } from '../api/client'
import type { Shipment, ShipmentStatus } from '../types'
import { format } from 'date-fns'

// Status badge styles and labels
const STATUS_CONFIG: Record<ShipmentStatus, { style: string; label: string }> = {
  created: { style: 'badge-info', label: 'Created' },
  docs_pending: { style: 'badge-warning', label: 'Docs Pending' },
  docs_complete: { style: 'badge-success', label: 'Docs Complete' },
  in_transit: { style: 'badge-info', label: 'In Transit' },
  arrived: { style: 'badge-success', label: 'Arrived' },
  delivered: { style: 'badge-success', label: 'Delivered' },
  closed: { style: 'bg-gray-100 text-gray-600', label: 'Closed' },
}

function getStatusBadge(status: ShipmentStatus) {
  const config = STATUS_CONFIG[status] || { style: 'badge-info', label: status }
  return (
    <span className={config.style}>
      {config.label}
    </span>
  )
}

// Error display component
function ErrorDisplay({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="bg-danger-50 border border-danger-200 rounded-lg p-6 text-center">
      <AlertCircle className="h-12 w-12 text-danger-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-danger-800 mb-2">Failed to Load Shipments</h3>
      <p className="text-danger-600 mb-4">{message}</p>
      <button onClick={onRetry} className="btn-primary">
        <RefreshCw className="h-4 w-4 mr-2" />
        Try Again
      </button>
    </div>
  )
}

// Empty state component
function EmptyState() {
  return (
    <div className="text-center py-12">
      <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">No shipments found</h3>
      <p className="text-gray-600">Shipments will appear here once created.</p>
    </div>
  )
}

// Loading skeleton component
function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="card p-6 animate-pulse">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-6 w-40 bg-gray-200 rounded"></div>
                <div className="h-5 w-24 bg-gray-200 rounded-full"></div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="h-4 w-32 bg-gray-200 rounded"></div>
                <div className="h-4 w-40 bg-gray-200 rounded"></div>
                <div className="h-4 w-36 bg-gray-200 rounded"></div>
                <div className="h-4 w-28 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// Shipment card component
function ShipmentCard({ shipment }: { shipment: Shipment }) {
  return (
    <Link
      to={`/shipment/${shipment.id}`}
      className="card p-6 hover:shadow-md transition-shadow block"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Reference and Status */}
          <div className="flex items-center gap-3 mb-3">
            <h2 className="text-lg font-semibold text-gray-900">
              {shipment.reference}
            </h2>
            {getStatusBadge(shipment.status)}
          </div>

          {/* Container and B/L */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center text-gray-600">
              <Package className="h-4 w-4 mr-2 text-gray-400 flex-shrink-0" />
              <span className="font-mono truncate">{shipment.container_number}</span>
            </div>

            <div className="flex items-center text-gray-600">
              <Ship className="h-4 w-4 mr-2 text-gray-400 flex-shrink-0" />
              <span className="truncate">
                {shipment.vessel_name || 'TBD'}
                {shipment.voyage_number ? ` / ${shipment.voyage_number}` : ''}
              </span>
            </div>

            <div className="flex items-center text-gray-600">
              <MapPin className="h-4 w-4 mr-2 text-gray-400 flex-shrink-0" />
              <span className="truncate">
                {shipment.pol_name || shipment.pol_code || 'Origin'}
                {' -> '}
                {shipment.pod_name || shipment.pod_code || 'Destination'}
              </span>
            </div>

            <div className="flex items-center text-gray-600">
              <Calendar className="h-4 w-4 mr-2 text-gray-400 flex-shrink-0" />
              <span>
                ETA: {shipment.eta ? format(new Date(shipment.eta), 'MMM d, yyyy') : 'TBD'}
              </span>
            </div>
          </div>
        </div>

        <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0 ml-4" />
      </div>
    </Link>
  )
}

export default function Dashboard() {
  const [shipments, setShipments] = useState<Shipment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchShipments = useCallback(async (showLoadingState = true) => {
    if (showLoadingState) {
      setIsLoading(true)
    } else {
      setIsRefreshing(true)
    }
    setError(null)

    try {
      const data = await api.getShipments()
      setShipments(data)
    } catch (err) {
      console.error('Failed to fetch shipments:', err)

      if (err instanceof NetworkError) {
        setError('Unable to connect to the server. Please check your internet connection.')
      } else if (err instanceof ApiClientError) {
        setError(err.message || 'Failed to load shipments')
      } else {
        setError('An unexpected error occurred while loading shipments')
      }
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchShipments()
  }, [fetchShipments])

  const handleRefresh = useCallback(() => {
    // Clear cache before refreshing
    api.invalidateCache('/shipments')
    fetchShipments(false)
  }, [fetchShipments])

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Shipments</h1>
          <p className="text-gray-600 mt-1">Track your container shipments and documentation</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="btn-secondary"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Content */}
      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorDisplay message={error} onRetry={() => fetchShipments()} />
      ) : shipments.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid gap-4">
          {shipments.map((shipment) => (
            <ShipmentCard key={shipment.id} shipment={shipment} />
          ))}
        </div>
      )}

      {/* Shipment count */}
      {!isLoading && !error && shipments.length > 0 && (
        <div className="mt-6 text-sm text-gray-500 text-center">
          Showing {shipments.length} shipment{shipments.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}
