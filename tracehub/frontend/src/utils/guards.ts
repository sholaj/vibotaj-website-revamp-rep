/**
 * Access Control Guards Utility
 *
 * Composable guards for role and permission-based access control.
 * Used in route guards, component-level access checks, and data filtering.
 */

import type { UserRole, OrgRole, OrganizationType, OrgPermission } from '../types'

/**
 * Guard result indicating whether access is allowed and why.
 * Enables auditable, composable access control patterns.
 */
export interface GuardResult {
  allowed: boolean
  reason?: string
}

/**
 * Helper function to create successful guard results
 */
function allow(): GuardResult {
  return { allowed: true }
}

/**
 * Helper function to create denied guard results with reason
 */
function deny(reason: string): GuardResult {
  return { allowed: false, reason }
}

/**
 * Guard: Check system user role
 * @param userRole - User's system role
 * @param requiredRole - Required role for access
 */
export function canUserRole(
  userRole: UserRole | null | undefined,
  requiredRole: UserRole
): GuardResult {
  if (!userRole) return deny('User role not set')
  if (userRole === requiredRole) return allow()
  
  // Admin can access anything
  if (userRole === 'admin') return allow()
  
  return deny(`User role "${userRole}" does not match required role "${requiredRole}"`)
}

/**
 * Guard: Check organization-scoped role
 * @param orgRole - User's organization role
 * @param requiredRole - Required organization role for access
 */
export function canOrgRole(
  orgRole: OrgRole | null | undefined,
  requiredRole: OrgRole
): GuardResult {
  if (!orgRole) return deny('Organization role not set')
  if (orgRole === requiredRole) return allow()
  
  // Admin can access anything
  if (orgRole === 'admin') return allow()
  
  // Manager can access member-level features
  if (orgRole === 'manager' && requiredRole === 'member') return allow()
  
  // Manager can access viewer-level features
  if (orgRole === 'manager' && requiredRole === 'viewer') return allow()
  
  return deny(`Organization role "${orgRole}" insufficient for required role "${requiredRole}"`)
}

/**
 * Guard: Check organization type
 * @param orgType - Organization type
 * @param requiredType - Required organization type for access
 */
export function canOrgType(
  orgType: OrganizationType | null | undefined,
  requiredType: OrganizationType
): GuardResult {
  if (!orgType) return deny('Organization type not set')
  if (orgType === requiredType) return allow()
  
  return deny(`Organization type "${orgType}" does not match required type "${requiredType}"`)
}

/**
 * Guard: Check system-level permission
 * @param permissions - User's available permissions
 * @param required - Required permission(s)
 * @param options - Guard options
 */
export function canPermission(
  permissions: string[] | null | undefined,
  required: string | string[],
  options: { requireAll?: boolean } = {}
): GuardResult {
  if (!permissions || permissions.length === 0) {
    return deny('No permissions granted')
  }

  const requiredList = Array.isArray(required) ? required : [required]
  const requireAll = options.requireAll ?? true

  if (requireAll) {
    // All required permissions must be present
    const missing = requiredList.filter(p => !permissions.includes(p))
    if (missing.length === 0) return allow()
    return deny(`Missing permissions: ${missing.join(', ')}`)
  } else {
    // At least one required permission must be present
    const hasAny = requiredList.some(p => permissions.includes(p))
    if (hasAny) return allow()
    return deny(`None of the required permissions [${requiredList.join(', ')}] are granted`)
  }
}

/**
 * Guard: Check organization-scoped permission
 * @param orgPermissions - User's organization permissions
 * @param required - Required organization permission(s)
 * @param options - Guard options
 */
export function canOrgPermission(
  orgPermissions: string[] | null | undefined,
  required: OrgPermission | OrgPermission[],
  options: { requireAll?: boolean } = {}
): GuardResult {
  if (!orgPermissions || orgPermissions.length === 0) {
    return deny('No organization permissions granted')
  }

  const requiredList = Array.isArray(required) ? required : [required]
  const requireAll = options.requireAll ?? true

  if (requireAll) {
    // All required permissions must be present
    const missing = requiredList.filter(p => !orgPermissions.includes(p))
    if (missing.length === 0) return allow()
    return deny(`Missing organization permissions: ${missing.join(', ')}`)
  } else {
    // At least one required permission must be present
    const hasAny = requiredList.some(p => orgPermissions.includes(p))
    if (hasAny) return allow()
    return deny(`None of the required permissions [${requiredList.join(', ')}] are granted`)
  }
}

/**
 * Composite Guard: Check all conditions (AND logic)
 * All guards must pass for access to be allowed.
 * @param guards - Array of guard results to check
 */
export function canAll(...guards: GuardResult[]): GuardResult {
  const denied = guards.filter(g => !g.allowed)
  if (denied.length === 0) return allow()

  const reasons = denied.map(g => g.reason || 'Access denied').join('; ')
  return deny(`All conditions not met: ${reasons}`)
}

/**
 * Composite Guard: Check any condition (OR logic)
 * At least one guard must pass for access to be allowed.
 * @param guards - Array of guard results to check
 */
export function canAny(...guards: GuardResult[]): GuardResult {
  const allowed = guards.filter(g => g.allowed)
  if (allowed.length > 0) return allow()

  const reasons = guards.map(g => g.reason || 'Access denied').join('; ')
  return deny(`No conditions met: ${reasons}`)
}

/**
 * Usage examples:
 *
 * // Single permission check
 * if (!canPermission(user.permissions, 'documents:upload').allowed) {
 *   return <AccessDenied />;
 * }
 *
 * // Organization permission check
 * if (!canOrgPermission(user.org_permissions, 'shipments:create').allowed) {
 *   return <AccessDenied />;
 * }
 *
 * // Composite: User must be admin OR have compliance role
 * const canReview = canAny(
 *   canUserRole(user.role, 'admin'),
 *   canUserRole(user.role, 'compliance')
 * );
 *
 * // Composite: User must have both permissions
 * const canApprove = canAll(
 *   canPermission(user.permissions, 'documents:validate'),
 *   canPermission(user.permissions, 'documents:approve')
 * );
 *
 * // Complex: User must be VIBOTAJ admin OR (Buyer with shipments:approve)
 * const canApproveShipment = canAny(
 *   canAll(
 *     canOrgType(user.org_type, 'vibotaj'),
 *     canOrgRole(user.org_role, 'admin')
 *   ),
 *   canAll(
 *     canOrgType(user.org_type, 'buyer'),
 *     canOrgPermission(user.org_permissions, 'shipments:approve')
 *   )
 * );
 */
