import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type {
  Document,
  DocumentValidationResponse,
  DocumentTransitionsResponse,
  DocumentStatus,
} from '../types'

interface DocumentReviewPanelProps {
  document: Document
  onClose: () => void
  onUpdate: () => void
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document details')
    } finally {
      setLoading(false)
    }
  }

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
      const blob = await api.downloadDocument(document.id)
      const url = URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url
      a.download = document.file_name || document.name
      window.document.body.appendChild(a)
      a.click()
      window.document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download document')
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

            {document.file_name && (
              <button
                onClick={handleDownload}
                className="mt-4 inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download Document
              </button>
            )}
          </div>

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
            {document.uploaded_by && document.uploaded_at && (
              <p>
                Uploaded by {document.uploaded_by} on{' '}
                {new Date(document.uploaded_at).toLocaleString()}
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
