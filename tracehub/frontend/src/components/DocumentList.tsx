import { FileText, CheckCircle, AlertCircle, Clock, Upload, Download, Layers, ChevronRight } from 'lucide-react'
import type { Document, DocumentType, DocumentStatus } from '../types'
import { format } from 'date-fns'

interface DocumentListProps {
  documents: Document[]
  missingDocuments?: DocumentType[]
  onUpload?: (type: DocumentType) => void
  onDocumentClick?: (doc: Document) => void
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

const STATUS_CONFIG: Record<DocumentStatus, { icon: typeof CheckCircle; color: string; label: string }> = {
  draft: { icon: Clock, color: 'text-gray-400', label: 'Draft' },
  uploaded: { icon: Clock, color: 'text-warning-500', label: 'Pending Review' },
  validated: { icon: CheckCircle, color: 'text-success-500', label: 'Validated' },
  compliance_ok: { icon: CheckCircle, color: 'text-success-500', label: 'Compliant' },
  compliance_failed: { icon: AlertCircle, color: 'text-danger-500', label: 'Issues Found' },
  linked: { icon: CheckCircle, color: 'text-primary-500', label: 'Linked' },
  archived: { icon: CheckCircle, color: 'text-gray-400', label: 'Archived' },
}

export default function DocumentList({ documents, missingDocuments = [], onUpload, onDocumentClick }: DocumentListProps) {
  return (
    <div className="space-y-4">
      {/* Present Documents */}
      {documents.map((doc) => {
        const statusConfig = STATUS_CONFIG[doc.status] || STATUS_CONFIG.draft
        const StatusIcon = statusConfig.icon
        const isCombined = doc.is_combined || (doc.document_types && doc.document_types.length > 1)

        return (
          <div
            key={doc.id}
            onClick={() => onDocumentClick?.(doc)}
            className={`p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors ${
              onDocumentClick ? 'cursor-pointer hover:bg-gray-50' : ''
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`p-2 rounded-lg ${isCombined ? 'bg-primary-100' : 'bg-gray-100'}`}>
                  {isCombined ? (
                    <Layers className="h-5 w-5 text-primary-600" />
                  ) : (
                    <FileText className="h-5 w-5 text-gray-600" />
                  )}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium text-gray-900">
                      {DOCUMENT_LABELS[doc.document_type] || doc.document_type}
                    </h4>
                    {isCombined && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 text-primary-700 rounded-full">
                        {doc.content_count || doc.document_types?.length || 0} docs
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-3 text-sm text-gray-500 mt-1">
                    {doc.reference_number && (
                      <span className="font-mono">{doc.reference_number}</span>
                    )}
                    {doc.page_count && doc.page_count > 1 && (
                      <span>{doc.page_count} pages</span>
                    )}
                    {doc.issue_date && (
                      <span>Issued: {format(new Date(doc.issue_date), 'MMM d, yyyy')}</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className={`flex items-center ${statusConfig.color}`}>
                  <StatusIcon className="h-4 w-4 mr-1" />
                  <span className="text-sm">{statusConfig.label}</span>
                </div>
                {doc.file_path && (
                  <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                    <Download className="h-4 w-4" />
                  </button>
                )}
                {isCombined && onDocumentClick && (
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                )}
              </div>
            </div>

            {/* Show contained document types for combined PDFs */}
            {isCombined && doc.document_types && doc.document_types.length > 1 && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="flex flex-wrap gap-2">
                  {doc.document_types.map((type, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                    >
                      {DOCUMENT_LABELS[type as DocumentType] || type}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })}

      {/* Missing Documents */}
      {missingDocuments.map((docType) => (
        <div
          key={docType}
          className="flex items-center justify-between p-4 bg-danger-50 rounded-lg border border-danger-200"
        >
          <div className="flex items-center space-x-4">
            <div className="p-2 bg-danger-100 rounded-lg">
              <AlertCircle className="h-5 w-5 text-danger-600" />
            </div>
            <div>
              <h4 className="font-medium text-danger-900">
                {DOCUMENT_LABELS[docType] || docType}
              </h4>
              <p className="text-sm text-danger-600 mt-1">
                Required document missing
              </p>
            </div>
          </div>

          {onUpload && (
            <button
              onClick={() => onUpload(docType)}
              className="flex items-center px-3 py-2 bg-danger-600 text-white rounded-md hover:bg-danger-700 transition-colors text-sm"
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </button>
          )}
        </div>
      ))}

      {documents.length === 0 && missingDocuments.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <FileText className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No documents yet</p>
        </div>
      )}
    </div>
  )
}
