/**
 * Invite Member Modal Component
 *
 * Sprint 13.2: Frontend Member Management UI
 *
 * Modal for inviting new members to an organization with:
 * - Email validation
 * - Role selection dropdown
 * - Optional custom message
 * - Loading state and error handling
 * - Toast notifications
 */

import { useState } from 'react'
import { X, Mail, UserPlus, Loader2, Send, AlertTriangle, Copy, Check } from 'lucide-react'
import api, { ApiClientError } from '../../api/client'
import type { OrgRole, InvitationCreateResponse } from '../../types'

interface InviteMemberModalProps {
  isOpen: boolean
  onClose: () => void
  organizationId: string
  organizationName: string
  onInviteSent: () => void
}

// Role options with descriptions
const ROLE_OPTIONS: Array<{ value: OrgRole; label: string; description: string }> = [
  { value: 'admin', label: 'Admin', description: 'Full access to manage organization' },
  { value: 'manager', label: 'Manager', description: 'Can manage shipments and documents' },
  { value: 'member', label: 'Member', description: 'Standard access to view and edit' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access' },
]

export default function InviteMemberModal({
  isOpen,
  onClose,
  organizationId,
  organizationName,
  onInviteSent,
}: InviteMemberModalProps) {
  const [email, setEmail] = useState('')
  const [orgRole, setOrgRole] = useState<OrgRole>('member')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<InvitationCreateResponse | null>(null)
  const [copied, setCopied] = useState(false)

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validate email
    if (!email.trim()) {
      setError('Email address is required')
      return
    }
    if (!validateEmail(email.trim())) {
      setError('Please enter a valid email address')
      return
    }

    setLoading(true)

    try {
      const response = await api.createInvitation(organizationId, {
        email: email.trim().toLowerCase(),
        org_role: orgRole,
        message: message.trim() || undefined,
      })

      setSuccess(response)
      onInviteSent()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to send invitation. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (!loading) {
      setEmail('')
      setOrgRole('member')
      setMessage('')
      setError(null)
      setSuccess(null)
      setCopied(false)
      onClose()
    }
  }

  const handleCopyLink = async () => {
    if (success?.invitation_url) {
      try {
        await navigator.clipboard.writeText(success.invitation_url)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      } catch {
        // Clipboard API might not be available
      }
    }
  }

  const handleSendAnother = () => {
    setEmail('')
    setOrgRole('member')
    setMessage('')
    setSuccess(null)
    setCopied(false)
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
            <div className="flex items-center space-x-2">
              <UserPlus className="h-5 w-5 text-primary-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Invite Member
              </h3>
            </div>
            <button
              onClick={handleClose}
              disabled={loading}
              className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              aria-label="Close modal"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6">
            {/* Success State */}
            {success ? (
              <div className="text-center">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                  <Send className="h-6 w-6 text-green-600" />
                </div>
                <h4 className="text-lg font-medium text-gray-900 mb-2">
                  Invitation Sent!
                </h4>
                <p className="text-gray-600 mb-4">
                  An invitation has been sent to{' '}
                  <span className="font-medium">{success.email}</span>
                </p>

                {/* Invitation Link */}
                <div className="bg-gray-50 rounded-lg p-3 mb-4">
                  <p className="text-sm text-gray-500 mb-2">
                    Or share this invitation link:
                  </p>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      readOnly
                      value={success.invitation_url}
                      className="flex-1 text-xs bg-white border border-gray-300 rounded px-2 py-1 font-mono truncate"
                    />
                    <button
                      onClick={handleCopyLink}
                      className="flex items-center space-x-1 px-2 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                    >
                      {copied ? (
                        <>
                          <Check className="h-4 w-4 text-green-600" />
                          <span className="text-green-600">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <p className="text-sm text-gray-500 mb-4">
                  The invitation expires on{' '}
                  {new Date(success.expires_at).toLocaleDateString()}
                </p>

                <div className="flex space-x-3">
                  <button
                    onClick={handleSendAnother}
                    className="flex-1 btn-secondary"
                  >
                    Send Another
                  </button>
                  <button
                    onClick={handleClose}
                    className="flex-1 btn-primary"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              /* Form State */
              <form onSubmit={handleSubmit}>
                <p className="text-gray-600 mb-4">
                  Invite someone to join <span className="font-medium">{organizationName}</span>
                </p>

                {/* Error message */}
                {error && (
                  <div className="flex items-start space-x-2 text-danger-600 bg-danger-50 p-3 rounded-lg mb-4">
                    <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{error}</span>
                  </div>
                )}

                {/* Email input */}
                <div className="mb-4">
                  <label
                    htmlFor="invite-email"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Email Address *
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      id="invite-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="colleague@example.com"
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      disabled={loading}
                      required
                    />
                  </div>
                </div>

                {/* Role select */}
                <div className="mb-4">
                  <label
                    htmlFor="invite-role"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Role *
                  </label>
                  <select
                    id="invite-role"
                    value={orgRole}
                    onChange={(e) => setOrgRole(e.target.value as OrgRole)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    disabled={loading}
                  >
                    {ROLE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    {ROLE_OPTIONS.find((r) => r.value === orgRole)?.description}
                  </p>
                </div>

                {/* Optional message */}
                <div className="mb-6">
                  <label
                    htmlFor="invite-message"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Personal Message (optional)
                  </label>
                  <textarea
                    id="invite-message"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Add a personal note to the invitation..."
                    rows={3}
                    maxLength={1000}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                    disabled={loading}
                  />
                  <p className="mt-1 text-xs text-gray-500 text-right">
                    {message.length}/1000
                  </p>
                </div>

                {/* Footer buttons */}
                <div className="flex items-center justify-end space-x-3">
                  <button
                    type="button"
                    onClick={handleClose}
                    disabled={loading}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !email.trim()}
                    className="btn-primary flex items-center"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4 mr-2" />
                        Send Invitation
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export { InviteMemberModal }
