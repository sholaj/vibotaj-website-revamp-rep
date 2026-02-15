/**
 * TraceHub Application Root Component — PRD-008 v2 Infrastructure Bridge
 *
 * Changes from v1:
 * - Login is handled by PropelAuth (redirect to hosted page)
 * - ProtectedRoute uses PropelAuth + AuthContext (same interface)
 * - No login form — unauthenticated users are redirected to PropelAuth
 * - Code splitting preserved for all page components
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense, type ReactNode } from 'react'
import { useRedirectFunctions } from '@propelauth/react'
import Layout from './components/Layout'
import { AuthProvider, useAuth } from './contexts/AuthContext'

// Lazy-loaded page components for code splitting (FE-002)
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Shipment = lazy(() => import('./pages/Shipment'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Users = lazy(() => import('./pages/Users'))
const Organizations = lazy(() => import('./pages/Organizations'))
const AcceptInvitation = lazy(() => import('./pages/AcceptInvitation'))

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

// Suspense wrapper for lazy-loaded page components (FE-002)
function PageSuspense({ children }: { children: ReactNode }) {
  return <Suspense fallback={<LoadingSpinner />}>{children}</Suspense>
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

// Protected route wrapper — redirects to PropelAuth login if unauthenticated
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const { redirectToLoginPage } = useRedirectFunctions()

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    // Redirect to PropelAuth hosted login page
    redirectToLoginPage()
    return <LoadingSpinner />
  }

  return <>{children}</>
}

// Inner app component that uses auth context
function AppRoutes() {
  const { isAuthenticated, isLoading, error, logout, refreshUser } = useAuth()

  // Handle logout
  const handleLogout = () => {
    logout()
  }

  // Handle retry after error
  const handleRetry = () => {
    refreshUser()
  }

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
      {/* Public invitation acceptance route */}
      <Route path="/accept-invitation/:token" element={<PageSuspense><AcceptInvitation /></PageSuspense>} />

      {/* Login route — redirect to PropelAuth or dashboard */}
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            // PropelAuth handles login — redirect there
            <LoginRedirect />
          )
        }
      />

      {/* Protected routes wrapped in Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout onLogout={handleLogout} />
          </ProtectedRoute>
        }
      >
        {/* Default redirect to dashboard */}
        <Route index element={<Navigate to="/dashboard" replace />} />

        {/* Dashboard - shipment list */}
        <Route path="dashboard" element={<PageSuspense><Dashboard /></PageSuspense>} />

        {/* Analytics dashboard */}
        <Route path="analytics" element={<PageSuspense><Analytics /></PageSuspense>} />

        {/* User management (admin only) */}
        <Route path="users" element={<PageSuspense><Users /></PageSuspense>} />

        {/* Organization management (admin only) */}
        <Route path="organizations" element={<PageSuspense><Organizations /></PageSuspense>} />

        {/* Shipment detail page */}
        <Route path="shipment/:id" element={<PageSuspense><Shipment /></PageSuspense>} />
      </Route>

      {/* Catch-all redirect to dashboard (or PropelAuth login) */}
      <Route
        path="*"
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <LoginRedirect />
          )
        }
      />
    </Routes>
  )
}

/**
 * Component that redirects to PropelAuth login page.
 * Used instead of rendering the v1 login form.
 */
function LoginRedirect() {
  const { redirectToLoginPage } = useRedirectFunctions()
  redirectToLoginPage()
  return <LoadingSpinner />
}

// Main App component wrapped in AuthProvider
function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App
