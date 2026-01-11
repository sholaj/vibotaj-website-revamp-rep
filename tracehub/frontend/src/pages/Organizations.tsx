/**
 * Organization Management Page
 *
 * Admin-only page to manage organizations (buyers, suppliers, logistics agents).
 *
 * Sprint 13.2: Updated with MemberManagementPanel for full member/invitation management.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Building2,
  Plus,
  Search,
  RefreshCw,
  Users as UsersIcon,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import api, { ApiClientError } from '../api/client'
import { useAuth, Permission } from '../contexts/AuthContext'
import { MemberManagementPanel } from '../components/organizations'
import type {
  OrganizationListItem,
  OrganizationType,
  OrganizationStatus,
  OrganizationCreate,
  Organization,
} from '../types'

// Organization type badge styling
const typeBadgeStyles: Record<OrganizationType, string> = {
  vibotaj: 'bg-purple-100 text-purple-800',
  buyer: 'bg-green-100 text-green-800',
  supplier: 'bg-orange-100 text-orange-800',
  logistics_agent: 'bg-teal-100 text-teal-800',
}

const typeLabels: Record<OrganizationType, string> = {
  vibotaj: 'VIBOTAJ',
  buyer: 'Buyer',
  supplier: 'Supplier',
  logistics_agent: 'Logistics Agent',
}

const statusBadgeStyles: Record<OrganizationStatus, string> = {
  active: 'bg-green-100 text-green-800',
  suspended: 'bg-red-100 text-red-800',
  pending_setup: 'bg-yellow-100 text-yellow-800',
}

// Create Organization Modal
function CreateOrganizationModal({
  isOpen,
  onClose,
  onCreated,
}: {
  isOpen: boolean
  onClose: () => void
  onCreated: () => void
}) {
  const [formData, setFormData] = useState<OrganizationCreate>({
    name: '',
    slug: '',
    type: 'buyer',
    contact_email: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
  }

  const handleNameChange = (name: string) => {
    setFormData({
      ...formData,
      name,
      slug: generateSlug(name),
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      await api.createOrganization(formData)
      onCreated()
      onClose()
      setFormData({ name: '', slug: '', type: 'buyer', contact_email: '' })
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to create organization')
      }
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="text-lg font-semibold">Create Organization</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              ×
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            {error && (
              <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Organization Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleNameChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Slug *
              </label>
              <input
                type="text"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"
                pattern="^[a-z0-9-]+$"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Lowercase letters, numbers, and hyphens only
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type *
              </label>
              <select
                value={formData.type}
                onChange={(e) =>
                  setFormData({ ...formData, type: e.target.value as OrganizationType })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="buyer">Buyer</option>
                <option value="supplier">Supplier</option>
                <option value="logistics_agent">Logistics Agent</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contact Email *
              </label>
              <input
                type="email"
                value={formData.contact_email}
                onChange={(e) =>
                  setFormData({ ...formData, contact_email: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contact Phone
              </label>
              <input
                type="tel"
                value={formData.contact_phone || ''}
                onChange={(e) =>
                  setFormData({ ...formData, contact_phone: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary"
                disabled={loading}
              >
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Creating...' : 'Create Organization'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// Organization Detail Panel
function OrganizationDetailPanel({
  organization,
  onClose,
}: {
  organization: OrganizationListItem | null
  onClose: () => void
}) {
  const { hasPermission } = useAuth()
  const [orgDetails, setOrgDetails] = useState<Organization | null>(null)
  const [loading, setLoading] = useState(false)

  // System admins can always manage members
  const canManageMembers = hasPermission(Permission.SYSTEM_ADMIN)

  useEffect(() => {
    if (organization) {
      loadDetails()
    }
  }, [organization])

  const loadDetails = async () => {
    if (!organization) return
    setLoading(true)
    try {
      const details = await api.getOrganization(organization.id)
      setOrgDetails(details)
    } catch (err) {
      console.error('Failed to load organization details:', err)
    } finally {
      setLoading(false)
    }
  }

  if (!organization) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="absolute inset-y-0 right-0 max-w-lg w-full bg-white shadow-xl flex flex-col">
        <div className="flex items-center justify-between p-4 border-b flex-shrink-0">
          <h3 className="text-lg font-semibold">{organization.name}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            x
          </button>
        </div>

        <div className="p-4 overflow-y-auto flex-1">
          {loading ? (
            <div className="text-center py-8 text-gray-500">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
              Loading...
            </div>
          ) : (
            <>
              {/* Organization Info */}
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">Details</h4>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Slug</dt>
                    <dd className="font-mono">{organization.slug}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Type</dt>
                    <dd>
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${
                          typeBadgeStyles[organization.type]
                        }`}
                      >
                        {typeLabels[organization.type]}
                      </span>
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Status</dt>
                    <dd>
                      <span
                        className={`px-2 py-1 rounded-full text-xs ${
                          statusBadgeStyles[organization.status]
                        }`}
                      >
                        {organization.status}
                      </span>
                    </dd>
                  </div>
                  {orgDetails?.contact_email && (
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Email</dt>
                      <dd>{orgDetails.contact_email}</dd>
                    </div>
                  )}
                  {orgDetails?.contact_phone && (
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Phone</dt>
                      <dd>{orgDetails.contact_phone}</dd>
                    </div>
                  )}
                </dl>
              </div>

              {/* Member Management Panel */}
              <MemberManagementPanel
                organizationId={organization.id}
                organizationName={organization.name}
                canManageMembers={canManageMembers}
              />
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Organizations() {
  const { hasPermission } = useAuth()
  const [organizations, setOrganizations] = useState<OrganizationListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<OrganizationType | ''>('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedOrg, setSelectedOrg] = useState<OrganizationListItem | null>(null)

  const fetchOrganizations = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await api.getOrganizations({
        page,
        limit: 20,
        type: typeFilter || undefined,
        search: search || undefined,
      })
      setOrganizations(response.items)
      setTotalPages(response.pages)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to load organizations')
      }
    } finally {
      setLoading(false)
    }
  }, [page, typeFilter, search])

  useEffect(() => {
    fetchOrganizations()
  }, [fetchOrganizations])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchOrganizations()
  }

  // Check if user has admin permission
  if (!hasPermission(Permission.SYSTEM_ADMIN)) {
    return (
      <div className="text-center py-12">
        <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Access Denied</h3>
        <p className="text-gray-600">You need admin permissions to view this page.</p>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
          <p className="text-gray-600 mt-1">
            Manage buyer, supplier, and logistics organizations
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Organization
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <form onSubmit={handleSearch} className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search organizations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </form>

        <select
          value={typeFilter}
          onChange={(e) => {
            setTypeFilter(e.target.value as OrganizationType | '')
            setPage(1)
          }}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Types</option>
          <option value="buyer">Buyers</option>
          <option value="supplier">Suppliers</option>
          <option value="logistics_agent">Logistics Agents</option>
        </select>

        <button
          onClick={fetchOrganizations}
          className="btn-secondary"
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Organizations Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Organization
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Members
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  Loading organizations...
                </td>
              </tr>
            ) : organizations.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  No organizations found
                </td>
              </tr>
            ) : (
              organizations.map((org) => (
                <tr
                  key={org.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedOrg(org)}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <Building2 className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <div className="font-medium text-gray-900">{org.name}</div>
                        <div className="text-sm text-gray-500 font-mono">{org.slug}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        typeBadgeStyles[org.type]
                      }`}
                    >
                      {typeLabels[org.type]}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        statusBadgeStyles[org.status]
                      }`}
                    >
                      {org.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <UsersIcon className="h-4 w-4 mr-1" />
                      {org.member_count}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(org.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center mt-6 space-x-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary text-sm"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="btn-secondary text-sm"
          >
            Next
          </button>
        </div>
      )}

      {/* Create Modal */}
      <CreateOrganizationModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={fetchOrganizations}
      />

      {/* Detail Panel */}
      <OrganizationDetailPanel
        organization={selectedOrg}
        onClose={() => setSelectedOrg(null)}
      />
    </div>
  )
}
