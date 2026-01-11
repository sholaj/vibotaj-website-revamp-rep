/**
 * Accept Invitation Page
 *
 * Sprint 13.3: Invitation Acceptance Workflow
 *
 * Handles the complete invitation acceptance flow:
 * - Loading invitation details
 * - New user registration (create account)
 * - Existing user login redirect
 * - Auto-acceptance for logged-in matching users
 * - Email mismatch handling
 */

import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Package,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
  XCircle,
  Building2,
  Mail,
  User,
  Shield,
  LogIn,
  LogOut,
} from 'lucide-react'
import api from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import type { InvitationAcceptInfo, AcceptedInvitationResponse, OrgRole } from '../types'

// Role display configuration
const ROLE_LABELS: Record<OrgRole, string> = {
  admin: 'Administrator',
  manager: 'Manager',
  member: 'Member',
  viewer: 'Viewer',
}

const ROLE_DESCRIPTIONS: Record<OrgRole, string> = {
  admin: 'Full access to manage organization settings, members, and all data',
  manager: 'Can manage shipments, documents, and invite members',
  member: 'Can view and manage shipments and documents',
  viewer: 'Read-only access to shipments and documents',
}

// Password strength indicator
function PasswordStrength({ password }: { password: string }) {
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
  }

  const passedCount = Object.values(checks).filter(Boolean).length
  const strengthColors = ['bg-danger-500', 'bg-warning-500', 'bg-warning-400', 'bg-success-500']
  const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong']

  if (password.length === 0) return null

  return (
    <div className="mt-2">
      <div className="flex gap-1 mb-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded ${
              i < passedCount ? strengthColors[passedCount - 1] : 'bg-gray-200'
            }`}
          />
        ))}
      </div>
      <p className="text-xs text-gray-500">
        Password strength: {strengthLabels[passedCount - 1] || 'Very weak'}
      </p>
      <ul className="text-xs text-gray-500 mt-1 space-y-0.5">
        <li className={checks.length ? 'text-success-600' : ''}>
          {checks.length ? '✓' : '○'} At least 8 characters
        </li>
        <li className={checks.uppercase ? 'text-success-600' : ''}>
          {checks.uppercase ? '✓' : '○'} One uppercase letter
        </li>
        <li className={checks.lowercase ? 'text-success-600' : ''}>
          {checks.lowercase ? '✓' : '○'} One lowercase letter
        </li>
        <li className={checks.number ? 'text-success-600' : ''}>
          {checks.number ? '✓' : '○'} One number
        </li>
      </ul>
    </div>
  )
}

// Loading state component
function LoadingState() {
  return (
    <div className="text-center py-12">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
      <p className="mt-4 text-gray-600">Loading invitation details...</p>
    </div>
  )
}

// Error state component
function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center py-12">
      <div className="mx-auto w-16 h-16 bg-danger-100 rounded-full flex items-center justify-center mb-4">
        <XCircle className="w-8 h-8 text-danger-600" />
      </div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Invitation Error</h2>
      <p className="text-gray-600 mb-6">{message}</p>
      <Link to="/login" className="btn-primary inline-flex items-center">
        <LogIn className="w-4 h-4 mr-2" />
        Go to Login
      </Link>
    </div>
  )
}

// Success state component
function SuccessState({
  organizationName,
  onContinue,
}: {
  organizationName: string
  onContinue: () => void
}) {
  return (
    <div className="text-center py-12">
      <div className="mx-auto w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mb-4">
        <CheckCircle className="w-8 h-8 text-success-600" />
      </div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Welcome to {organizationName}!</h2>
      <p className="text-gray-600 mb-6">
        You have successfully joined the organization. You can now access shared shipments and
        documents.
      </p>
      <button onClick={onContinue} className="btn-primary inline-flex items-center">
        Go to Dashboard
      </button>
    </div>
  )
}

// Email mismatch state component
function EmailMismatchState({
  invitedEmail,
  loggedInEmail,
  onLogout,
  onCancel,
}: {
  invitedEmail: string
  loggedInEmail: string
  onLogout: () => void
  onCancel: () => void
}) {
  return (
    <div className="text-center py-8">
      <div className="mx-auto w-16 h-16 bg-warning-100 rounded-full flex items-center justify-center mb-4">
        <AlertCircle className="w-8 h-8 text-warning-600" />
      </div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Email Mismatch</h2>
      <p className="text-gray-600 mb-4">
        This invitation is for <span className="font-medium">{invitedEmail}</span>, but you are
        currently logged in as <span className="font-medium">{loggedInEmail}</span>.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center mt-6">
        <button onClick={onLogout} className="btn-primary inline-flex items-center justify-center">
          <LogOut className="w-4 h-4 mr-2" />
          Log out and Accept
        </button>
        <button onClick={onCancel} className="btn-secondary inline-flex items-center justify-center">
          Cancel
        </button>
      </div>
    </div>
  )
}

// Main AcceptInvitation component
export default function AcceptInvitation() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated, isLoading: authLoading, login, logout } = useAuth()

  // State
  const [invitation, setInvitation] = useState<InvitationAcceptInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [acceptSuccess, setAcceptSuccess] = useState<AcceptedInvitationResponse | null>(null)

  // Form state for new users
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [formError, setFormError] = useState('')

  // Fetch invitation details
  const fetchInvitation = useCallback(async () => {
    if (!token) {
      setError('Invalid invitation link')
      setIsLoading(false)
      return
    }

    try {
      const data = await api.getInvitationByToken(token)
      setInvitation(data)
      setError(null)
    } catch (err: unknown) {
      console.error('Failed to fetch invitation:', err)
      // Extract error message from response
      const axiosError = err as { response?: { data?: { detail?: string } } }
      const message =
        axiosError.response?.data?.detail || 'This invitation is invalid or has expired'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [token])

  // Load invitation on mount
  useEffect(() => {
    fetchInvitation()
  }, [fetchInvitation])

  // Auto-accept for logged-in users with matching email
  useEffect(() => {
    if (
      !authLoading &&
      isAuthenticated &&
      user &&
      invitation &&
      user.email.toLowerCase() === invitation.email.toLowerCase()
    ) {
      handleAcceptExistingUser()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, isAuthenticated, user, invitation])

  // Handle accepting as existing user
  const handleAcceptExistingUser = async () => {
    if (!token) return

    setIsSubmitting(true)
    setFormError('')

    try {
      const response = await api.acceptInvitation(token)
      setAcceptSuccess(response)
    } catch (err: unknown) {
      console.error('Failed to accept invitation:', err)
      const axiosError = err as { response?: { data?: { detail?: string } } }
      const message = axiosError.response?.data?.detail || 'Failed to accept invitation'
      setFormError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handle form submission for new users
  const handleSubmitNewUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')

    // Validation
    if (!fullName.trim()) {
      setFormError('Full name is required')
      return
    }

    if (fullName.trim().length < 2) {
      setFormError('Full name must be at least 2 characters')
      return
    }

    if (!password) {
      setFormError('Password is required')
      return
    }

    if (password.length < 8) {
      setFormError('Password must be at least 8 characters')
      return
    }

    if (!/[A-Z]/.test(password)) {
      setFormError('Password must contain at least one uppercase letter')
      return
    }

    if (!/[a-z]/.test(password)) {
      setFormError('Password must contain at least one lowercase letter')
      return
    }

    if (!/\d/.test(password)) {
      setFormError('Password must contain at least one number')
      return
    }

    if (password !== confirmPassword) {
      setFormError('Passwords do not match')
      return
    }

    if (!token) return

    setIsSubmitting(true)

    try {
      const response = await api.acceptInvitation(token, {
        full_name: fullName.trim(),
        password,
      })

      setAcceptSuccess(response)

      // If we got an access token, trigger login
      if (response.access_token) {
        await login(response.access_token)
      }
    } catch (err: unknown) {
      console.error('Failed to accept invitation:', err)
      const axiosError = err as { response?: { data?: { detail?: string } } }
      const message = axiosError.response?.data?.detail || 'Failed to create account'
      setFormError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handle logout and redirect back
  const handleLogoutAndAccept = () => {
    logout()
    // Page will re-render with login prompt
  }

  // Handle cancel (go to dashboard)
  const handleCancel = () => {
    navigate('/dashboard')
  }

  // Handle redirect to login with return URL
  const handleLoginRedirect = () => {
    const returnUrl = `/accept-invitation/${token}`
    navigate(`/login?returnUrl=${encodeURIComponent(returnUrl)}`)
  }

  // Handle continue to dashboard
  const handleContinueToDashboard = () => {
    navigate('/dashboard')
  }

  // Show loading while auth is being checked
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 py-12 px-4">
        <div className="max-w-md w-full">
          <div className="card p-8 shadow-xl">
            <LoadingState />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="flex justify-center">
            <div className="bg-primary-600 p-3 rounded-xl shadow-lg">
              <Package className="h-10 w-10 text-white" />
            </div>
          </div>
          <h1 className="mt-4 text-3xl font-bold text-gray-900">TraceHub</h1>
          <p className="mt-2 text-sm text-gray-600">Container Tracking & Compliance Platform</p>
        </div>

        {/* Main Card */}
        <div className="card p-8 shadow-xl">
          {/* Loading State */}
          {isLoading && <LoadingState />}

          {/* Error State */}
          {!isLoading && error && <ErrorState message={error} />}

          {/* Success State */}
          {!isLoading && !error && acceptSuccess && (
            <SuccessState
              organizationName={acceptSuccess.organization_name}
              onContinue={handleContinueToDashboard}
            />
          )}

          {/* Email Mismatch State */}
          {!isLoading &&
            !error &&
            !acceptSuccess &&
            invitation &&
            isAuthenticated &&
            user &&
            user.email.toLowerCase() !== invitation.email.toLowerCase() && (
              <EmailMismatchState
                invitedEmail={invitation.email}
                loggedInEmail={user.email}
                onLogout={handleLogoutAndAccept}
                onCancel={handleCancel}
              />
            )}

          {/* Invitation Details and Actions (when not logged in or new user) */}
          {!isLoading && !error && !acceptSuccess && invitation && !isAuthenticated && (
            <>
              {/* Invitation Header */}
              <div className="text-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">You have been invited!</h2>
                {invitation.invited_by_name && (
                  <p className="text-sm text-gray-600 mt-1">
                    {invitation.invited_by_name} has invited you to join
                  </p>
                )}
              </div>

              {/* Organization Info */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="flex items-center mb-3">
                  <Building2 className="w-5 h-5 text-primary-600 mr-2" />
                  <span className="font-medium text-gray-900">{invitation.organization_name}</span>
                </div>
                <div className="flex items-center mb-3">
                  <Mail className="w-5 h-5 text-gray-400 mr-2" />
                  <span className="text-gray-600">{invitation.email}</span>
                </div>
                <div className="flex items-start">
                  <Shield className="w-5 h-5 text-gray-400 mr-2 mt-0.5" />
                  <div>
                    <span className="text-gray-900 font-medium">
                      {ROLE_LABELS[invitation.org_role]}
                    </span>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {ROLE_DESCRIPTIONS[invitation.org_role]}
                    </p>
                  </div>
                </div>
              </div>

              {/* Custom Message */}
              {invitation.custom_message && (
                <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-primary-800 italic">"{invitation.custom_message}"</p>
                </div>
              )}

              {/* Existing User - Login Required */}
              {!invitation.requires_registration && (
                <div className="text-center">
                  <div className="mb-4">
                    <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-sm">
                      <User className="w-4 h-4 mr-1" />
                      Account exists
                    </div>
                  </div>
                  <p className="text-gray-600 mb-6">
                    An account already exists for this email. Please log in to accept the
                    invitation.
                  </p>
                  <button
                    onClick={handleLoginRedirect}
                    className="btn-primary w-full inline-flex items-center justify-center"
                  >
                    <LogIn className="w-4 h-4 mr-2" />
                    Log in to Accept
                  </button>
                </div>
              )}

              {/* New User - Registration Form */}
              {invitation.requires_registration && (
                <form onSubmit={handleSubmitNewUser} className="space-y-4">
                  <div className="mb-4">
                    <div className="inline-flex items-center px-3 py-1 rounded-full bg-success-50 text-success-700 text-sm">
                      <User className="w-4 h-4 mr-1" />
                      Create your account
                    </div>
                  </div>

                  {/* Error Alert */}
                  {formError && (
                    <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-md text-sm flex items-start">
                      <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
                      <span>{formError}</span>
                    </div>
                  )}

                  {/* Full Name Field */}
                  <div>
                    <label htmlFor="fullName" className="label">
                      Full Name
                    </label>
                    <input
                      id="fullName"
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="input"
                      placeholder="Enter your full name"
                      required
                      disabled={isSubmitting}
                      autoFocus
                    />
                  </div>

                  {/* Password Field */}
                  <div>
                    <label htmlFor="password" className="label">
                      Password
                    </label>
                    <div className="relative">
                      <input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="input pr-10"
                        placeholder="Create a password"
                        required
                        autoComplete="new-password"
                        disabled={isSubmitting}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 transition-colors"
                        tabIndex={-1}
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <PasswordStrength password={password} />
                  </div>

                  {/* Confirm Password Field */}
                  <div>
                    <label htmlFor="confirmPassword" className="label">
                      Confirm Password
                    </label>
                    <input
                      id="confirmPassword"
                      type={showPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="input"
                      placeholder="Confirm your password"
                      required
                      autoComplete="new-password"
                      disabled={isSubmitting}
                    />
                    {confirmPassword && password !== confirmPassword && (
                      <p className="text-sm text-danger-600 mt-1">Passwords do not match</p>
                    )}
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="btn-primary w-full py-3 relative mt-6"
                  >
                    {isSubmitting ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Creating account...
                      </div>
                    ) : (
                      'Accept & Create Account'
                    )}
                  </button>
                </form>
              )}
            </>
          )}

          {/* Auto-accepting for logged-in matching user */}
          {!isLoading &&
            !error &&
            !acceptSuccess &&
            invitation &&
            isAuthenticated &&
            user &&
            user.email.toLowerCase() === invitation.email.toLowerCase() &&
            isSubmitting && (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Accepting invitation...</p>
              </div>
            )}
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs text-gray-500">VIBOTAJ Global Nigeria Ltd</p>
      </div>
    </div>
  )
}
