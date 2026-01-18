/**
 * Organization Delete Modal Component
 *
 * Modal for deleting organizations with:
 * - Organization details display (name, slug, type, member count)
 * - Type confirmation input (type slug to confirm)
 * - Reason text area (required, min 10 chars)
 * - Warning messages about member impact
 * - Cannot delete VIBOTAJ organizations
 */

import { useState, useEffect } from 'react'
import {
  Trash2,
  AlertTriangle,
  AlertCircle,
  Loader2,
  Building2,
  Users,
  Info,
} from 'lucide-react'
import api, { ApiClientError } from '../../api/client'
import type { OrganizationListItem, OrganizationDeleteResponse, OrganizationType } from '../../types'

interface OrganizationDeleteModalProps {
  isOpen: boolean
  onClose: () => void
  organization: OrganizationListItem | null
  onDeleted: (response: OrganizationDeleteResponse) => void
}

const typeLabels: Record<OrganizationType, string> = {
  vibotaj: 'VIBOTAJ',
  buyer: 'Buyer',
  supplier: 'Supplier',
  logistics_agent: 'Logistics Agent',
}

const typeBadgeStyles: Record<OrganizationType, string> = {
  vibotaj: 'bg-purple-100 text-purple-800',
  buyer: 'bg-green-100 text-green-800',
  supplier: 'bg-orange-100 text-orange-800',
  logistics_agent: 'bg-teal-100 text-teal-800',
}

export default function OrganizationDeleteModal({
  isOpen,
  onClose,
  organization,
  onDeleted,
}: OrganizationDeleteModalProps) {
  // Form state
  const [confirmSlug, setConfirmSlug] = useState('')
  const [reason, setReason] = useState('')

  // UI state
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setConfirmSlug('')
      setReason('')
      setError(null)
    }
  }, [isOpen])

  if (!isOpen || !organization) return null

  const isVibotaj = organization.type === 'vibotaj'
  const isSlugConfirmed = confirmSlug.toLowerCase() === organization.slug.toLowerCase()
  const isReasonValid = reason.trim().length >= 10
  const canSubmit = isSlugConfirmed && isReasonValid && !isVibotaj

  const handleSubmit = async () => {
    if (!canSubmit) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await api.deleteOrganization(organization.id, reason)
      onDeleted(response)
      onClose()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to delete organization. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
          {/* Header */}
          <div className="flex items-center space-x-3 p-6 border-b border-gray-200">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-danger-100 flex items-center justify-center">
              <Trash2 className="h-5 w-5 text-danger-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Delete Organization</h3>
              <p className="text-sm text-gray-500">This will suspend the organization</p>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Error Alert */}
            {error && (
              <div className="flex items-start space-x-2 text-danger-600 bg-danger-50 p-3 rounded-lg">
                <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            {/* VIBOTAJ Warning */}
            {isVibotaj && (
              <div className="flex items-start space-x-2 text-amber-600 bg-amber-50 p-3 rounded-lg">
                <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">Cannot delete VIBOTAJ organization</p>
                  <p className="text-amber-700">
                    The VIBOTAJ organization is the system owner and cannot be deleted.
                  </p>
                </div>
              </div>
            )}

            {/* Organization Info Card */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Building2 className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{organization.name}</p>
                    <p className="text-xs text-gray-500 font-mono">{organization.slug}</p>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Type</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${typeBadgeStyles[organization.type]}`}>
                    {typeLabels[organization.type]}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Members</span>
                  <span className="flex items-center text-sm font-medium text-gray-900">
                    <Users className="h-4 w-4 mr-1 text-gray-400" />
                    {organization.member_count}
                  </span>
                </div>
              </div>
            </div>

            {/* Member Impact Warning */}
            {organization.member_count > 0 && !isVibotaj && (
              <div className="flex items-start space-x-2 text-amber-600 bg-amber-50 p-3 rounded-lg">
                <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">
                    {organization.member_count} member{organization.member_count !== 1 ? 's' : ''} will be affected
                  </p>
                  <p className="text-amber-700">
                    All memberships will be suspended. Members will lose access to this organization.
                  </p>
                </div>
              </div>
            )}

            {/* Reason Input */}
            <div>
              <label htmlFor="delete-reason" className="block text-sm font-medium text-gray-700 mb-1">
                Reason for deletion <span className="text-danger-500">*</span>
              </label>
              <textarea
                id="delete-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Enter the reason for deleting this organization (min 10 characters)"
                rows={3}
                disabled={isVibotaj}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:text-gray-500"
              />
              <div className="flex justify-between mt-1">
                <span className="text-xs text-gray-500">
                  {reason.length < 10 ? `${10 - reason.length} more characters needed` : 'Valid reason'}
                </span>
                <span className="text-xs text-gray-500">{reason.length}/500</span>
              </div>
            </div>

            {/* Confirm Slug Input */}
            <div>
              <label htmlFor="confirm-slug" className="block text-sm font-medium text-gray-700 mb-1">
                Type <span className="font-mono text-danger-600">{organization.slug}</span> to confirm
              </label>
              <input
                id="confirm-slug"
                type="text"
                value={confirmSlug}
                onChange={(e) => setConfirmSlug(e.target.value)}
                placeholder="Type the organization slug"
                disabled={isVibotaj}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:text-gray-500 font-mono"
              />
              {confirmSlug && !isSlugConfirmed && (
                <p className="text-xs text-danger-500 mt-1">Slug does not match</p>
              )}
            </div>

            {/* Soft Delete Info */}
            {!isVibotaj && (
              <div className="flex items-start space-x-2 text-blue-600 bg-blue-50 p-3 rounded-lg">
                <Info className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <p className="text-sm">
                  This will set the organization status to "suspended" and deactivate all memberships.
                  The organization data is preserved for audit purposes.
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50 rounded-b-lg">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!canSubmit || isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-danger-600 border border-transparent rounded-lg hover:bg-danger-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-danger-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Organization
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
