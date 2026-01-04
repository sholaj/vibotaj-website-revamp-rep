import { CheckCircle, AlertTriangle, XCircle, FileCheck } from 'lucide-react'
import type { ComplianceStatus as ComplianceStatusType, DocumentType } from '../types'

interface ComplianceStatusProps {
  compliance: ComplianceStatusType
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
  // Horn & Hoof specific documents (HS 0506/0507)
  eu_traces_certificate: 'EU TRACES Certificate',
  veterinary_health_certificate: 'Veterinary Health Certificate',
  export_declaration: 'Export Declaration',
  other: 'Other Document',
}

export default function ComplianceStatus({ compliance }: ComplianceStatusProps) {
  const percentage = compliance.total_required > 0
    ? Math.round((compliance.total_present / compliance.total_required) * 100)
    : 0

  return (
    <div className="space-y-4">
      {/* Overall Status */}
      <div className={`p-4 rounded-lg ${compliance.is_compliant ? 'bg-success-50 border border-success-200' : 'bg-danger-50 border border-danger-200'}`}>
        <div className="flex items-center">
          {compliance.is_compliant ? (
            <CheckCircle className="h-6 w-6 text-success-600 mr-3" />
          ) : (
            <AlertTriangle className="h-6 w-6 text-danger-600 mr-3" />
          )}
          <div>
            <h3 className={`font-medium ${compliance.is_compliant ? 'text-success-900' : 'text-danger-900'}`}>
              {compliance.is_compliant ? 'Documentation Complete' : 'Documentation Incomplete'}
            </h3>
            <p className={`text-sm mt-1 ${compliance.is_compliant ? 'text-success-700' : 'text-danger-700'}`}>
              {compliance.total_present} of {compliance.total_required} required documents present
            </p>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div>
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Compliance Progress</span>
          <span>{percentage}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${compliance.is_compliant ? 'bg-success-500' : 'bg-warning-500'}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Missing Documents */}
      {compliance.missing_documents.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Missing Documents</h4>
          <ul className="space-y-2">
            {compliance.missing_documents.map((docType) => (
              <li key={docType} className="flex items-center text-sm text-danger-600">
                <XCircle className="h-4 w-4 mr-2" />
                {DOCUMENT_LABELS[docType] || docType}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pending Validation */}
      {compliance.pending_validation.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Pending Validation</h4>
          <ul className="space-y-2">
            {compliance.pending_validation.map((docName, idx) => (
              <li key={idx} className="flex items-center text-sm text-warning-600">
                <FileCheck className="h-4 w-4 mr-2" />
                {docName}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Issues */}
      {compliance.issues.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Issues</h4>
          <ul className="space-y-2">
            {compliance.issues.map((issue, idx) => (
              <li key={idx} className="flex items-start text-sm text-danger-600">
                <AlertTriangle className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
