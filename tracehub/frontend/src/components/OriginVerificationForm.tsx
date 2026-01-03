/**
 * Origin Verification Form Component
 *
 * Form for verifying and updating origin data for EUDR compliance.
 * Includes:
 * - Geolocation input with coordinate validation
 * - Production date picker with EUDR cutoff check
 * - Country selection with risk level display
 * - Supplier attestation fields
 * - Real-time validation feedback
 */

import { useState, useEffect } from 'react'
import {
  MapPin,
  Calendar,
  Building,
  FileCheck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  Globe,
  Info,
} from 'lucide-react'
import api from '../api/client'
import type {
  EUDROriginVerificationRequest,
  EUDROriginValidationResponse,
  EUDRProductionDateCheckResponse,
  EUDRGeolocationCheckResponse,
  RiskLevel,
  VerificationMethod,
} from '../types'

interface OriginVerificationFormProps {
  originId: string
  initialData?: Partial<EUDROriginVerificationRequest>
  onVerificationComplete?: (result: EUDROriginValidationResponse) => void
  onCancel?: () => void
}

// Verification methods options
const VERIFICATION_METHODS: { value: VerificationMethod; label: string }[] = [
  { value: 'document_review', label: 'Document Review' },
  { value: 'supplier_attestation', label: 'Supplier Attestation' },
  { value: 'on_site_inspection', label: 'On-Site Inspection' },
  { value: 'satellite_verification', label: 'Satellite Verification' },
  { value: 'third_party_audit', label: 'Third-Party Audit' },
  { value: 'self_declaration', label: 'Self Declaration' },
]

// Common countries for origin
const COUNTRIES = [
  { code: 'NG', name: 'Nigeria' },
  { code: 'ET', name: 'Ethiopia' },
  { code: 'KE', name: 'Kenya' },
  { code: 'TZ', name: 'Tanzania' },
  { code: 'GH', name: 'Ghana' },
  { code: 'CI', name: "Cote d'Ivoire" },
  { code: 'ZA', name: 'South Africa' },
  { code: 'BR', name: 'Brazil' },
  { code: 'ID', name: 'Indonesia' },
  { code: 'MY', name: 'Malaysia' },
]

// Risk level badge component
function RiskBadge({ level }: { level: RiskLevel }) {
  const config = {
    low: { color: 'bg-success-100 text-success-700', label: 'Low Risk' },
    medium: { color: 'bg-warning-100 text-warning-700', label: 'Medium Risk' },
    high: { color: 'bg-danger-100 text-danger-700', label: 'High Risk' },
    unknown: { color: 'bg-gray-100 text-gray-700', label: 'Unknown' },
  }

  const { color, label } = config[level]

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded ${color}`}>
      {label}
    </span>
  )
}

export default function OriginVerificationForm({
  originId,
  initialData,
  onVerificationComplete,
  onCancel,
}: OriginVerificationFormProps) {
  // Form state
  const [formData, setFormData] = useState<EUDROriginVerificationRequest>({
    farm_plot_identifier: initialData?.farm_plot_identifier || '',
    geolocation_lat: initialData?.geolocation_lat,
    geolocation_lng: initialData?.geolocation_lng,
    country: initialData?.country || '',
    region: initialData?.region || '',
    district: initialData?.district || '',
    production_start_date: initialData?.production_start_date || '',
    production_end_date: initialData?.production_end_date || '',
    supplier_attestation_date: initialData?.supplier_attestation_date || '',
    supplier_attestation_reference: initialData?.supplier_attestation_reference || '',
    deforestation_free_statement: initialData?.deforestation_free_statement || '',
    verification_method: initialData?.verification_method,
  })

  // Validation state
  const [dateCheck, setDateCheck] = useState<EUDRProductionDateCheckResponse | null>(null)
  const [geoCheck, setGeoCheck] = useState<EUDRGeolocationCheckResponse | null>(null)
  const [countryRisk, setCountryRisk] = useState<RiskLevel>('unknown')
  const [isCheckingDate, setIsCheckingDate] = useState(false)
  const [isCheckingGeo, setIsCheckingGeo] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Update form field
  const updateField = <K extends keyof EUDROriginVerificationRequest>(
    field: K,
    value: EUDROriginVerificationRequest[K]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  // Check production date when it changes
  useEffect(() => {
    const checkDate = async () => {
      const dateToCheck = formData.production_end_date || formData.production_start_date
      if (!dateToCheck) {
        setDateCheck(null)
        return
      }

      setIsCheckingDate(true)
      try {
        const result = await api.checkProductionDate({ production_date: dateToCheck })
        setDateCheck(result)
      } catch (err) {
        console.error('Failed to check production date:', err)
      } finally {
        setIsCheckingDate(false)
      }
    }

    const timer = setTimeout(checkDate, 500) // Debounce
    return () => clearTimeout(timer)
  }, [formData.production_start_date, formData.production_end_date])

  // Check geolocation when coordinates change
  useEffect(() => {
    const checkGeo = async () => {
      if (
        formData.geolocation_lat === undefined ||
        formData.geolocation_lng === undefined ||
        !formData.country
      ) {
        setGeoCheck(null)
        return
      }

      setIsCheckingGeo(true)
      try {
        const result = await api.checkGeolocation({
          lat: formData.geolocation_lat,
          lng: formData.geolocation_lng,
          country: formData.country,
        })
        setGeoCheck(result)
        setCountryRisk(result.risk_assessment.country_risk)
      } catch (err) {
        console.error('Failed to check geolocation:', err)
      } finally {
        setIsCheckingGeo(false)
      }
    }

    const timer = setTimeout(checkGeo, 500) // Debounce
    return () => clearTimeout(timer)
  }, [formData.geolocation_lat, formData.geolocation_lng, formData.country])

  // Fetch country risk when country changes
  useEffect(() => {
    const fetchCountryRisk = async () => {
      if (!formData.country) {
        setCountryRisk('unknown')
        return
      }

      try {
        const riskLevels = await api.getCountryRiskLevels()
        const risk = riskLevels.risk_levels[formData.country] || 'unknown'
        setCountryRisk(risk)
      } catch (err) {
        console.error('Failed to fetch country risk:', err)
      }
    }

    fetchCountryRisk()
  }, [formData.country])

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      const result = await api.verifyOrigin(originId, formData)
      onVerificationComplete?.(result)
    } catch (err) {
      console.error('Verification failed:', err)
      setError('Failed to verify origin. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Farm/Plot Identification */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Farm/Plot Identifier *
        </label>
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={formData.farm_plot_identifier || ''}
            onChange={(e) => updateField('farm_plot_identifier', e.target.value)}
            placeholder="e.g., FARM-NG-001"
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            required
          />
        </div>
      </div>

      {/* Geolocation */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Latitude *
          </label>
          <input
            type="number"
            step="any"
            min="-90"
            max="90"
            value={formData.geolocation_lat ?? ''}
            onChange={(e) =>
              updateField('geolocation_lat', e.target.value ? parseFloat(e.target.value) : undefined)
            }
            placeholder="-90 to 90"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Longitude *
          </label>
          <input
            type="number"
            step="any"
            min="-180"
            max="180"
            value={formData.geolocation_lng ?? ''}
            onChange={(e) =>
              updateField('geolocation_lng', e.target.value ? parseFloat(e.target.value) : undefined)
            }
            placeholder="-180 to 180"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            required
          />
        </div>
      </div>

      {/* Geolocation validation feedback */}
      {isCheckingGeo && (
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Checking geolocation...</span>
        </div>
      )}
      {geoCheck && !isCheckingGeo && (
        <div
          className={`p-3 rounded-md text-sm ${
            geoCheck.validation.is_valid ? 'bg-success-50' : 'bg-warning-50'
          }`}
        >
          <div className="flex items-start space-x-2">
            {geoCheck.validation.is_valid ? (
              <CheckCircle className="h-4 w-4 text-success-600 mt-0.5" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-warning-600 mt-0.5" />
            )}
            <div>
              <span
                className={
                  geoCheck.validation.is_valid ? 'text-success-700' : 'text-warning-700'
                }
              >
                {geoCheck.validation.is_valid
                  ? 'Coordinates are valid'
                  : 'Coordinates may be outside country boundaries'}
              </span>
              {geoCheck.risk_assessment.recommendations.length > 0 && (
                <p className="text-xs text-gray-600 mt-1">
                  {geoCheck.risk_assessment.recommendations[0]}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Country and Region */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Country *
          </label>
          <div className="relative">
            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <select
              value={formData.country || ''}
              onChange={(e) => updateField('country', e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            >
              <option value="">Select country</option>
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          {formData.country && (
            <div className="mt-1">
              <RiskBadge level={countryRisk} />
            </div>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Region
          </label>
          <input
            type="text"
            value={formData.region || ''}
            onChange={(e) => updateField('region', e.target.value)}
            placeholder="e.g., Northern Region"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            District
          </label>
          <input
            type="text"
            value={formData.district || ''}
            onChange={(e) => updateField('district', e.target.value)}
            placeholder="e.g., Tamale District"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Production Dates */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Production Start Date *
          </label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="date"
              value={formData.production_start_date || ''}
              onChange={(e) => updateField('production_start_date', e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Production End Date
          </label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="date"
              value={formData.production_end_date || ''}
              onChange={(e) => updateField('production_end_date', e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Production date validation feedback */}
      {isCheckingDate && (
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Checking production date...</span>
        </div>
      )}
      {dateCheck && !isCheckingDate && (
        <div
          className={`p-3 rounded-md text-sm ${
            dateCheck.is_valid ? 'bg-success-50' : 'bg-danger-50'
          }`}
        >
          <div className="flex items-start space-x-2">
            {dateCheck.is_valid ? (
              <CheckCircle className="h-4 w-4 text-success-600 mt-0.5" />
            ) : (
              <XCircle className="h-4 w-4 text-danger-600 mt-0.5" />
            )}
            <div>
              <span className={dateCheck.is_valid ? 'text-success-700' : 'text-danger-700'}>
                {dateCheck.message}
              </span>
              {dateCheck.days_after_cutoff !== null && (
                <p className="text-xs text-gray-600 mt-1">
                  {dateCheck.days_after_cutoff} days after EUDR cutoff ({dateCheck.cutoff_date})
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Supplier Attestation */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-700 flex items-center space-x-2">
          <Building className="h-4 w-4" />
          <span>Supplier Attestation</span>
        </h4>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Attestation Date
            </label>
            <input
              type="date"
              value={formData.supplier_attestation_date || ''}
              onChange={(e) => updateField('supplier_attestation_date', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Attestation Reference
            </label>
            <input
              type="text"
              value={formData.supplier_attestation_reference || ''}
              onChange={(e) => updateField('supplier_attestation_reference', e.target.value)}
              placeholder="e.g., ATT-2024-001"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Deforestation Free Statement */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Deforestation-Free Statement
        </label>
        <textarea
          value={formData.deforestation_free_statement || ''}
          onChange={(e) => updateField('deforestation_free_statement', e.target.value)}
          placeholder="Enter the supplier's deforestation-free declaration..."
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      {/* Verification Method */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Verification Method *
        </label>
        <div className="relative">
          <FileCheck className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <select
            value={formData.verification_method || ''}
            onChange={(e) =>
              updateField('verification_method', e.target.value as VerificationMethod)
            }
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            required
          >
            <option value="">Select verification method</option>
            {VERIFICATION_METHODS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* EUDR Info */}
      <div className="p-3 bg-blue-50 rounded-md">
        <div className="flex items-start space-x-2">
          <Info className="h-4 w-4 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-700">
            <p className="font-medium">EUDR Compliance Requirements</p>
            <ul className="list-disc list-inside mt-1 text-xs text-blue-600">
              <li>Production must be after December 31, 2020</li>
              <li>Precise geolocation coordinates are mandatory</li>
              <li>Supplier attestation is required for due diligence</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-danger-50 rounded-md">
          <div className="flex items-center space-x-2 text-danger-700">
            <AlertTriangle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
        )}
        <button type="submit" disabled={isSubmitting} className="btn-primary">
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Verifying...
            </>
          ) : (
            <>
              <CheckCircle className="h-4 w-4 mr-2" />
              Verify Origin
            </>
          )}
        </button>
      </div>
    </form>
  )
}
