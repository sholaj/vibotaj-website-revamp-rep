/**
 * User Management Page
 *
 * Admin-only page to manage users, create new accounts, and update roles.
 */

import { useState, useEffect, useCallback } from 'react'
import { Users as UsersIcon, Plus, Search, Shield, Check, X, RefreshCw, UserPlus, Key, Lock, Edit2 } from 'lucide-react'
import api, { ApiClientError } from '../api/client'
import { useAuth, Permission } from '../contexts/AuthContext'
import PermissionGuard from '../components/PermissionGuard'
import type { UserResponse, UserRole, RoleInfo, UserCreate, UserUpdate, OrganizationType } from '../types'

// Role badge styling
const roleBadgeStyles: Record<UserRole, string> = {
  admin: 'bg-purple-100 text-purple-800',
  compliance: 'bg-blue-100 text-blue-800',
  logistics_agent: 'bg-teal-100 text-teal-800',
  buyer: 'bg-green-100 text-green-800',
  supplier: 'bg-orange-100 text-orange-800',
  viewer: 'bg-gray-100 text-gray-800',
}

const roleLabels: Record<UserRole, string> = {
  admin: 'Admin',
  compliance: 'Compliance',
  logistics_agent: 'Logistics Agent',
  buyer: 'Buyer',
  supplier: 'Supplier',
  viewer: 'Viewer',
}

// Organization type badge styling
const orgTypeBadgeStyles: Record<OrganizationType, string> = {
  vibotaj: 'bg-purple-100 text-purple-800',
  buyer: 'bg-green-100 text-green-800',
  supplier: 'bg-orange-100 text-orange-800',
  logistics_agent: 'bg-teal-100 text-teal-800',
}

const orgTypeLabels: Record<OrganizationType, string> = {
  vibotaj: 'VIBOTAJ',
  buyer: 'Buyer',
  supplier: 'Supplier',
  logistics_agent: 'Logistics',
}

function EditUserModal({
  isOpen,
  onClose,
  onUpdated,
  user,
  roles,
}: {
  isOpen: boolean
  onClose: () => void
  onUpdated: () => void
  user: UserResponse | null
  roles: RoleInfo[]
}) {
  const [formData, setFormData] = useState<UserUpdate>({})
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email,
        full_name: user.full_name,
        role: user.role,
        is_active: user.is_active,
      })
      setNewPassword('')
      setSuccess(null)
      setError(null)
    }
  }, [user])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      await api.updateUser(user.id, formData)
      setSuccess('User updated successfully')
      onUpdated()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update user')
    } finally {
      setLoading(false)
    }
  }

  const handleResetPassword = async () => {
    if (!user || !newPassword) return
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      await api.adminResetPassword(user.id, newPassword)
      setSuccess('Password reset successfully')
      setNewPassword('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset password')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen || !user) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Edit2 className="h-5 w-5 mr-2 text-primary-600" />
            Edit User: {user.full_name}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Profile Information</h4>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={formData.full_name || ''}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                value={formData.role || ''}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
              >
                {roles.filter(r => r.can_assign || r.value === user.role).map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              Update Profile
            </button>
          </form>

          <div className="pt-6 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Security</h4>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reset Password</label>
                <div className="flex space-x-2">
                  <div className="relative flex-1">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500"
                      placeholder="New password"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleResetPassword}
                    disabled={loading || !newPassword}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 flex items-center"
                  >
                    <Key className="h-4 w-4 mr-2" />
                    Reset
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function CreateUserModal({
  isOpen,
  onClose,
  onCreated,
  roles,
}: {
  isOpen: boolean
  onClose: () => void
  onCreated: () => void
  roles: RoleInfo[]
}) {
  const [formData, setFormData] = useState<UserCreate>({
    email: '',
    full_name: '',
    password: '',
    role: 'viewer',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      await api.createUser(formData)
      onCreated()
      onClose()
      setFormData({ email: '', full_name: '', password: '', role: 'viewer' })
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Failed to create user')
      } else {
        setError('Failed to create user')
      }
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <UserPlus className="h-5 w-5 mr-2 text-primary-600" />
            Create New User
          </h3>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="user@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name
            </label>
            <input
              type="text"
              required
              minLength={2}
              maxLength={100}
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Min 8 chars, upper, lower, number"
            />
            <p className="text-xs text-gray-500 mt-1">
              Must contain uppercase, lowercase, and a number
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {roles.filter(r => r.can_assign).map((role) => (
                <option key={role.value} value={role.value}>
                  {role.name} - {role.description}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Users() {
  const { hasPermission } = useAuth()
  const [users, setUsers] = useState<UserResponse[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<UserRole | ''>('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserResponse | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const params: any = {}
      if (search) params.search = search
      if (roleFilter) params.role = roleFilter

      const [usersData, rolesData] = await Promise.all([
        api.getUsers(params),
        api.getRoles(),
      ])

      setUsers(usersData.items)
      setRoles(rolesData.roles)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Failed to load users')
      } else {
        setError('Failed to load users')
      }
    } finally {
      setLoading(false)
    }
  }, [search, roleFilter])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const handleToggleActive = async (user: UserResponse, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent row click
    try {
      if (user.is_active) {
        await api.deactivateUser(user.id)
      } else {
        await api.activateUser(user.id)
      }
      fetchUsers()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Failed to update user status')
      } else {
        setError('Failed to update user status')
      }
    }
  }

  const handleRowClick = (user: UserResponse) => {
    setSelectedUser(user)
    setShowEditModal(true)
  }

  // Check if user has permission to view this page
  if (!hasPermission(Permission.USERS_LIST)) {
    return (
      <div className="text-center py-12">
        <Shield className="h-12 w-12 mx-auto text-gray-400 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
        <p className="text-gray-600">You don't have permission to view user management.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <UsersIcon className="h-7 w-7 mr-3 text-primary-600" />
            User Management
          </h1>
          <p className="text-gray-600 mt-1">Manage users and their access roles</p>
        </div>

        <PermissionGuard permission={Permission.USERS_CREATE}>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add User
          </button>
        </PermissionGuard>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value as UserRole | '')}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Roles</option>
            {roles.map((role) => (
              <option key={role.value} value={role.value}>
                {role.name}
              </option>
            ))}
          </select>

          <button
            onClick={fetchUsers}
            className="flex items-center px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-md"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading users...</p>
          </div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No users found
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Organization
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Login
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr
                  key={user.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleRowClick(user)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {user.full_name}
                      </div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleBadgeStyles[user.role]}`}>
                      {user.role === 'admin' && <Shield className="h-3 w-3 mr-1" />}
                      {roleLabels[user.role]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.primary_organization ? (
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {user.primary_organization.organization_name}
                        </div>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${orgTypeBadgeStyles[user.primary_organization.organization_type]}`}>
                          {orgTypeLabels[user.primary_organization.organization_type]}
                        </span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400 italic">No organization</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.is_active ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <Check className="h-3 w-3 mr-1" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <X className="h-3 w-3 mr-1" />
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.last_login
                      ? new Date(user.last_login).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <PermissionGuard permission={Permission.USERS_UPDATE}>
                      <button
                        onClick={(e) => handleToggleActive(user, e)}
                        className={`text-sm px-3 py-1 rounded ${user.is_active
                          ? 'text-red-600 hover:bg-red-50'
                          : 'text-green-600 hover:bg-green-50'
                          }`}
                      >
                        {user.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </PermissionGuard>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create User Modal */}
      <CreateUserModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={fetchUsers}
        roles={roles}
      />

      {/* Edit User Modal */}
      <EditUserModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          setSelectedUser(null)
        }}
        onUpdated={fetchUsers}
        user={selectedUser}
        roles={roles}
      />
    </div>
  )
}
