/**
 * Shipment Validation Panel Component
 *
 * Displays validation status for a shipment with:
 * - Overall validation status badge (valid/invalid)
 * - Summary stats (passed, failed, warnings)
 * - Individual rule results with severity indicators
 * - Admin override functionality
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  AlertCircle,
  Loader2,
  RefreshCw,
  Info,
  ShieldOff,
  ShieldCheck,
  Lock,
  Unlock,
} from 'lucide-react'
import api from '../api/client'
import type {
  ShipmentValidationReport,
  ShipmentValidationRuleResult,
  ValidationSeverity,
} from '../types'

interface ShipmentValidationPanelProps {
  shipmentId: string
  onValidationComplete?: ((report: ShipmentValidationReport) => void) | (() => void)
  isAdmin?: boolean
}

// Severity configuration
const SEVERITY_CONFIG: Record<ValidationSeverity, {
  icon: typeof AlertCircle
  color: string
  bgColor: string
  textColor: string
}> = {
  critical: {
    icon: XCircle,
    color: 'text-danger-600',
    bgColor: 'bg-danger-50',
    textColor: 'text-danger-800',
  },
  error: {
    icon: XCircle,
    color: 'text-danger-600',
    bgColor: 'bg-danger-50',
    textColor: 'text-danger-800',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-warning-600',
    bgColor: 'bg-warning-50',
    textColor: 'text-warning-800',
  },
  info: {
    icon: Info,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-800',
  },
}

// Group results by category
function groupResultsByCategory(
  results: ShipmentValidationRuleResult[]
): Record<string, ShipmentValidationRuleResult[]> {
  return results.reduce((acc, result) => {
    const category = result.category || 'General'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(result)
    return acc
  }, {} as Record<string, ShipmentValidationRuleResult[]>)
}

export default function ShipmentValidationPanel({
  shipmentId,
  onValidationComplete,
  isAdmin = false,
}: ShipmentValidationPanelProps) {
  const [report, setReport] = useState<ShipmentValidationReport | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isValidating, setIsValidating] = useState(false)
  const [isOverriding, setIsOverriding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showOverrideModal, setShowOverrideModal] = useState(false)
  const [overrideReason, setOverrideReason] = useState('')

  // Fetch existing validation report
  const fetchValidationReport = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const result = await api.getShipmentValidationReport(shipmentId)
      setReport(result)
    } catch (err) {
      console.error('Failed to fetch validation report:', err)
      setError('Failed to load validation report')
    } finally {
      setIsLoading(false)
    }
  }, [shipmentId])

  useEffect(() => {
    fetchValidationReport()
  }, [fetchValidationReport])

  // Run validation
  const handleValidate = async () => {
    setIsValidating(true)
    setError(null)

    try {
      const result = await api.validateShipment(shipmentId)
      setReport(result)
      onValidationComplete?.(result)
    } catch (err) {
      console.error('Failed to validate shipment:', err)
      setError(err instanceof Error ? err.message : 'Failed to validate shipment')
    } finally {
      setIsValidating(false)
    }
  }

  // Override validation (admin only)
  const handleOverride = async () => {
    if (!overrideReason.trim()) {
      setError('Please provide a reason for the override')
      return
    }

    setIsOverriding(true)
    setError(null)

    try {
      const result = await api.overrideShipmentValidation(shipmentId, {
        reason: overrideReason.trim(),
      })
      setReport(result)
      setShowOverrideModal(false)
      setOverrideReason('')
      onValidationComplete?.(result)
    } catch (err) {
      console.error('Failed to override validation:', err)
      setError(err instanceof Error ? err.message : 'Failed to override validation')
    } finally {
      setIsOverriding(false)
    }
  }

  // Clear override (admin only)
  const handleClearOverride = async () => {
    setIsOverriding(true)
    setError(null)

    try {
      const result = await api.clearValidationOverride(shipmentId)
      setReport(result)
      onValidationComplete?.(result)
    } catch (err) {
      console.error('Failed to clear override:', err)
      setError(err instanceof Error ? err.message : 'Failed to clear override')
    } finally {
      setIsOverriding(false)
    }
  }

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  // No report yet - show validate button
  if (!report) {
    return (
      <div className="card p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Shield className="h-6 w-6 text-gray-400" />
          <div>
            <h3 className="font-semibold text-gray-900">Shipment Validation</h3>
            <p className="text-sm text-gray-500">Run validation to check compliance</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center space-x-2 text-sm text-danger-600 bg-danger-50 p-3 rounded mb-4">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          onClick={handleValidate}
          disabled={isValidating}
          className="btn-primary w-full justify-center"
        >
          {isValidating ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Validating...
            </>
          ) : (
            <>
              <Shield className="h-4 w-4 mr-2" />
              Run Validation
            </>
          )}
        </button>
      </div>
    )
  }

  const { summary, results, override, validated_at, product_type } = report
  const isValid = summary.is_valid || Boolean(override)
  const hasOverride = Boolean(override)
  const groupedResults = groupResultsByCategory(results)

  return (
    <div className="card overflow-hidden">
      {/* Header with Status */}
      <div
        className={`p-4 border-b ${
          hasOverride
            ? 'bg-blue-50 border-blue-200'
            : isValid
            ? 'bg-success-50 border-success-200'
            : 'bg-danger-50 border-danger-200'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {hasOverride ? (
              <Lock className="h-6 w-6 text-blue-600" />
            ) : isValid ? (
              <ShieldCheck className="h-6 w-6 text-success-600" />
            ) : (
              <ShieldOff className="h-6 w-6 text-danger-600" />
            )}
            <div>
              <h3 className="font-semibold text-gray-900">Validation Status</h3>
              <p
                className={`text-sm ${
                  hasOverride
                    ? 'text-blue-600'
                    : isValid
                    ? 'text-success-600'
                    : 'text-danger-600'
                }`}
              >
                {hasOverride ? 'Overridden (Valid)' : isValid ? 'Valid' : 'Invalid'}
              </p>
            </div>
          </div>
          <span className="text-sm text-gray-600 bg-white px-2 py-1 rounded">
            {product_type}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Override Banner */}
        {override && (
          <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded border border-blue-200">
            <Lock className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-blue-800">Admin Override Active</p>
              <p className="text-xs text-blue-600 mt-0.5">
                Overridden by {override.overridden_by} on{' '}
                {new Date(override.overridden_at).toLocaleDateString()}
              </p>
              <p className="text-xs text-blue-700 mt-1 italic">
                Reason: {override.reason}
              </p>
            </div>
            {isAdmin && (
              <button
                onClick={handleClearOverride}
                disabled={isOverriding}
                className="text-xs text-blue-600 hover:text-blue-800 underline"
              >
                Clear
              </button>
            )}
          </div>
        )}

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
            <div className="font-semibold text-danger-700">{summary.failed}</div>
            <div className="text-xs text-danger-600">Failed</div>
          </div>
          <div className="text-center p-2 bg-warning-50 rounded">
            <div className="font-semibold text-warning-700">{summary.warnings}</div>
            <div className="text-xs text-warning-600">Warnings</div>
          </div>
        </div>

        {/* Rule Results by Category */}
        {Object.keys(groupedResults).length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Validation Rules</h4>
            {Object.entries(groupedResults).map(([category, categoryResults]) => (
              <div key={category} className="space-y-1">
                <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  {category}
                </h5>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {categoryResults.map((rule) => {
                    const severityConfig = SEVERITY_CONFIG[rule.severity]
                    const RuleIcon = rule.passed ? CheckCircle : severityConfig.icon

                    return (
                      <div
                        key={rule.rule_id}
                        className={`flex items-start space-x-2 p-2 rounded text-sm ${
                          rule.passed ? 'bg-success-50' : severityConfig.bgColor
                        }`}
                      >
                        <RuleIcon
                          className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                            rule.passed ? 'text-success-600' : severityConfig.color
                          }`}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span
                              className={`font-medium ${
                                rule.passed ? 'text-success-800' : severityConfig.textColor
                              }`}
                            >
                              {rule.rule_name}
                            </span>
                            <span
                              className={`text-xs px-1.5 py-0.5 rounded ${
                                rule.passed
                                  ? 'bg-success-100 text-success-700'
                                  : `${severityConfig.bgColor} ${severityConfig.color}`
                              }`}
                            >
                              {rule.severity}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mt-0.5">{rule.message}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
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
            onClick={handleValidate}
            disabled={isValidating}
            className="btn-secondary flex-1 justify-center"
          >
            {isValidating ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Re-validate
          </button>

          {isAdmin && !hasOverride && !isValid && (
            <button
              onClick={() => setShowOverrideModal(true)}
              className="btn-secondary flex-1 justify-center"
            >
              <Unlock className="h-4 w-4 mr-2" />
              Override
            </button>
          )}
        </div>
      </div>

      {/* Footer with timestamp */}
      {validated_at && (
        <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
          Last validated: {new Date(validated_at).toLocaleString()}
        </div>
      )}

      {/* Override Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black/50 transition-opacity"
              onClick={() => setShowOverrideModal(false)}
            />

            {/* Modal */}
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Override Validation
              </h3>

              <p className="text-sm text-gray-600 mb-4">
                Override the validation status for this shipment. This action will be
                logged for audit purposes.
              </p>

              <div className="mb-4">
                <label
                  htmlFor="override-reason"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Reason for Override *
                </label>
                <textarea
                  id="override-reason"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Enter the reason for this override..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  rows={3}
                />
              </div>

              {error && (
                <div className="flex items-center space-x-2 text-sm text-danger-600 bg-danger-50 p-2 rounded mb-4">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setShowOverrideModal(false)
                    setOverrideReason('')
                    setError(null)
                  }}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleOverride}
                  disabled={isOverriding || !overrideReason.trim()}
                  className="btn-primary flex-1"
                >
                  {isOverriding ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Overriding...
                    </>
                  ) : (
                    'Confirm Override'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
