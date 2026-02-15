import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type {
  Document,
  DocumentValidationResponse,
  DocumentTransitionsResponse,
  DocumentStatus,
  DocumentIssue,
  IssueSeverity,
} from '../types'
import BolCompliancePanel from './BolCompliancePanel'

interface DocumentReviewPanelProps {
  document: Document
  onClose: () => void
  onUpdate: () => void
}

// Issue severity colors and icons
const SEVERITY_CONFIG: Record<IssueSeverity, { color: string; bgColor: string; icon: string }> = {
  ERROR: { color: 'text-red-700', bgColor: 'bg-red-50 border-red-200', icon: '⚠️' },
  WARNING: { color: 'text-yellow-700', bgColor: 'bg-yellow-50 border-yellow-200', icon: '⚡' },
  INFO: { color: 'text-blue-700', bgColor: 'bg-blue-50 border-blue-200', icon: 'ℹ️' },
}

const STATUS_COLORS: Record<string, string> = {
  gray: 'bg-gray-100 text-gray-800',
  yellow: 'bg-yellow-100 text-yellow-800',
  blue: 'bg-blue-100 text-blue-800',
  green: 'bg-green-100 text-green-800',
  red: 'bg-red-100 text-red-800',
}

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  bill_of_lading: 'Bill of Lading',
  commercial_invoice: 'Commercial Invoice',
  packing_list: 'Packing List',
  certificate_of_origin: 'Certificate of Origin',
  phytosanitary_certificate: 'Phytosanitary Certificate',
  fumigation_certificate: 'Fumigation Certificate',
  sanitary_certificate: 'Sanitary Certificate',
  insurance_certificate: 'Insurance Certificate',
  customs_declaration: 'Customs Declaration',
  contract: 'Contract',
  eudr_due_diligence: 'EUDR Due Diligence',
  quality_certificate: 'Quality Certificate',
  // Horn & Hoof specific documents (HS 0506/0507)
  eu_traces_certificate: 'EU TRACES Certificate',
  veterinary_health_certificate: 'Veterinary Health Certificate',
  export_declaration: 'Export Declaration',
  other: 'Other',
}

export default function DocumentReviewPanel({
  document,
  onClose,
  onUpdate,
}: DocumentReviewPanelProps) {
  const [validation, setValidation] = useState<DocumentValidationResponse | null>(null)
  const [transitions, setTransitions] = useState<DocumentTransitionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [showDeleteForm, setShowDeleteForm] = useState(false)
  const [deleteReason, setDeleteReason] = useState('')
  const [deleteLoading, setDeleteLoading] = useState(false)
  // Document validation issues state
  const [issues, setIssues] = useState<DocumentIssue[]>([])
  const [overrideIssueId, setOverrideIssueId] = useState<string | null>(null)
  const [overrideReason, setOverrideReason] = useState('')
  const [overrideLoading, setOverrideLoading] = useState(false)

  useEffect(() => {
    loadDocumentDetails()
  }, [document.id])

  const loadDocumentDetails = async () => {
    try {
      setLoading(true)
      setError(null)

      const [validationData, transitionsData] = await Promise.all([
        api.getDocumentValidation(document.id),
        api.getDocumentTransitions(document.id),
      ])

      setValidation(validationData)
      setTransitions(transitionsData)

      // Load document issues if the API exists
      try {
        const issuesResponse = await api.getDocumentIssues(document.id)
        if (issuesResponse && issuesResponse.issues) {
          setIssues(issuesResponse.issues)
        }
      } catch {
        // Issues endpoint may not exist yet, silently ignore
        setIssues([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document details')
    } finally {
      setLoading(false)
    }
  }

  const handleOverrideIssue = async (issueId: string) => {
    if (overrideReason.trim().length < 10) {
      setError('Override reason must be at least 10 characters')
      return
    }

    try {
      setOverrideLoading(true)
      setError(null)
      await api.overrideDocumentIssue(document.id, issueId, overrideReason)

      // Update the issue in local state
      setIssues(prev => prev.map(issue =>
        issue.id === issueId
          ? { ...issue, is_overridden: true, override_reason: overrideReason }
          : issue
      ))

      setOverrideIssueId(null)
      setOverrideReason('')
      onUpdate()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to override issue')
    } finally {
      setOverrideLoading(false)
    }
  }

  const getBlockingIssues = () => issues.filter(i => i.severity === 'ERROR' && !i.is_overridden)
  const getWarningIssues = () => issues.filter(i => i.severity === 'WARNING' && !i.is_overridden)
  const getOverriddenIssues = () => issues.filter(i => i.is_overridden)

  const handleApprove = async () => {
    try {
      setActionLoading(true)
      setError(null)
      await api.approveDocument(document.id, notes || undefined)
      onUpdate()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve document')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async () => {
    if (!notes.trim()) {
      setError('Rejection notes are required')
      return
    }

    try {
      setActionLoading(true)
      setError(null)
      await api.rejectDocument(document.id, notes)
      onUpdate()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject document')
    } finally {
      setActionLoading(false)
    }
  }

  const handleTransition = async (targetStatus: DocumentStatus) => {
    try {
      setActionLoading(true)
      setError(null)
      await api.transitionDocument(document.id, targetStatus, notes || undefined)
      onUpdate()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to transition document')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      const result = await api.downloadDocument(document.id)
      if (typeof result === 'string') {
        // Signed URL from Supabase Storage — open in new tab
        window.open(result, '_blank')
      } else {
        // Blob from v1 local storage — download directly
        const url = URL.createObjectURL(result)
        const a = window.document.createElement('a')
        a.href = url
        a.download = document.file_name || document.name
        window.document.body.appendChild(a)
        a.click()
        window.document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download document')
    }
  }

  const handleDelete = async () => {
    if (deleteReason.trim().length < 5) {
      setError('Deletion reason must be at least 5 characters')
      return
    }

    try {
      setDeleteLoading(true)
      setError(null)
      await api.deleteDocument(document.id, deleteReason.trim())
      onUpdate()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document')
    } finally {
      setDeleteLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading document details...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Document Review</h2>
            <p className="text-sm text-gray-500">
              {DOCUMENT_TYPE_LABELS[document.document_type] || document.document_type}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Document Info */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Document Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Name:</span>
                <p className="font-medium">{document.name}</p>
              </div>
              <div>
                <span className="text-gray-500">Status:</span>
                <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                  STATUS_COLORS[validation?.status_info?.color || 'gray']
                }`}>
                  {validation?.status_info?.display || document.status}
                </span>
              </div>
              {document.reference_number && (
                <div>
                  <span className="text-gray-500">Reference:</span>
                  <p className="font-medium">{document.reference_number}</p>
                </div>
              )}
              {document.document_date && (
                <div>
                  <span className="text-gray-500">Issue Date:</span>
                  <p className="font-medium">{new Date(document.document_date).toLocaleDateString()}</p>
                </div>
              )}
              {document.expiry_date && (
                <div>
                  <span className="text-gray-500">Expiry Date:</span>
                  <p className="font-medium">{new Date(document.expiry_date).toLocaleDateString()}</p>
                </div>
              )}
              {document.issuer && (
                <div>
                  <span className="text-gray-500">Issuing Authority:</span>
                  <p className="font-medium">{document.issuer}</p>
                </div>
              )}
            </div>

            <div className="mt-4 flex gap-2 flex-wrap">
              {document.file_name && (
                <button
                  onClick={handleDownload}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download
                </button>
              )}
              <button
                onClick={() => setShowDeleteForm(true)}
                className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            </div>
          </div>

          {/* Delete Confirmation Form */}
          {showDeleteForm && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="font-medium text-red-900 mb-3">Delete Document</h3>
              <p className="text-sm text-red-700 mb-3">
                This action cannot be undone. Please provide a reason for deleting this document.
              </p>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-red-800 mb-1">
                    Reason for Deletion <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={deleteReason}
                    onChange={(e) => setDeleteReason(e.target.value)}
                    placeholder="Explain why this document is being deleted (min 5 characters)..."
                    rows={3}
                    className="w-full px-3 py-2 border border-red-300 rounded-md text-sm focus:ring-red-500 focus:border-red-500"
                    required
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleDelete}
                    disabled={deleteLoading || deleteReason.trim().length < 5}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {deleteLoading ? 'Deleting...' : 'Confirm Delete'}
                  </button>
                  <button
                    onClick={() => {
                      setShowDeleteForm(false)
                      setDeleteReason('')
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* BoL Compliance Panel - Only for Bill of Lading documents */}
          {document.document_type === 'bill_of_lading' && (
            <BolCompliancePanel
              documentId={document.id}
              shipmentId={document.shipment_id}
              onSyncComplete={onUpdate}
            />
          )}

          {/* Document Validation Issues */}
          {issues.length > 0 && (
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3 flex items-center justify-between">
                <span>Validation Issues</span>
                <span className="text-sm font-normal">
                  {getBlockingIssues().length > 0 && (
                    <span className="text-red-600 mr-2">
                      {getBlockingIssues().length} blocking
                    </span>
                  )}
                  {getWarningIssues().length > 0 && (
                    <span className="text-yellow-600">
                      {getWarningIssues().length} warnings
                    </span>
                  )}
                </span>
              </h3>

              <div className="space-y-3">
                {/* Blocking errors (not overridden) */}
                {getBlockingIssues().map((issue) => (
                  <div
                    key={issue.id}
                    className={`p-3 rounded-md border ${SEVERITY_CONFIG.ERROR.bgColor}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span>{SEVERITY_CONFIG.ERROR.icon}</span>
                          <span className={`font-medium ${SEVERITY_CONFIG.ERROR.color}`}>
                            {issue.rule_name}
                          </span>
                          <span className="text-xs bg-red-200 text-red-800 px-2 py-0.5 rounded">
                            BLOCKING
                          </span>
                        </div>
                        <p className="text-sm text-red-600 mt-1">{issue.message}</p>
                        {issue.field && (
                          <p className="text-xs text-red-500 mt-1">
                            Field: {issue.field}
                            {issue.expected_value && ` (expected: ${issue.expected_value})`}
                            {issue.actual_value && ` (actual: ${issue.actual_value})`}
                          </p>
                        )}
                      </div>
                      {overrideIssueId !== issue.id && (
                        <button
                          onClick={() => setOverrideIssueId(issue.id)}
                          className="text-xs px-2 py-1 border border-red-300 rounded text-red-700 hover:bg-red-100"
                        >
                          Override
                        </button>
                      )}
                    </div>

                    {/* Override form for this issue */}
                    {overrideIssueId === issue.id && (
                      <div className="mt-3 pt-3 border-t border-red-200">
                        <label className="block text-sm font-medium text-red-800 mb-1">
                          Override Reason (min 10 characters)
                        </label>
                        <textarea
                          value={overrideReason}
                          onChange={(e) => setOverrideReason(e.target.value)}
                          placeholder="Explain why this issue should be overridden..."
                          rows={2}
                          className="w-full px-3 py-2 border border-red-300 rounded-md text-sm"
                        />
                        <div className="flex gap-2 mt-2">
                          <button
                            onClick={() => handleOverrideIssue(issue.id)}
                            disabled={overrideLoading || overrideReason.trim().length < 10}
                            className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50"
                          >
                            {overrideLoading ? 'Overriding...' : 'Confirm Override'}
                          </button>
                          <button
                            onClick={() => {
                              setOverrideIssueId(null)
                              setOverrideReason('')
                            }}
                            className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Warnings (not overridden) */}
                {getWarningIssues().map((issue) => (
                  <div
                    key={issue.id}
                    className={`p-3 rounded-md border ${SEVERITY_CONFIG.WARNING.bgColor}`}
                  >
                    <div className="flex items-center gap-2">
                      <span>{SEVERITY_CONFIG.WARNING.icon}</span>
                      <span className={`font-medium ${SEVERITY_CONFIG.WARNING.color}`}>
                        {issue.rule_name}
                      </span>
                    </div>
                    <p className="text-sm text-yellow-600 mt-1">{issue.message}</p>
                  </div>
                ))}

                {/* Overridden issues (collapsed by default) */}
                {getOverriddenIssues().length > 0 && (
                  <details className="mt-2">
                    <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                      Show {getOverriddenIssues().length} overridden issue(s)
                    </summary>
                    <div className="mt-2 space-y-2">
                      {getOverriddenIssues().map((issue) => (
                        <div
                          key={issue.id}
                          className="p-2 rounded-md bg-gray-50 border border-gray-200 opacity-70"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-gray-400 line-through">{issue.rule_name}</span>
                            <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
                              OVERRIDDEN
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            Reason: {issue.override_reason}
                          </p>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            </div>
          )}

          {/* Validation Status */}
          {validation && (
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3">Validation Status</h3>

              <div className={`p-3 rounded-md mb-4 ${
                validation.validation.is_valid
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-center">
                  {validation.validation.is_valid ? (
                    <>
                      <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="font-medium text-green-800">All validation checks passed</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <span className="font-medium text-red-800">
                        {validation.validation.total_issues} validation issue(s) found
                      </span>
                    </>
                  )}
                </div>
              </div>

              {validation.validation.errors.length > 0 && (
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-red-800 mb-2">Errors</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {validation.validation.errors.map((error, i) => (
                      <li key={i} className="text-sm text-red-700">{error}</li>
                    ))}
                  </ul>
                </div>
              )}

              {validation.validation.warnings.length > 0 && (
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-yellow-800 mb-2">Warnings</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {validation.validation.warnings.map((warning, i) => (
                      <li key={i} className="text-sm text-yellow-700">{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Required Fields */}
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Required Fields</h4>
                <div className="grid grid-cols-2 gap-2">
                  {validation.required_fields.map((field, i) => (
                    <div
                      key={i}
                      className={`text-sm px-2 py-1 rounded ${
                        field.severity === 'error'
                          ? 'bg-red-50 text-red-700'
                          : field.severity === 'warning'
                          ? 'bg-yellow-50 text-yellow-700'
                          : 'bg-gray-50 text-gray-700'
                      }`}
                    >
                      {field.description}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Available Actions */}
          {transitions && transitions.allowed_transitions.length > 0 && (
            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3">Available Actions</h3>

              {!showRejectForm ? (
                <div className="space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {/* Quick approve/reject buttons for common states */}
                    {document.status === 'uploaded' && (
                      <>
                        <button
                          onClick={handleApprove}
                          disabled={actionLoading}
                          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                        >
                          Validate Document
                        </button>
                        <button
                          onClick={() => setShowRejectForm(true)}
                          disabled={actionLoading}
                          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                        >
                          Reject
                        </button>
                      </>
                    )}

                    {document.status === 'validated' && (
                      <>
                        <button
                          onClick={handleApprove}
                          disabled={actionLoading}
                          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                        >
                          Approve Compliance
                        </button>
                        <button
                          onClick={() => setShowRejectForm(true)}
                          disabled={actionLoading}
                          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                        >
                          Fail Compliance
                        </button>
                      </>
                    )}

                    {document.status === 'compliance_ok' && (
                      <button
                        onClick={handleApprove}
                        disabled={actionLoading}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                      >
                        Link to Shipment
                      </button>
                    )}
                  </div>

                  {/* Optional notes for approval */}
                  {['uploaded', 'validated', 'compliance_ok'].includes(document.status) && (
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">
                        Notes (optional)
                      </label>
                      <input
                        type="text"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Add optional notes..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </div>
                  )}

                  {/* All available transitions */}
                  <details className="mt-4">
                    <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                      Show all transitions
                    </summary>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {transitions.allowed_transitions.map((transition) => (
                        <button
                          key={transition.status}
                          onClick={() => handleTransition(transition.status)}
                          disabled={actionLoading}
                          className={`px-3 py-1 text-sm rounded-md border ${
                            STATUS_COLORS[transition.info.color]
                          } disabled:opacity-50`}
                        >
                          → {transition.info.display}
                        </button>
                      ))}
                    </div>
                  </details>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Rejection Reason <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Explain why this document is being rejected..."
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      required
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleReject}
                      disabled={actionLoading || !notes.trim()}
                      className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                    >
                      Confirm Rejection
                    </button>
                    <button
                      onClick={() => {
                        setShowRejectForm(false)
                        setNotes('')
                      }}
                      className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Audit Trail */}
          <div className="text-sm text-gray-500 space-y-1">
            {document.uploaded_by && document.created_at && (
              <p>
                Uploaded by {document.uploaded_by} on{' '}
                {new Date(document.created_at).toLocaleString()}
              </p>
            )}
            {document.validated_by && document.validated_at && (
              <p>
                Validated by {document.validated_by} on{' '}
                {new Date(document.validated_at).toLocaleString()}
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
