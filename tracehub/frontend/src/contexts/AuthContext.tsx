/**
 * Authentication Context
 *
 * Provides authentication state and role-based access control throughout the app.
 * Includes:
 * - User state management
 * - Role and permission checking
 * - Login/logout handling
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import api from '../api/client'
import type { CurrentUser, UserRole } from '../types'

// Permission definitions aligned with backend
export const Permission = {
  // User management
  USERS_CREATE: 'users:create',
  USERS_READ: 'users:read',
  USERS_UPDATE: 'users:update',
  USERS_DELETE: 'users:delete',
  USERS_LIST: 'users:list',

  // Shipment permissions
  SHIPMENTS_CREATE: 'shipments:create',
  SHIPMENTS_READ: 'shipments:read',
  SHIPMENTS_UPDATE: 'shipments:update',
  SHIPMENTS_DELETE: 'shipments:delete',
  SHIPMENTS_LIST: 'shipments:list',

  // Document permissions
  DOCUMENTS_CREATE: 'documents:create',
  DOCUMENTS_READ: 'documents:read',
  DOCUMENTS_UPDATE: 'documents:update',
  DOCUMENTS_DELETE: 'documents:delete',
  DOCUMENTS_UPLOAD: 'documents:upload',
  DOCUMENTS_VALIDATE: 'documents:validate',
  DOCUMENTS_APPROVE: 'documents:approve',
  DOCUMENTS_REJECT: 'documents:reject',
  DOCUMENTS_TRANSITION: 'documents:transition',

  // Tracking permissions
  TRACKING_READ: 'tracking:read',
  TRACKING_REFRESH: 'tracking:refresh',

  // Audit pack
  AUDIT_PACK_DOWNLOAD: 'audit_pack:download',

  // Admin-only
  SYSTEM_ADMIN: 'system:admin',
} as const

export type PermissionKey = typeof Permission[keyof typeof Permission]

interface AuthContextType {
  user: CurrentUser | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (token: string) => void
  logout: () => void
  refreshUser: () => Promise<void>
  hasPermission: (permission: PermissionKey) => boolean
  hasAnyPermission: (permissions: PermissionKey[]) => boolean
  hasAllPermissions: (permissions: PermissionKey[]) => boolean
  hasRole: (role: UserRole) => boolean
  hasAnyRole: (roles: UserRole[]) => boolean
  isAdmin: boolean
  isCompliance: boolean
  isBuyer: boolean
  isSupplier: boolean
  isViewer: boolean
  canManageUsers: boolean
  canValidateDocuments: boolean
  canUploadDocuments: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch full user details including permissions
  const fetchUserDetails = useCallback(async () => {
    try {
      const userDetails = await api.getCurrentUserFull()
      setUser(userDetails)
      setError(null)
      return true
    } catch (err) {
      console.error('Failed to fetch user details:', err)
      setUser(null)
      return false
    }
  }, [])

  // Verify authentication on mount
  useEffect(() => {
    const verifyAuth = async () => {
      setIsLoading(true)
      try {
        if (api.isAuthenticated()) {
          const isValid = await api.verifyToken()
          if (isValid) {
            await fetchUserDetails()
          } else {
            api.logout()
          }
        }
      } catch (err) {
        console.error('Auth verification failed:', err)
        if (api.isAuthenticated()) {
          setError('Session expired. Please log in again.')
          api.logout()
        }
      } finally {
        setIsLoading(false)
      }
    }

    verifyAuth()
  }, [fetchUserDetails])

  const login = useCallback(async (token: string) => {
    // Token is already stored by api.login()
    await fetchUserDetails()
    setError(null)
  }, [fetchUserDetails])

  const logout = useCallback(() => {
    api.logout()
    setUser(null)
    setError(null)
  }, [])

  const refreshUser = useCallback(async () => {
    await fetchUserDetails()
  }, [fetchUserDetails])

  // Permission checking functions
  const hasPermission = useCallback((permission: PermissionKey): boolean => {
    if (!user) return false
    return user.permissions.includes(permission)
  }, [user])

  const hasAnyPermission = useCallback((permissions: PermissionKey[]): boolean => {
    if (!user) return false
    return permissions.some(p => user.permissions.includes(p))
  }, [user])

  const hasAllPermissions = useCallback((permissions: PermissionKey[]): boolean => {
    if (!user) return false
    return permissions.every(p => user.permissions.includes(p))
  }, [user])

  const hasRole = useCallback((role: UserRole): boolean => {
    if (!user) return false
    return user.role === role
  }, [user])

  const hasAnyRole = useCallback((roles: UserRole[]): boolean => {
    if (!user) return false
    return roles.includes(user.role)
  }, [user])

  // Convenience boolean flags
  const isAdmin = user?.role === 'admin'
  const isCompliance = user?.role === 'compliance'
  const isBuyer = user?.role === 'buyer'
  const isSupplier = user?.role === 'supplier'
  const isViewer = user?.role === 'viewer'

  // Common permission checks
  const canManageUsers = hasPermission(Permission.USERS_CREATE)
  const canValidateDocuments = hasPermission(Permission.DOCUMENTS_VALIDATE)
  const canUploadDocuments = hasPermission(Permission.DOCUMENTS_UPLOAD)

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    logout,
    refreshUser,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    isAdmin,
    isCompliance,
    isBuyer,
    isSupplier,
    isViewer,
    canManageUsers,
    canValidateDocuments,
    canUploadDocuments,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Export the context for testing
export { AuthContext }
