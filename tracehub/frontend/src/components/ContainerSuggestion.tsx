/**
 * ContainerSuggestion Component
 *
 * Displays a suggestion banner when AI extracts a container number from
 * a Bill of Lading document and the shipment still has a placeholder
 * container number. Allows users to accept or dismiss the suggestion.
 */

import React, { useState } from 'react'
import { Info, Check, X, Loader } from 'lucide-react'

interface ContainerSuggestionProps {
  extractedContainer: string
  confidence: number
  shipmentId: string  // Kept for potential future use (logging, analytics)
  currentContainer: string
  onAccept: (container: string) => Promise<void>
  onDismiss: () => void
}

export const ContainerSuggestion: React.FC<ContainerSuggestionProps> = ({
  extractedContainer,
  confidence,
  shipmentId: _shipmentId,  // Prefixed to avoid unused variable error
  currentContainer,
  onAccept,
  onDismiss,
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAccept = async () => {
    setIsLoading(true)
    setError(null)
    try {
      await onAccept(extractedContainer)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update container')
    } finally {
      setIsLoading(false)
    }
  }

  // Don't show if current container is already valid (not a placeholder)
  const isPlaceholder =
    currentContainer.includes('-CNT-') || currentContainer.includes('PLACEHOLDER')
  if (!isPlaceholder) return null

  const confidencePercent = Math.round(confidence * 100)
  const confidenceColor =
    confidence >= 0.9
      ? 'text-success-600'
      : confidence >= 0.7
        ? 'text-warning-600'
        : 'text-orange-600'

  return (
    <div className="bg-primary-50 border-l-4 border-primary-400 p-4 mb-6 rounded-r-lg">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <Info className="h-5 w-5 text-primary-500" />
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-primary-800">
            Container Number Detected
          </h3>
          <div className="mt-2 text-sm text-primary-700">
            <p>
              A Bill of Lading document contains container number:{' '}
              <strong className="font-mono bg-primary-100 px-1.5 py-0.5 rounded">
                {extractedContainer}
              </strong>
            </p>
            <p className="mt-1">
              Confidence:{' '}
              <span className={`font-medium ${confidenceColor}`}>
                {confidencePercent}%
              </span>
            </p>
            <p className="mt-1 text-gray-500">
              Current placeholder:{' '}
              <span className="font-mono text-gray-600">{currentContainer}</span>
            </p>
          </div>
          {error && (
            <p className="mt-2 text-sm text-danger-600 flex items-center">
              <X className="h-4 w-4 mr-1" />
              {error}
            </p>
          )}
          <div className="mt-4 flex gap-3">
            <button
              onClick={handleAccept}
              disabled={isLoading}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <>
                  <Loader className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Check className="h-3.5 w-3.5 mr-1.5" />
                  Accept & Update
                </>
              )}
            </button>
            <button
              onClick={onDismiss}
              disabled={isLoading}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <X className="h-3.5 w-3.5 mr-1.5" />
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ContainerSuggestion
