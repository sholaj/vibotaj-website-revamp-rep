/**
 * EUDR Compliance Status Card Component
 *
 * Displays EUDR compliance status for a shipment with:
 * - Overall compliance status badge
 * - Risk level indicator
 * - Compliance checklist
 * - Action buttons for validation and report download
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Download,
  MapPin,
  Calendar,
  FileText,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import api from '../api/client'
import type {
  EUDRStatusResponse,
  EUDRValidationResponse,
  RiskLevel,
  EUDRValidationStatus,
} from '../types'

interface EUDRStatusCardProps {
  shipmentId: string
  onValidationComplete?: () => void
}

// Status configuration
const STATUS_CONFIG: Record<EUDRValidationStatus, {
  icon: typeof Shield
  color: string
  bgColor: string
  label: string
}> = {
  compliant: {
    icon: ShieldCheck,
    color: 'text-success-600',
    bgColor: 'bg-success-50',
    label: 'EUDR Compliant',
  },
  non_compliant: {
    icon: ShieldAlert,
    color: 'text-danger-600',
    bgColor: 'bg-danger-50',
    label: 'Non-Compliant',
  },
  pending: {
    icon: Shield,
    color: 'text-warning-600',
    bgColor: 'bg-warning-50',
    label: 'Pending Validation',
  },
  incomplete: {
    icon: ShieldQuestion,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    label: 'Incomplete Data',
  },
}

// Risk level configuration
const RISK_CONFIG: Record<RiskLevel, {
  color: string
  bgColor: string
  label: string
}> = {
  low: {
    color: 'text-success-700',
    bgColor: 'bg-success-100',
    label: 'Low Risk',
  },
  medium: {
    color: 'text-warning-700',
    bgColor: 'bg-warning-100',
    label: 'Medium Risk',
  },
  high: {
    color: 'text-danger-700',
    bgColor: 'bg-danger-100',
    label: 'High Risk',
  },
  unknown: {
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    label: 'Unknown',
  },
}

export default function EUDRStatusCard({
  shipmentId,
  onValidationComplete,
}: EUDRStatusCardProps) {
  const [status, setStatus] = useState<EUDRStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isValidating, setIsValidating] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [validationResult, setValidationResult] = useState<EUDRValidationResponse | null>(null)

  // Fetch EUDR status
  const fetchStatus = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const data = await api.getEUDRStatus(shipmentId)
      setStatus(data)
    } catch (err) {
      console.error('Failed to fetch EUDR status:', err)
      setError('Failed to load EUDR compliance status')
    } finally {
      setIsLoading(false)
    }
  }, [shipmentId])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  // Run validation
  const handleValidate = async () => {
    setIsValidating(true)
    setError(null)

    try {
      const result = await api.validateEUDR(shipmentId)
      setValidationResult(result)
      setStatus(result.validation_result)
      onValidationComplete?.()
    } catch (err) {
      console.error('EUDR validation failed:', err)
      setError('Validation failed. Please try again.')
    } finally {
      setIsValidating(false)
    }
  }

  // Download report
  const handleDownloadReport = async () => {
    setIsDownloading(true)

    try {
      const blob = await api.downloadEUDRReport(shipmentId)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `EUDR-Report-${shipmentId}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to download report:', err)
      setError('Failed to download report')
    } finally {
      setIsDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-40 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error && !status) {
    return (
      <div className="card p-6">
        <div className="flex items-center space-x-3 text-danger-600">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
        <button
          onClick={fetchStatus}
          className="mt-4 btn-secondary w-full"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </button>
      </div>
    )
  }

  if (!status) {
    return null
  }

  const statusConfig = STATUS_CONFIG[status.overall_status]
  const riskConfig = RISK_CONFIG[status.overall_risk_level]
  const StatusIcon = statusConfig.icon

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className={`p-4 ${statusConfig.bgColor} border-b`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <StatusIcon className={`h-6 w-6 ${statusConfig.color}`} />
            <div>
              <h3 className="font-semibold text-gray-900">EUDR Compliance</h3>
              <p className={`text-sm ${statusConfig.color}`}>{statusConfig.label}</p>
            </div>
          </div>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${riskConfig.bgColor} ${riskConfig.color}`}>
            {riskConfig.label}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <MapPin className="h-4 w-4 text-gray-400" />
            <span>
              <span className="font-medium">{status.summary.compliant_origins}</span>
              <span className="text-gray-500">/{status.summary.total_origins} origins</span>
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4 text-gray-400" />
            <span>
              <span className="font-medium">{status.summary.passed_checks}</span>
              <span className="text-gray-500">/{status.summary.total_checks} checks</span>
            </span>
          </div>
        </div>

        {/* Checklist */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Compliance Checklist</h4>
          <div className="space-y-1">
            {status.checklist.map((item, index) => (
              <div
                key={index}
                className={`flex items-start space-x-2 p-2 rounded text-sm ${
                  item.passed ? 'bg-success-50' : 'bg-danger-50'
                }`}
              >
                {item.passed ? (
                  <CheckCircle className="h-4 w-4 text-success-600 mt-0.5 flex-shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-danger-600 mt-0.5 flex-shrink-0" />
                )}
                <div>
                  <span className={item.passed ? 'text-success-800' : 'text-danger-800'}>
                    {item.item}
                  </span>
                  <p className="text-xs text-gray-600 mt-0.5">{item.details}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Validation Result Actions */}
        {validationResult && validationResult.action_items.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Action Items</h4>
            <div className="space-y-1">
              {validationResult.action_items.map((item, index) => (
                <div
                  key={index}
                  className={`flex items-start space-x-2 p-2 rounded text-sm ${
                    item.priority === 'high'
                      ? 'bg-danger-50'
                      : item.priority === 'medium'
                      ? 'bg-warning-50'
                      : 'bg-gray-50'
                  }`}
                >
                  <AlertTriangle
                    className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                      item.priority === 'high'
                        ? 'text-danger-600'
                        : item.priority === 'medium'
                        ? 'text-warning-600'
                        : 'text-gray-600'
                    }`}
                  />
                  <div>
                    <span className="font-medium">{item.action}</span>
                    <p className="text-xs text-gray-600 mt-0.5">{item.details}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* EUDR Document Status */}
        <div className="flex items-center space-x-2 text-sm">
          <FileText className="h-4 w-4 text-gray-400" />
          <span>
            EUDR Due Diligence Document:{' '}
            {status.summary.has_eudr_document ? (
              <span className="text-success-600 font-medium">Uploaded</span>
            ) : (
              <span className="text-danger-600 font-medium">Missing</span>
            )}
          </span>
        </div>

        {/* Cutoff Date Info */}
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <Calendar className="h-3 w-3" />
          <span>EUDR Cutoff Date: {status.cutoff_date}</span>
        </div>

        {/* Error Display */}
        {error && (
          <div className="flex items-center space-x-2 text-sm text-danger-600 bg-danger-50 p-2 rounded">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex space-x-2 pt-2">
          <button
            onClick={handleValidate}
            disabled={isValidating}
            className="btn-primary flex-1 justify-center"
          >
            {isValidating ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            {isValidating ? 'Validating...' : 'Run Validation'}
          </button>
          <button
            onClick={handleDownloadReport}
            disabled={isDownloading}
            className="btn-secondary"
          >
            {isDownloading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Footer with timestamp */}
      <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
        Last assessed: {new Date(status.assessed_at).toLocaleString()}
      </div>
    </div>
  )
}
