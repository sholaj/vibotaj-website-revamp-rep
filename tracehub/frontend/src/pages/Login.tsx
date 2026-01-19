/**
 * Login Page Component
 *
 * Handles user authentication with:
 * - Form validation
 * - Error handling
 * - Loading states
 * - Secure credential handling
 */

import { useState, useCallback, useMemo } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Package, Eye, EyeOff, AlertCircle } from 'lucide-react'
import api, { ApiClientError, NetworkError, AuthenticationError } from '../api/client'

interface LoginProps {
  onLogin: (token: string) => void
}

interface LocationState {
  from?: { pathname: string }
}

export default function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Get the intended destination - check for returnUrl query param first (for invitation acceptance)
  // then fall back to location state from protected route redirect
  const from = useMemo(() => {
    const returnUrl = searchParams.get('returnUrl')
    if (returnUrl) {
      // Validate returnUrl is a relative path (security check)
      try {
        const url = new URL(returnUrl, window.location.origin)
        if (url.origin === window.location.origin) {
          return returnUrl
        }
      } catch {
        // Invalid URL, ignore
      }
    }
    return (location.state as LocationState)?.from?.pathname || '/dashboard'
  }, [searchParams, location.state])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Basic validation
    if (!username.trim()) {
      setError('Username is required')
      return
    }

    if (!password) {
      setError('Password is required')
      return
    }

    setIsLoading(true)

    try {
      const response = await api.login({ username: username.trim(), password })

      // Notify parent component of successful login
      onLogin(response.access_token)

      // Navigate to the originally intended destination
      navigate(from, { replace: true })
    } catch (err) {
      console.error('Login failed:', err)

      if (err instanceof AuthenticationError) {
        setError('Invalid username or password')
      } else if (err instanceof NetworkError) {
        setError('Unable to connect to the server. Please check your internet connection.')
      } else if (err instanceof ApiClientError) {
        setError(err.message || 'Login failed. Please try again.')
      } else {
        setError('An unexpected error occurred. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [username, password, onLogin, navigate, from])

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
          <p className="mt-2 text-sm text-gray-600">
            Container Tracking & Compliance Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="card p-8 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Invitation acceptance notice */}
            {from.startsWith('/accept-invitation/') && (
              <div className="bg-primary-50 border border-primary-200 text-primary-700 px-4 py-3 rounded-md text-sm">
                <p className="font-medium">Sign in to accept your invitation</p>
                <p className="text-primary-600 mt-1">You will be redirected after logging in.</p>
              </div>
            )}

            {/* Error Alert */}
            {error && (
              <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-md text-sm flex items-start">
                <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* Username Field */}
            <div>
              <label htmlFor="username" className="label">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input"
                placeholder="Enter your username"
                required
                autoComplete="username"
                disabled={isLoading}
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
                  placeholder="Enter your password"
                  required
                  autoComplete="current-password"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 transition-colors"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3 relative"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Signing in...
                </div>
              ) : (
                'Sign in'
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs text-gray-500">
          VIBOTAJ Global Nigeria Ltd
        </p>
      </div>
    </div>
  )
}
