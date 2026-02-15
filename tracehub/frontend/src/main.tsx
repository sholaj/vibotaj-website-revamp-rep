/**
 * TraceHub Frontend Entry Point — PRD-008 v2 Infrastructure Bridge
 *
 * - PropelAuth AuthProvider wraps the entire app
 * - Sentry error tracking initialized before render
 * - React Router provides client-side routing
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider as PropelAuthProvider } from '@propelauth/react'
import * as Sentry from '@sentry/react'
import App from './App'
import './index.css'

// Initialize Sentry (PRD-008)
const sentryDsn = import.meta.env.VITE_SENTRY_DSN
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    environment: import.meta.env.VITE_ENVIRONMENT || 'development',
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    tracesSampleRate: import.meta.env.VITE_ENVIRONMENT === 'production' ? 0.1 : 1.0,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 1.0,
    sendDefaultPii: false,
  })
}

const propelAuthUrl = import.meta.env.VITE_PROPELAUTH_URL

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Sentry.ErrorBoundary
      fallback={({ error }) => (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-4">{(error as Error)?.message || 'An unexpected error occurred.'}</p>
            <button
              onClick={() => window.location.reload()}
              className="btn-primary w-full"
            >
              Reload Page
            </button>
          </div>
        </div>
      )}
    >
      {propelAuthUrl ? (
        <PropelAuthProvider authUrl={propelAuthUrl}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </PropelAuthProvider>
      ) : (
        // Development without PropelAuth — render directly
        <BrowserRouter>
          <App />
        </BrowserRouter>
      )}
    </Sentry.ErrorBoundary>
  </React.StrictMode>,
)
