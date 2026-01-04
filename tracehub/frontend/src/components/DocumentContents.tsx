/**
 * DocumentContents Component
 *
 * Displays individual document types detected within a combined PDF.
 * Shows validation status, page ranges, and allows per-type validation.
 */

import { useState, useEffect } from 'react'
import {
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Hash,
} from 'lucide-react'
import api from '../api/client'
import type { DocumentContent, DocumentType, DocumentStatus } from '../types'

interface DocumentContentsProps {
  documentId: string
  onValidate?: (contentId: string) => void
  onReject?: (contentId: string, reason: string) => void
  onUpdate?: () => void
}

const DOCUMENT_LABELS: Record<DocumentType, string> = {
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
  other: 'Other Document',
}

const STATUS_CONFIG: Record<DocumentStatus, { icon: typeof CheckCircle; color: string; bgColor: string; label: string }> = {
  draft: { icon: Clock, color: 'text-gray-500', bgColor: 'bg-gray-100', label: 'Draft' },
  uploaded: { icon: Clock, color: 'text-warning-600', bgColor: 'bg-warning-100', label: 'Pending Review' },
  validated: { icon: CheckCircle, color: 'text-success-600', bgColor: 'bg-success-100', label: 'Validated' },
  compliance_ok: { icon: CheckCircle, color: 'text-success-600', bgColor: 'bg-success-100', label: 'Compliant' },
  compliance_failed: { icon: AlertCircle, color: 'text-danger-600', bgColor: 'bg-danger-100', label: 'Issues Found' },
  linked: { icon: CheckCircle, color: 'text-primary-600', bgColor: 'bg-primary-100', label: 'Linked' },
  archived: { icon: CheckCircle, color: 'text-gray-500', bgColor: 'bg-gray-100', label: 'Archived' },
}

export default function DocumentContents({
  documentId,
  onValidate,
  onReject,
  onUpdate,
}: DocumentContentsProps) {
  const [contents, setContents] = useState<DocumentContent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [expandedContent, setExpandedContent] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchContents()
  }, [documentId])

  const fetchContents = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await api.getDocumentContents(documentId)
      setContents(response.contents as DocumentContent[] || [])
    } catch (err) {
      console.error('Failed to fetch document contents:', err)
      setError('Failed to load document contents')
    } finally {
      setIsLoading(false)
    }
  }

  const handleValidate = async (contentId: string) => {
    try {
      await api.validateDocumentContent(documentId, contentId)
      fetchContents()
      onUpdate?.()
    } catch (err) {
      console.error('Failed to validate content:', err)
    }
  }

  const handleReject = async (contentId: string, reason: string) => {
    try {
      await api.rejectDocumentContent(documentId, contentId, reason)
      fetchContents()
      onUpdate?.()
    } catch (err) {
      console.error('Failed to reject content:', err)
    }
  }

  const getConfidenceBadge = (confidence: number, method: string) => {
    if (method === 'manual') {
      return (
        <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full">
          Manual
        </span>
      )
    }

    const percent = Math.round(confidence * 100)
    let color = 'bg-danger-100 text-danger-700'
    if (percent >= 80) color = 'bg-success-100 text-success-700'
    else if (percent >= 60) color = 'bg-warning-100 text-warning-700'

    return (
      <span className={`px-2 py-0.5 text-xs rounded-full flex items-center gap-1 ${color}`}>
        {method === 'ai' && <Sparkles className="h-3 w-3" />}
        {percent}%
      </span>
    )
  }

  if (isLoading) {
    return (
      <div className="p-4 space-y-3 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-gray-100 rounded-lg"></div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-center text-danger-600">
        <AlertCircle className="h-8 w-8 mx-auto mb-2" />
        <p>{error}</p>
      </div>
    )
  }

  if (contents.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <FileText className="h-8 w-8 mx-auto mb-2 text-gray-400" />
        <p>No document contents detected</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-700">
          Detected Documents ({contents.length})
        </h3>
        <div className="text-xs text-gray-500">
          Click to expand for details
        </div>
      </div>

      {contents.map((content) => {
        const statusConfig = STATUS_CONFIG[content.status] || STATUS_CONFIG.uploaded
        const StatusIcon = statusConfig.icon
        const isExpanded = expandedContent === content.id

        return (
          <div
            key={content.id}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            {/* Header - always visible */}
            <div
              onClick={() => setExpandedContent(isExpanded ? null : content.id)}
              className="flex items-center justify-between p-3 bg-white hover:bg-gray-50 cursor-pointer"
            >
              <div className="flex items-center space-x-3">
                <div className={`p-1.5 rounded ${statusConfig.bgColor}`}>
                  <StatusIcon className={`h-4 w-4 ${statusConfig.color}`} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-gray-900">
                      {DOCUMENT_LABELS[content.document_type] || content.document_type}
                    </span>
                    {getConfidenceBadge(content.confidence, content.detection_method)}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                    <span>Pages {content.page_start}-{content.page_end}</span>
                    {content.reference_number && (
                      <>
                        <span>•</span>
                        <span className="font-mono flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          {content.reference_number}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span className={`text-xs ${statusConfig.color}`}>
                  {statusConfig.label}
                </span>
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                )}
              </div>
            </div>

            {/* Expanded details */}
            {isExpanded && (
              <div className="px-3 pb-3 border-t border-gray-100 bg-gray-50">
                <div className="pt-3 space-y-3">
                  {/* Detected fields */}
                  {content.detected_fields && Object.keys(content.detected_fields).length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 mb-1">Detected Fields</p>
                      <div className="text-xs text-gray-600 bg-white p-2 rounded border border-gray-200">
                        {Object.entries(content.detected_fields).map(([key, value]) => (
                          <div key={key} className="flex justify-between py-0.5">
                            <span className="text-gray-500">{key}:</span>
                            <span className="font-mono">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Validation info */}
                  {content.validated_at && (
                    <div className="text-xs text-gray-500">
                      Validated by {content.validated_by} on{' '}
                      {new Date(content.validated_at).toLocaleDateString()}
                    </div>
                  )}

                  {content.validation_notes && (
                    <div className="text-xs text-gray-600 bg-white p-2 rounded border border-gray-200">
                      {content.validation_notes}
                    </div>
                  )}

                  {/* Actions */}
                  {content.status === 'uploaded' && (onValidate || onReject) && (
                    <div className="flex gap-2 pt-2">
                      {onValidate && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleValidate(content.id)
                          }}
                          className="flex-1 px-3 py-1.5 text-xs font-medium bg-success-600 text-white rounded hover:bg-success-700"
                        >
                          <CheckCircle className="h-3 w-3 inline mr-1" />
                          Validate
                        </button>
                      )}
                      {onReject && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            const reason = prompt('Enter rejection reason:')
                            if (reason) handleReject(content.id, reason)
                          }}
                          className="flex-1 px-3 py-1.5 text-xs font-medium bg-danger-600 text-white rounded hover:bg-danger-700"
                        >
                          <AlertCircle className="h-3 w-3 inline mr-1" />
                          Reject
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
