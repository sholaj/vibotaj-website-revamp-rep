/**
 * Authentication Context — PropelAuth Bridge (PRD-008)
 *
 * Same interface as v1 AuthContext, but powered by PropelAuth.
 * - PropelAuth manages login/logout (redirect-based)
 * - User details hydrated from backend /auth/me/full
 * - Permission/role helpers unchanged
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useAuthInfo, useLogoutFunction, useRedirectFunctions } from '@propelauth/react'
import api, { setCachedToken } from '../api/client'
import { setAccessTokenFn, clearLegacyTokens } from '../api/auth-bridge'
import type { CurrentUser, UserRole, OrgRole, OrganizationType, OrgPermission } from '../types'

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
  // Organization-scoped permission checking
  orgRole: OrgRole | null
  orgType: OrganizationType | null
  hasOrgPermission: (permission: OrgPermission) => boolean
  hasAnyOrgPermission: (permissions: OrgPermission[]) => boolean
  hasAllOrgPermissions: (permissions: OrgPermission[]) => boolean
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
  const propelAuth = useAuthInfo()
  const propelLogout = useLogoutFunction()
  const { redirectToLoginPage } = useRedirectFunctions()
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Clean up v1 JWT tokens on first load
  useEffect(() => {
    clearLegacyTokens()
  }, [])

  // Wire PropelAuth token into the auth bridge + API client
  useEffect(() => {
    if (propelAuth.loading) return

    if (propelAuth.isLoggedIn && propelAuth.accessToken) {
      // Update cached token for synchronous access in interceptors
      setCachedToken(propelAuth.accessToken)

      // Set async token accessor for token refresh scenarios
      setAccessTokenFn(async () => propelAuth.accessToken ?? null)
    } else {
      setCachedToken(null)
      setAccessTokenFn(async () => null)
    }
  }, [propelAuth.loading, propelAuth.isLoggedIn, propelAuth.accessToken])

  // Fetch TraceHub user details when PropelAuth is authenticated
  useEffect(() => {
    const fetchUserDetails = async () => {
      if (propelAuth.loading) return

      if (!propelAuth.isLoggedIn) {
        setUser(null)
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      try {
        const userDetails = await api.getCurrentUserFull()
        setUser(userDetails)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch user details:', err)
        setUser(null)
        setError('Failed to load user profile. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchUserDetails()
  }, [propelAuth.loading, propelAuth.isLoggedIn, propelAuth.accessToken])

  // Login: redirect to PropelAuth hosted login page
  const login = useCallback((_token: string) => {
    redirectToLoginPage()
  }, [redirectToLoginPage])

  // Logout: PropelAuth SDK + clear local state
  const logout = useCallback(async () => {
    try {
      await propelLogout(false) // false = don't redirect
    } catch {
      // PropelAuth logout may fail if already logged out
    }
    setCachedToken(null)
    api.logout()
    setUser(null)
    setError(null)
  }, [propelLogout])

  const refreshUser = useCallback(async () => {
    try {
      const userDetails = await api.getCurrentUserFull()
      setUser(userDetails)
      setError(null)
    } catch (err) {
      console.error('Failed to refresh user:', err)
    }
  }, [])

  // Permission checking functions (unchanged from v1)
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

  // Organization permission checking functions
  const hasOrgPermission = useCallback((permission: OrgPermission): boolean => {
    if (!user || !user.org_permissions) return false
    return user.org_permissions.includes(permission)
  }, [user])

  const hasAnyOrgPermission = useCallback((permissions: OrgPermission[]): boolean => {
    if (!user || !user.org_permissions) return false
    return permissions.some(p => user.org_permissions!.includes(p))
  }, [user])

  const hasAllOrgPermissions = useCallback((permissions: OrgPermission[]): boolean => {
    if (!user || !user.org_permissions) return false
    return permissions.every(p => user.org_permissions!.includes(p))
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

  // Organization context
  const orgRole = user?.org_role ?? null
  const orgType = user?.org_type ?? null

  // Common permission checks
  const canManageUsers = hasPermission(Permission.USERS_CREATE)
  const canValidateDocuments = hasPermission(Permission.DOCUMENTS_VALIDATE)
  const canUploadDocuments = hasPermission(Permission.DOCUMENTS_UPLOAD)

  const value: AuthContextType = {
    user,
    isAuthenticated: propelAuth.isLoggedIn === true && !!user,
    isLoading: propelAuth.loading || isLoading,
    error,
    login,
    logout,
    refreshUser,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    // Organization permission helpers
    orgRole,
    orgType,
    hasOrgPermission,
    hasAnyOrgPermission,
    hasAllOrgPermissions,
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
