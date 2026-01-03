/**
 * TraceHub Application Root Component
 *
 * Implements:
 * - Protected route handling
 * - Token validation on app load
 * - Proper authentication state management
 */

import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import Login from './pages/Login'
import Shipment from './pages/Shipment'
import Dashboard from './pages/Dashboard'
import Layout from './components/Layout'
import api from './api/client'

// Loading spinner component for consistent UI
function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading TraceHub...</p>
      </div>
    </div>
  )
}

// Error display component
function AuthError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
        <div className="text-danger-500 mb-4">
          <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Error</h2>
        <p className="text-gray-600 mb-6">{message}</p>
        <button
          onClick={onRetry}
          className="btn-primary w-full"
        >
          Try Again
        </button>
      </div>
    </div>
  )
}

// Protected route wrapper
function ProtectedRoute({ children, isAuthenticated }: { children: React.ReactNode; isAuthenticated: boolean }) {
  const location = useLocation()

  if (!isAuthenticated) {
    // Redirect to login, preserving the intended destination
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Verify token on app load
  const verifyAuthentication = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Check if we have a stored token that hasn't expired
      if (api.isAuthenticated()) {
        // Verify token is still valid with backend
        const isValid = await api.verifyToken()
        setIsAuthenticated(isValid)

        if (!isValid) {
          // Token was invalid, clear it
          api.logout()
        }
      } else {
        setIsAuthenticated(false)
      }
    } catch (err) {
      console.error('Authentication verification failed:', err)
      setIsAuthenticated(false)
      // Only show error if we thought we were authenticated
      if (api.isAuthenticated()) {
        setError('Session expired. Please log in again.')
        api.logout()
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    verifyAuthentication()
  }, [verifyAuthentication])

  // Handle successful login
  const handleLogin = useCallback((token: string) => {
    // Token is already stored by api.login(), just update state
    setIsAuthenticated(true)
    setError(null)
  }, [])

  // Handle logout
  const handleLogout = useCallback(() => {
    api.logout()
    setIsAuthenticated(false)
  }, [])

  // Handle retry after error
  const handleRetry = useCallback(() => {
    setError(null)
    verifyAuthentication()
  }, [verifyAuthentication])

  // Show loading state while checking authentication
  if (isLoading) {
    return <LoadingSpinner />
  }

  // Show error state if authentication check failed
  if (error) {
    return <AuthError message={error} onRetry={handleRetry} />
  }

  return (
    <Routes>
      {/* Login route - redirect to dashboard if already authenticated */}
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Login onLogin={handleLogin} />
          )
        }
      />

      {/* Protected routes wrapped in Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute isAuthenticated={isAuthenticated}>
            <Layout onLogout={handleLogout} />
          </ProtectedRoute>
        }
      >
        {/* Default redirect to dashboard */}
        <Route index element={<Navigate to="/dashboard" replace />} />

        {/* Dashboard - shipment list */}
        <Route path="dashboard" element={<Dashboard />} />

        {/* Shipment detail page */}
        <Route path="shipment/:id" element={<Shipment />} />
      </Route>

      {/* Catch-all redirect to login or dashboard based on auth state */}
      <Route
        path="*"
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  )
}

export default App
