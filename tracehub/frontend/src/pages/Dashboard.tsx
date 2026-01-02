import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Package, Ship, MapPin, Calendar, ChevronRight, RefreshCw } from 'lucide-react'
import api from '../api/client'
import type { Shipment } from '../types'
import { format } from 'date-fns'

export default function Dashboard() {
  const [shipments, setShipments] = useState<Shipment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchShipments = async () => {
    setIsLoading(true)
    try {
      const data = await api.getShipments()
      setShipments(data)
      setError('')
    } catch (err) {
      setError('Failed to load shipments')
      // For demo, show mock data if API fails
      setShipments([
        {
          id: 'demo-1',
          reference: 'TEMIRA-2025-001',
          container_number: 'MRSU3452572',
          bl_number: '262495038',
          vessel_name: 'RHINE MAERSK',
          voyage_number: '550N',
          etd: '2025-12-13T00:00:00Z',
          eta: '2026-01-04T19:00:00Z',
          pol_code: 'NGAPP',
          pol_name: 'Apapa, Lagos',
          pod_code: 'DEHAM',
          pod_name: 'Hamburg',
          status: 'in_transit',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchShipments()
  }, [])

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
      <span className={styles[status] || 'badge-info'}>
        {labels[status] || status}
      </span>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Shipments</h1>
          <p className="text-gray-600 mt-1">Track your container shipments and documentation</p>
        </div>
        <button
          onClick={fetchShipments}
          className="btn-secondary"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-warning-50 border border-warning-200 text-warning-600 px-4 py-3 rounded-md text-sm mb-6">
          {error} - Showing demo data
        </div>
      )}

      {/* Shipments Grid */}
      <div className="grid gap-4">
        {shipments.map((shipment) => (
          <Link
            key={shipment.id}
            to={`/shipment/${shipment.id}`}
            className="card p-6 hover:shadow-md transition-shadow"
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
                    <Package className="h-4 w-4 mr-2 text-gray-400" />
                    <span className="font-mono">{shipment.container_number}</span>
                  </div>

                  <div className="flex items-center text-gray-600">
                    <Ship className="h-4 w-4 mr-2 text-gray-400" />
                    <span>{shipment.vessel_name} / {shipment.voyage_number}</span>
                  </div>

                  <div className="flex items-center text-gray-600">
                    <MapPin className="h-4 w-4 mr-2 text-gray-400" />
                    <span>{shipment.pol_name} → {shipment.pod_name}</span>
                  </div>

                  <div className="flex items-center text-gray-600">
                    <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                    <span>
                      ETA: {shipment.eta ? format(new Date(shipment.eta), 'MMM d, yyyy') : 'TBD'}
                    </span>
                  </div>
                </div>
              </div>

              <ChevronRight className="h-5 w-5 text-gray-400" />
            </div>
          </Link>
        ))}
      </div>

      {shipments.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No shipments found</h3>
          <p className="text-gray-600">Shipments will appear here once created.</p>
        </div>
      )}
    </div>
  )
}
