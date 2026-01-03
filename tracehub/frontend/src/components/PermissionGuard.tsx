/**
 * PermissionGuard Component
 *
 * Conditionally renders children based on user permissions or roles.
 * Provides role-based access control for UI elements.
 *
 * Usage:
 *   <PermissionGuard permission="documents:validate">
 *     <ValidateButton />
 *   </PermissionGuard>
 *
 *   <PermissionGuard roles={['admin', 'compliance']}>
 *     <AdminPanel />
 *   </PermissionGuard>
 *
 *   <PermissionGuard permissions={['documents:read', 'documents:update']} requireAll={false}>
 *     <EditButton />
 *   </PermissionGuard>
 */

import React from 'react'
import { useAuth, PermissionKey } from '../contexts/AuthContext'
import type { UserRole } from '../types'

interface PermissionGuardProps {
  children: React.ReactNode
  /** Single permission to check */
  permission?: PermissionKey
  /** Multiple permissions to check (use with requireAll) */
  permissions?: PermissionKey[]
  /** Single role to check */
  role?: UserRole
  /** Multiple roles to check (any match allows access) */
  roles?: UserRole[]
  /** If true, all permissions must be present; if false, any one is sufficient (default: true) */
  requireAll?: boolean
  /** What to render if access is denied (default: null) */
  fallback?: React.ReactNode
  /** If true, shows a "no access" message instead of hiding content */
  showDenied?: boolean
}

export function PermissionGuard({
  children,
  permission,
  permissions,
  role,
  roles,
  requireAll = true,
  fallback = null,
  showDenied = false,
}: PermissionGuardProps) {
  const { hasPermission, hasAnyPermission, hasAllPermissions, hasRole, hasAnyRole } = useAuth()

  let hasAccess = true

  // Check single permission
  if (permission) {
    hasAccess = hasPermission(permission)
  }

  // Check multiple permissions
  if (permissions && permissions.length > 0) {
    hasAccess = requireAll
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions)
  }

  // Check single role
  if (role) {
    hasAccess = hasRole(role)
  }

  // Check multiple roles (any match)
  if (roles && roles.length > 0) {
    hasAccess = hasAnyRole(roles)
  }

  if (hasAccess) {
    return <>{children}</>
  }

  if (showDenied) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
        <div className="text-gray-400 mb-2">
          <svg
            className="h-8 w-8 mx-auto"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>
        <p className="text-sm text-gray-500">
          You don't have permission to view this content.
        </p>
      </div>
    )
  }

  return <>{fallback}</>
}

/**
 * HOC version of PermissionGuard for wrapping entire components
 */
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  permission: PermissionKey
) {
  return function WrappedComponent(props: P) {
    return (
      <PermissionGuard permission={permission}>
        <Component {...props} />
      </PermissionGuard>
    )
  }
}

/**
 * HOC version for role-based access
 */
export function withRole<P extends object>(
  Component: React.ComponentType<P>,
  roles: UserRole[]
) {
  return function WrappedComponent(props: P) {
    return (
      <PermissionGuard roles={roles}>
        <Component {...props} />
      </PermissionGuard>
    )
  }
}

/**
 * Hook to check if current route/action is accessible
 */
export function usePermissionCheck() {
  const { hasPermission, hasAnyPermission, hasRole, hasAnyRole } = useAuth()

  return {
    canAccess: (options: {
      permission?: PermissionKey
      permissions?: PermissionKey[]
      role?: UserRole
      roles?: UserRole[]
      requireAll?: boolean
    }) => {
      const { permission, permissions, role, roles, requireAll = true } = options

      if (permission) {
        return hasPermission(permission)
      }

      if (permissions && permissions.length > 0) {
        return requireAll ? permissions.every(p => hasPermission(p)) : hasAnyPermission(permissions)
      }

      if (role) {
        return hasRole(role)
      }

      if (roles && roles.length > 0) {
        return hasAnyRole(roles)
      }

      return true
    },
  }
}

export default PermissionGuard
