/**
 * User Delete Modal Component
 *
 * Modal for deleting users with:
 * - User details display (name, email, role)
 * - Type confirmation input (type email to confirm)
 * - Reason text area (required, min 10 chars)
 * - Soft/Hard delete toggle (advanced, collapsed by default)
 * - Warning messages based on deletion type
 * - Disabled if last admin
 */

import { useState, useEffect } from 'react'
import {
  Trash2,
  AlertTriangle,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Info,
} from 'lucide-react'
import api, { ApiClientError } from '../../api/client'
import type { OrganizationMember, UserDeleteResponse } from '../../types'

interface UserDeleteModalProps {
  isOpen: boolean
  onClose: () => void
  member: OrganizationMember | null
  organizationId: string
  isLastAdmin?: boolean
  onDeleted: (response: UserDeleteResponse) => void
}

const roleLabels: Record<string, string> = {
  admin: 'Admin',
  manager: 'Manager',
  member: 'Member',
  viewer: 'Viewer',
}

export default function UserDeleteModal({
  isOpen,
  onClose,
  member,
  organizationId: _organizationId,
  isLastAdmin = false,
  onDeleted,
}: UserDeleteModalProps) {
  // Note: _organizationId available for future organization-specific logic
  // Form state
  const [confirmEmail, setConfirmEmail] = useState('')
  const [reason, setReason] = useState('')
  const [hardDelete, setHardDelete] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // UI state
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setConfirmEmail('')
      setReason('')
      setHardDelete(false)
      setShowAdvanced(false)
      setError(null)
    }
  }, [isOpen])

  if (!isOpen || !member) return null

  const isEmailConfirmed = confirmEmail.toLowerCase() === member.email.toLowerCase()
  const isReasonValid = reason.trim().length >= 10
  const canSubmit = isEmailConfirmed && isReasonValid && !isLastAdmin

  const handleSubmit = async () => {
    if (!canSubmit) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await api.deleteUser(member.user_id, reason, hardDelete)
      onDeleted(response)
      onClose()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to delete user. Please try again.')
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
              <h3 className="text-lg font-semibold text-gray-900">Delete User</h3>
              <p className="text-sm text-gray-500">This action cannot be undone</p>
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

            {/* Last Admin Warning */}
            {isLastAdmin && (
              <div className="flex items-start space-x-2 text-amber-600 bg-amber-50 p-3 rounded-lg">
                <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">Cannot delete last admin</p>
                  <p className="text-amber-700">
                    This user is the last admin in the organization. Assign another admin before deleting.
                  </p>
                </div>
              </div>
            )}

            {/* User Info Card */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-2">
                <div className="flex justify-between items-start">
                  <span className="text-sm text-gray-500">Name</span>
                  <span className="text-sm font-medium text-gray-900">{member.full_name}</span>
                </div>
                <div className="flex justify-between items-start">
                  <span className="text-sm text-gray-500">Email</span>
                  <span className="text-sm font-medium text-gray-900">{member.email}</span>
                </div>
                <div className="flex justify-between items-start">
                  <span className="text-sm text-gray-500">Role</span>
                  <span className="text-sm font-medium text-gray-900">
                    {roleLabels[member.org_role] || member.org_role}
                  </span>
                </div>
              </div>
            </div>

            {/* Reason Input */}
            <div>
              <label htmlFor="delete-reason" className="block text-sm font-medium text-gray-700 mb-1">
                Reason for deletion <span className="text-danger-500">*</span>
              </label>
              <textarea
                id="delete-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Enter the reason for deleting this user (min 10 characters)"
                rows={3}
                disabled={isLastAdmin}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:text-gray-500"
              />
              <div className="flex justify-between mt-1">
                <span className="text-xs text-gray-500">
                  {reason.length < 10 ? `${10 - reason.length} more characters needed` : 'Valid reason'}
                </span>
                <span className="text-xs text-gray-500">{reason.length}/500</span>
              </div>
            </div>

            {/* Confirm Email Input */}
            <div>
              <label htmlFor="confirm-email" className="block text-sm font-medium text-gray-700 mb-1">
                Type <span className="font-mono text-danger-600">{member.email}</span> to confirm
              </label>
              <input
                id="confirm-email"
                type="email"
                value={confirmEmail}
                onChange={(e) => setConfirmEmail(e.target.value)}
                placeholder="Type the email address"
                disabled={isLastAdmin}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:text-gray-500"
              />
              {confirmEmail && !isEmailConfirmed && (
                <p className="text-xs text-danger-500 mt-1">Email does not match</p>
              )}
            </div>

            {/* Advanced Options (Collapsible) */}
            <div className="border border-gray-200 rounded-lg">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                disabled={isLastAdmin}
                className="w-full flex items-center justify-between p-3 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                <span>Advanced Options</span>
                {showAdvanced ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>

              {showAdvanced && (
                <div className="p-3 pt-0 border-t border-gray-200">
                  {/* Hard Delete Toggle */}
                  <label className="flex items-start space-x-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={hardDelete}
                      onChange={(e) => setHardDelete(e.target.checked)}
                      disabled={isLastAdmin}
                      className="mt-1 h-4 w-4 text-danger-600 focus:ring-danger-500 border-gray-300 rounded"
                    />
                    <div>
                      <span className="text-sm font-medium text-gray-900">Permanent deletion</span>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Permanently remove user record and anonymize all audit log references.
                        This cannot be undone.
                      </p>
                    </div>
                  </label>

                  {hardDelete && (
                    <div className="mt-3 flex items-start space-x-2 text-amber-600 bg-amber-50 p-2 rounded">
                      <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                      <p className="text-xs">
                        This will permanently delete all user data. Use only for GDPR erasure requests.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Soft Delete Info */}
            {!hardDelete && (
              <div className="flex items-start space-x-2 text-blue-600 bg-blue-50 p-3 rounded-lg">
                <Info className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <p className="text-sm">
                  Soft delete will deactivate the user and preserve the record for audit purposes.
                  The user can be restored later if needed.
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
                  {hardDelete ? 'Permanently Delete' : 'Delete User'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
