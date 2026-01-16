/**
 * Bill of Lading Compliance Panel Component
 *
 * Displays BoL parsing results and compliance status for a document with:
 * - Compliance decision badge (APPROVE/HOLD/REJECT)
 * - Rule results with severity indicators
 * - Parsed BoL data summary
 * - Sync preview and action buttons
 */

import { useState, useEffect, useCallback } from 'react'
import {
  FileText,
  CheckCircle,
  XCircle,
  AlertTriangle,
  AlertCircle,
  Loader2,
  RefreshCw,
  Ship,
  Package,
  MapPin,
  Calendar,
  Hash,
  ArrowRight,
  Info,
} from 'lucide-react'
import api from '../api/client'
import type {
  BolComplianceResultsResponse,
  BolSyncPreviewResponse,
  BolComplianceDecision,
} from '../types'

interface BolCompliancePanelProps {
  documentId: string
  shipmentId?: string
  onSyncComplete?: () => void
}

// Decision configuration
const DECISION_CONFIG: Record<BolComplianceDecision, {
  icon: typeof CheckCircle
  color: string
  bgColor: string
  borderColor: string
  label: string
}> = {
  APPROVE: {
    icon: CheckCircle,
    color: 'text-success-600',
    bgColor: 'bg-success-50',
    borderColor: 'border-success-200',
    label: 'Approved',
  },
  HOLD: {
    icon: AlertTriangle,
    color: 'text-warning-600',
    bgColor: 'bg-warning-50',
    borderColor: 'border-warning-200',
    label: 'On Hold',
  },
  REJECT: {
    icon: XCircle,
    color: 'text-danger-600',
    bgColor: 'bg-danger-50',
    borderColor: 'border-danger-200',
    label: 'Rejected',
  },
}

// Severity configuration
const SEVERITY_CONFIG: Record<string, {
  icon: typeof AlertCircle
  color: string
  bgColor: string
}> = {
  ERROR: {
    icon: XCircle,
    color: 'text-danger-600',
    bgColor: 'bg-danger-50',
  },
  WARNING: {
    icon: AlertTriangle,
    color: 'text-warning-600',
    bgColor: 'bg-warning-50',
  },
  INFO: {
    icon: Info,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
}

export default function BolCompliancePanel({
  documentId,
  shipmentId,
  onSyncComplete,
}: BolCompliancePanelProps) {
  const [complianceResults, setComplianceResults] = useState<BolComplianceResultsResponse | null>(null)
  const [syncPreview, setSyncPreview] = useState<BolSyncPreviewResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isParsing, setIsParsing] = useState(false)
  const [isCheckingCompliance, setIsCheckingCompliance] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSyncPreview, setShowSyncPreview] = useState(false)

  // Fetch existing compliance results
  const fetchComplianceResults = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const results = await api.getBolComplianceResults(documentId)
      setComplianceResults(results)
    } catch (err) {
      // If 404, no results yet - that's OK
      if (err instanceof Error && err.message.includes('404')) {
        setComplianceResults(null)
      } else {
        console.error('Failed to fetch BoL compliance results:', err)
        setError('Failed to load compliance results')
      }
    } finally {
      setIsLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    fetchComplianceResults()
  }, [fetchComplianceResults])

  // Parse BoL document
  const handleParse = async () => {
    setIsParsing(true)
    setError(null)

    try {
      await api.parseBol(documentId, false)
      // After parsing, run compliance check
      await handleCheckCompliance()
    } catch (err) {
      console.error('Failed to parse BoL:', err)
      setError(err instanceof Error ? err.message : 'Failed to parse document')
    } finally {
      setIsParsing(false)
    }
  }

  // Check compliance
  const handleCheckCompliance = async () => {
    setIsCheckingCompliance(true)
    setError(null)

    try {
      await api.checkBolCompliance(documentId, { storeResults: true })
      // Refresh results
      await fetchComplianceResults()
    } catch (err) {
      console.error('Failed to check compliance:', err)
      setError(err instanceof Error ? err.message : 'Failed to check compliance')
    } finally {
      setIsCheckingCompliance(false)
    }
  }

  // Preview sync changes
  const handlePreviewSync = async () => {
    setError(null)

    try {
      const preview = await api.previewBolSync(documentId)
      setSyncPreview(preview)
      setShowSyncPreview(true)
    } catch (err) {
      console.error('Failed to preview sync:', err)
      setError(err instanceof Error ? err.message : 'Failed to preview sync')
    }
  }

  // Sync BoL data to shipment
  const handleSync = async () => {
    setIsSyncing(true)
    setError(null)

    try {
      await api.syncBolToShipment(documentId)
      setShowSyncPreview(false)
      setSyncPreview(null)
      onSyncComplete?.()
    } catch (err) {
      console.error('Failed to sync BoL:', err)
      setError(err instanceof Error ? err.message : 'Failed to sync to shipment')
    } finally {
      setIsSyncing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  // No results yet - show parse button
  if (!complianceResults) {
    return (
      <div className="card p-6">
        <div className="flex items-center space-x-3 mb-4">
          <FileText className="h-6 w-6 text-gray-400" />
          <div>
            <h3 className="font-semibold text-gray-900">Bill of Lading Compliance</h3>
            <p className="text-sm text-gray-500">Parse document to check compliance</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-sm text-danger-600 bg-danger-50 p-3 rounded mb-4">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          onClick={handleParse}
          disabled={isParsing}
          className="btn-primary w-full justify-center"
        >
          {isParsing ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Parsing Document...
            </>
          ) : (
            <>
              <FileText className="h-4 w-4 mr-2" />
              Parse & Check Compliance
            </>
          )}
        </button>
      </div>
    )
  }

  const { compliance_status, summary, results, parsed_bol, checked_at } = complianceResults

  // Handle null compliance_status
  if (!compliance_status) {
    return (
      <div className="card p-6">
        <div className="flex items-center space-x-3 mb-4">
          <FileText className="h-6 w-6 text-gray-400" />
          <div>
            <h3 className="font-semibold text-gray-900">Bill of Lading Compliance</h3>
            <p className="text-sm text-gray-500">Compliance check incomplete</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-sm text-danger-600 bg-danger-50 p-3 rounded mb-4">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          onClick={handleCheckCompliance}
          disabled={isCheckingCompliance}
          className="btn-primary w-full justify-center"
        >
          {isCheckingCompliance ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Checking Compliance...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4 mr-2" />
              Check Compliance
            </>
          )}
        </button>
      </div>
    )
  }

  const decisionConfig = DECISION_CONFIG[compliance_status]
  const DecisionIcon = decisionConfig.icon

  return (
    <div className="card overflow-hidden">
      {/* Header with Decision */}
      <div className={`p-4 ${decisionConfig.bgColor} border-b ${decisionConfig.borderColor}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <DecisionIcon className={`h-6 w-6 ${decisionConfig.color}`} />
            <div>
              <h3 className="font-semibold text-gray-900">BoL Compliance</h3>
              <p className={`text-sm ${decisionConfig.color}`}>{decisionConfig.label}</p>
            </div>
          </div>
          {parsed_bol && (
            <span className="text-sm text-gray-600 font-mono">
              {parsed_bol.bol_number || 'No BoL#'}
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-3 text-sm">
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="font-semibold text-gray-900">{summary.total_rules}</div>
            <div className="text-xs text-gray-500">Total</div>
          </div>
          <div className="text-center p-2 bg-success-50 rounded">
            <div className="font-semibold text-success-700">{summary.passed}</div>
            <div className="text-xs text-success-600">Passed</div>
          </div>
          <div className="text-center p-2 bg-danger-50 rounded">
            <div className="font-semibold text-danger-700">{summary.errors}</div>
            <div className="text-xs text-danger-600">Errors</div>
          </div>
          <div className="text-center p-2 bg-warning-50 rounded">
            <div className="font-semibold text-warning-700">{summary.warnings}</div>
            <div className="text-xs text-warning-600">Warnings</div>
          </div>
        </div>

        {/* Rule Results */}
        {results && results.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Compliance Rules</h4>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {results.map((rule) => {
                const severityConfig = SEVERITY_CONFIG[rule.severity] || SEVERITY_CONFIG.INFO
                const SeverityIcon = rule.passed ? CheckCircle : severityConfig.icon

                return (
                  <div
                    key={rule.rule_id || rule.id}
                    className={`flex items-start space-x-2 p-2 rounded text-sm ${
                      rule.passed ? 'bg-success-50' : severityConfig.bgColor
                    }`}
                  >
                    <SeverityIcon
                      className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                        rule.passed ? 'text-success-600' : severityConfig.color
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className={`font-medium ${rule.passed ? 'text-success-800' : 'text-gray-800'}`}>
                          {rule.rule_name}
                        </span>
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          rule.passed
                            ? 'bg-success-100 text-success-700'
                            : `${severityConfig.bgColor} ${severityConfig.color}`
                        }`}>
                          {rule.severity}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 mt-0.5 truncate">{rule.message}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Parsed Data Summary */}
        {parsed_bol && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Parsed Data</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {parsed_bol.vessel_name && (
                <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <Ship className="h-4 w-4 text-gray-400" />
                  <span className="truncate">{parsed_bol.vessel_name}</span>
                </div>
              )}
              {parsed_bol.containers && parsed_bol.containers.length > 0 && (
                <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <Package className="h-4 w-4 text-gray-400" />
                  <span>{parsed_bol.containers.length} container(s)</span>
                </div>
              )}
              {parsed_bol.port_of_loading && (
                <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <MapPin className="h-4 w-4 text-gray-400" />
                  <span className="truncate">From: {parsed_bol.port_of_loading}</span>
                </div>
              )}
              {parsed_bol.port_of_discharge && (
                <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <MapPin className="h-4 w-4 text-gray-400" />
                  <span className="truncate">To: {parsed_bol.port_of_discharge}</span>
                </div>
              )}
              {parsed_bol.shipped_on_board_date && (
                <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span>{new Date(parsed_bol.shipped_on_board_date).toLocaleDateString()}</span>
                </div>
              )}
              {parsed_bol.confidence_score !== undefined && (
                <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <Hash className="h-4 w-4 text-gray-400" />
                  <span>Confidence: {Math.round(parsed_bol.confidence_score * 100)}%</span>
                </div>
              )}
            </div>

            {/* Shipper/Consignee */}
            {(parsed_bol.shipper || parsed_bol.consignee) && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                {parsed_bol.shipper?.name && (
                  <span className="truncate">{parsed_bol.shipper.name}</span>
                )}
                {parsed_bol.shipper?.name && parsed_bol.consignee?.name && (
                  <ArrowRight className="h-4 w-4 flex-shrink-0" />
                )}
                {parsed_bol.consignee?.name && (
                  <span className="truncate">{parsed_bol.consignee.name}</span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Sync Preview */}
        {showSyncPreview && syncPreview && (
          <div className="space-y-2 p-3 bg-blue-50 rounded border border-blue-200">
            <h4 className="text-sm font-medium text-blue-800">Sync Preview</h4>
            {syncPreview.change_count > 0 ? (
              <>
                <p className="text-xs text-blue-600">
                  {syncPreview.change_count} field(s) will be updated
                </p>
                <div className="space-y-1 text-sm max-h-32 overflow-y-auto">
                  {Object.entries(syncPreview.changes_to_apply).map(([field, change]) => {
                    const typedChange = change as { old: unknown; new: unknown }
                    return (
                      <div key={field} className="flex items-center space-x-2 text-blue-800">
                        <span className="font-mono text-xs">{field}:</span>
                        <span className="text-blue-600 line-through text-xs">
                          {String(typedChange.old ?? '(empty)')}
                        </span>
                        <ArrowRight className="h-3 w-3" />
                        <span className="text-blue-800 text-xs font-medium">
                          {String(typedChange.new ?? '(empty)')}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </>
            ) : (
              <p className="text-xs text-blue-600">No changes needed - shipment is up to date</p>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="flex items-center space-x-2 text-sm text-danger-600 bg-danger-50 p-2 rounded">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex space-x-2 pt-2">
          <button
            onClick={handleCheckCompliance}
            disabled={isCheckingCompliance}
            className="btn-secondary flex-1 justify-center"
          >
            {isCheckingCompliance ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Re-check
          </button>

          {shipmentId && (
            <>
              {!showSyncPreview ? (
                <button
                  onClick={handlePreviewSync}
                  className="btn-secondary flex-1 justify-center"
                >
                  <ArrowRight className="h-4 w-4 mr-2" />
                  Preview Sync
                </button>
              ) : (
                <button
                  onClick={handleSync}
                  disabled={isSyncing || Boolean(syncPreview && syncPreview.change_count === 0)}
                  className="btn-primary flex-1 justify-center"
                >
                  {isSyncing ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <ArrowRight className="h-4 w-4 mr-2" />
                  )}
                  Sync to Shipment
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Footer with timestamp */}
      {checked_at && (
        <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
          Last checked: {new Date(checked_at).toLocaleString()}
        </div>
      )}
    </div>
  )
}
