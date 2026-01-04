/**
 * Document Upload Modal Component
 *
 * Allows users to upload documents to a shipment with:
 * - File selection via drag & drop or click
 * - Document type selection
 * - Optional reference number
 * - Upload progress indication
 */

import { useState, useRef, useCallback } from 'react'
import { X, Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import api from '../api/client'
import type { DocumentType } from '../types'

interface DocumentUploadModalProps {
  shipmentId: string
  isOpen: boolean
  onClose: () => void
  onUploadComplete: () => void
}

const DOCUMENT_TYPES: { value: DocumentType; label: string }[] = [
  { value: 'bill_of_lading', label: 'Bill of Lading' },
  { value: 'commercial_invoice', label: 'Commercial Invoice' },
  { value: 'packing_list', label: 'Packing List' },
  { value: 'certificate_of_origin', label: 'Certificate of Origin' },
  { value: 'phytosanitary_certificate', label: 'Phytosanitary Certificate' },
  { value: 'fumigation_certificate', label: 'Fumigation Certificate' },
  { value: 'sanitary_certificate', label: 'Sanitary Certificate' },
  { value: 'insurance_certificate', label: 'Insurance Certificate' },
  { value: 'customs_declaration', label: 'Customs Declaration' },
  { value: 'eudr_due_diligence', label: 'EUDR Due Diligence' },
  { value: 'quality_certificate', label: 'Quality Certificate' },
  { value: 'contract', label: 'Contract' },
  // Horn & Hoof specific documents (HS 0506/0507)
  { value: 'eu_traces_certificate', label: 'EU TRACES Certificate' },
  { value: 'veterinary_health_certificate', label: 'Veterinary Health Certificate' },
  { value: 'export_declaration', label: 'Export Declaration' },
  { value: 'other', label: 'Other' },
]

export default function DocumentUploadModal({
  shipmentId,
  isOpen,
  onClose,
  onUploadComplete,
}: DocumentUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [documentType, setDocumentType] = useState<DocumentType>('other')
  const [referenceNumber, setReferenceNumber] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const resetForm = useCallback(() => {
    setSelectedFile(null)
    setDocumentType('other')
    setReferenceNumber('')
    setUploadStatus('idle')
    setErrorMessage('')
    setIsDragOver(false)
  }, [])

  const handleClose = useCallback(() => {
    resetForm()
    onClose()
  }, [onClose, resetForm])

  const handleFileSelect = useCallback((file: File) => {
    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]

    if (!allowedTypes.includes(file.type)) {
      setErrorMessage('Invalid file type. Please upload PDF, JPEG, PNG, or Word documents.')
      setUploadStatus('error')
      return
    }

    // Validate file size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      setErrorMessage('File too large. Maximum size is 50MB.')
      setUploadStatus('error')
      return
    }

    setSelectedFile(file)
    setUploadStatus('idle')
    setErrorMessage('')
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)

      const file = e.dataTransfer.files[0]
      if (file) {
        handleFileSelect(file)
      }
    },
    [handleFileSelect]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadStatus('idle')
    setErrorMessage('')

    try {
      await api.uploadDocument(shipmentId, selectedFile, documentType, {
        reference_number: referenceNumber || undefined,
      })

      setUploadStatus('success')

      // Wait a moment to show success, then close
      setTimeout(() => {
        handleClose()
        onUploadComplete()
      }, 1500)
    } catch (err) {
      console.error('Upload failed:', err)
      setUploadStatus('error')
      setErrorMessage(err instanceof Error ? err.message : 'Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Upload Document</h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-4">
            {/* File Drop Zone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                isDragOver
                  ? 'border-primary-500 bg-primary-50'
                  : selectedFile
                    ? 'border-success-500 bg-success-50'
                    : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleFileSelect(file)
                }}
              />

              {selectedFile ? (
                <div className="flex items-center justify-center space-x-3">
                  <FileText className="h-8 w-8 text-success-500" />
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="h-10 w-10 text-gray-400 mx-auto mb-3" />
                  <p className="text-sm text-gray-600">
                    <span className="text-primary-600 font-medium">Click to upload</span> or drag
                    and drop
                  </p>
                  <p className="text-xs text-gray-500 mt-1">PDF, JPEG, PNG, Word (max 50MB)</p>
                </>
              )}
            </div>

            {/* Document Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value as DocumentType)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {DOCUMENT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Reference Number */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reference Number (optional)
              </label>
              <input
                type="text"
                value={referenceNumber}
                onChange={(e) => setReferenceNumber(e.target.value)}
                placeholder="e.g., INV-2026-001"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Status Messages */}
            {uploadStatus === 'success' && (
              <div className="flex items-center space-x-2 text-success-600 bg-success-50 p-3 rounded-lg">
                <CheckCircle className="h-5 w-5" />
                <span>Document uploaded successfully!</span>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div className="flex items-center space-x-2 text-danger-600 bg-danger-50 p-3 rounded-lg">
                <AlertCircle className="h-5 w-5" />
                <span>{errorMessage}</span>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-4 border-t border-gray-200">
            <button onClick={handleClose} className="btn-secondary" disabled={isUploading}>
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={!selectedFile || isUploading || uploadStatus === 'success'}
              className="btn-primary"
            >
              {isUploading ? (
                <>
                  <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></span>
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Document
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
