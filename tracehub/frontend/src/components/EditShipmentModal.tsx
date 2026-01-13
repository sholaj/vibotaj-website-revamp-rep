/**
 * Edit Shipment Modal Component
 *
 * Modal dialog for editing existing shipments with:
 * - Pre-populated form fields from existing shipment
 * - Same validation as CreateShipmentModal
 * - Status updates
 * - Buyer organization selection
 */

import { useState, useEffect, useCallback } from 'react'
import { X, Ship, AlertCircle, Loader2, CheckCircle, Leaf } from 'lucide-react'
import api from '../api/client'
import type { Shipment, BuyerOrganization, ProductType, ShipmentStatus } from '../types'
import { PRODUCT_TYPE_OPTIONS } from '../types'

interface EditShipmentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (shipment: Shipment) => void
  shipment: Shipment | null
}

// Container number validation (ISO 6346): 4 letters + 7 digits
const CONTAINER_PATTERN = /^[A-Z]{4}[0-9]{7}$/

// Reference pattern: VIBO-YYYY-NNN
const REFERENCE_PATTERN = /^VIBO-\d{4}-\d{3}$/

// TICKET-001: Available shipment statuses (aligned with backend ShipmentStatus enum)
const STATUS_OPTIONS: { value: ShipmentStatus; label: string }[] = [
  { value: 'draft', label: 'Draft' },
  { value: 'docs_pending', label: 'Documents Pending' },
  { value: 'docs_complete', label: 'Documents Complete' },
  { value: 'in_transit', label: 'In Transit' },
  { value: 'arrived', label: 'Arrived' },
  { value: 'customs', label: 'At Customs' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'archived', label: 'Archived' },
]

export default function EditShipmentModal({
  isOpen,
  onClose,
  onSuccess,
  shipment,
}: EditShipmentModalProps) {
  // Form field state
  const [reference, setReference] = useState('')
  const [containerNumber, setContainerNumber] = useState('')
  const [productType, setProductType] = useState<ProductType | ''>('')
  const [vesselName, setVesselName] = useState('')
  const [status, setStatus] = useState<ShipmentStatus>('draft')
  const [buyerOrgId, setBuyerOrgId] = useState<string>('')

  // Buyers dropdown state
  const [buyers, setBuyers] = useState<BuyerOrganization[]>([])
  const [loadingBuyers, setLoadingBuyers] = useState(false)

  // Form submission state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  // Field validation errors
  const [referenceError, setReferenceError] = useState<string | null>(null)
  const [containerError, setContainerError] = useState<string | null>(null)

  // Populate form with shipment data when modal opens
  useEffect(() => {
    if (isOpen && shipment) {
      setReference(shipment.reference || '')
      setContainerNumber(shipment.container_number || '')
      setProductType(shipment.product_type || '')
      setVesselName(shipment.vessel_name || '')
      setStatus(shipment.status || 'draft')
      setBuyerOrgId(shipment.buyer_organization_id || '')
      setSubmitStatus('idle')
      setError(null)
      setReferenceError(null)
      setContainerError(null)
      loadBuyerOrganizations()
    }
  }, [isOpen, shipment])

  // Handle modal close
  const handleClose = useCallback(() => {
    onClose()
  }, [onClose])

  // Load buyer organizations from API
  const loadBuyerOrganizations = async () => {
    setLoadingBuyers(true)
    try {
      const buyerOrgs = await api.getBuyerOrganizations()
      setBuyers(buyerOrgs)
    } catch (err) {
      console.error('Failed to load buyer organizations:', err)
    } finally {
      setLoadingBuyers(false)
    }
  }

  // Validate container number (ISO 6346 format)
  const validateContainer = (value: string): boolean => {
    if (!value) {
      setContainerError('Container number is required')
      return false
    }
    const normalizedValue = value.toUpperCase().replace(/\s/g, '')
    if (!CONTAINER_PATTERN.test(normalizedValue)) {
      setContainerError('Invalid format. Expected: 4 letters + 7 digits (e.g., MSCU1234567)')
      return false
    }
    setContainerError(null)
    return true
  }

  // Validate reference number
  const validateReference = (value: string): boolean => {
    if (!value) {
      setReferenceError('Reference is required')
      return false
    }
    if (!REFERENCE_PATTERN.test(value)) {
      setReferenceError('Invalid format. Expected: VIBO-YYYY-NNN (e.g., VIBO-2026-001)')
      return false
    }
    setReferenceError(null)
    return true
  }

  // Handle container number input change
  const handleContainerChange = (value: string) => {
    const normalizedValue = value.toUpperCase().replace(/\s/g, '')
    setContainerNumber(normalizedValue)
    if (containerError && CONTAINER_PATTERN.test(normalizedValue)) {
      setContainerError(null)
    }
  }

  // Handle reference input change
  const handleReferenceChange = (value: string) => {
    setReference(value.toUpperCase())
    if (referenceError && REFERENCE_PATTERN.test(value.toUpperCase())) {
      setReferenceError(null)
    }
  }

  // Form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!shipment) return

    // Validate fields
    const isReferenceValid = validateReference(reference)
    const isContainerValid = validateContainer(containerNumber)

    if (!isReferenceValid || !isContainerValid) {
      return
    }

    setIsSubmitting(true)
    setSubmitStatus('idle')
    setError(null)

    try {
      const updateData: Partial<Shipment> = {
        reference,
        container_number: containerNumber,
        product_type: productType || undefined,
        vessel_name: vesselName || undefined,
        status,
        buyer_organization_id: buyerOrgId || undefined,
      }

      const updatedShipment = await api.updateShipment(shipment.id, updateData)

      setSubmitStatus('success')

      // Wait a moment to show success, then close
      setTimeout(() => {
        handleClose()
        onSuccess(updatedShipment)
      }, 1000)
    } catch (err) {
      console.error('Failed to update shipment:', err)
      setSubmitStatus('error')
      setError(err instanceof Error ? err.message : 'Failed to update shipment. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen || !shipment) return null

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
            <div className="flex items-center space-x-2">
              <Ship className="h-5 w-5 text-primary-600" />
              <h3 className="text-lg font-semibold text-gray-900">Edit Shipment</h3>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close modal"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Body */}
          <form onSubmit={handleSubmit}>
            <div className="p-6 space-y-4">
              {/* Reference Number */}
              <div>
                <label htmlFor="reference" className="block text-sm font-medium text-gray-700 mb-1">
                  Reference Number <span className="text-danger-500">*</span>
                </label>
                <input
                  id="reference"
                  type="text"
                  value={reference}
                  onChange={(e) => handleReferenceChange(e.target.value)}
                  onBlur={() => reference && validateReference(reference)}
                  placeholder="VIBO-2026-001"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    referenceError ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                  }`}
                  disabled={isSubmitting}
                />
                {referenceError && (
                  <p className="mt-1 text-sm text-danger-600 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    {referenceError}
                  </p>
                )}
              </div>

              {/* Container Number */}
              <div>
                <label htmlFor="containerNumber" className="block text-sm font-medium text-gray-700 mb-1">
                  Container Number <span className="text-danger-500">*</span>
                </label>
                <input
                  id="containerNumber"
                  type="text"
                  value={containerNumber}
                  onChange={(e) => handleContainerChange(e.target.value)}
                  onBlur={() => containerNumber && validateContainer(containerNumber)}
                  placeholder="MSCU1234567"
                  maxLength={11}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    containerError ? 'border-danger-500 bg-danger-50' : 'border-gray-300'
                  }`}
                  disabled={isSubmitting}
                />
                {containerError && (
                  <p className="mt-1 text-sm text-danger-600 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-1" />
                    {containerError}
                  </p>
                )}
              </div>

              {/* Status */}
              <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  id="status"
                  value={status}
                  onChange={(e) => setStatus(e.target.value as ShipmentStatus)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={isSubmitting}
                >
                  {STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Product Type */}
              <div>
                <label htmlFor="productType" className="block text-sm font-medium text-gray-700 mb-1">
                  Product Type
                </label>
                <select
                  id="productType"
                  value={productType}
                  onChange={(e) => setProductType(e.target.value as ProductType | '')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={isSubmitting}
                >
                  <option value="">Select product type</option>
                  {PRODUCT_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label} (HS {option.hsCode})
                    </option>
                  ))}
                </select>
                {productType && (
                  <p className="mt-1 text-xs flex items-center">
                    {PRODUCT_TYPE_OPTIONS.find(o => o.value === productType)?.eudrRequired ? (
                      <span className="text-warning-600 flex items-center">
                        <Leaf className="h-3 w-3 mr-1" />
                        EUDR compliance required
                      </span>
                    ) : (
                      <span className="text-gray-500">No EUDR requirements</span>
                    )}
                  </p>
                )}
              </div>

              {/* Vessel Name */}
              <div>
                <label htmlFor="vesselName" className="block text-sm font-medium text-gray-700 mb-1">
                  Vessel Name
                </label>
                <input
                  id="vesselName"
                  type="text"
                  value={vesselName}
                  onChange={(e) => setVesselName(e.target.value)}
                  placeholder="MSC AURORA"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={isSubmitting}
                />
              </div>

              {/* Buyer Organization */}
              <div>
                <label htmlFor="buyerOrg" className="block text-sm font-medium text-gray-700 mb-1">
                  Buyer Organization
                </label>
                <select
                  id="buyerOrg"
                  value={buyerOrgId}
                  onChange={(e) => setBuyerOrgId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={isSubmitting || loadingBuyers}
                >
                  <option value="">Select buyer (optional)</option>
                  {buyers.map((buyer) => (
                    <option key={buyer.id} value={buyer.id}>
                      {buyer.name}
                    </option>
                  ))}
                </select>
                {loadingBuyers && (
                  <p className="mt-1 text-xs text-gray-500 flex items-center">
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    Loading buyers...
                  </p>
                )}
              </div>

              {/* Status Messages */}
              {submitStatus === 'success' && (
                <div className="flex items-center space-x-2 text-success-600 bg-success-50 p-3 rounded-lg">
                  <CheckCircle className="h-5 w-5" />
                  <span>Shipment updated successfully!</span>
                </div>
              )}

              {submitStatus === 'error' && error && (
                <div className="flex items-center space-x-2 text-danger-600 bg-danger-50 p-3 rounded-lg">
                  <AlertCircle className="h-5 w-5" />
                  <span>{error}</span>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end space-x-3 p-4 border-t border-gray-200">
              <button
                type="button"
                onClick={handleClose}
                className="btn-secondary"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || submitStatus === 'success'}
                className="btn-primary"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Changes'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export { EditShipmentModal }
