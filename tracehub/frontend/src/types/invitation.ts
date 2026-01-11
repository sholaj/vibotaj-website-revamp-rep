/**
 * Invitation Types for TraceHub Frontend
 *
 * Sprint 13.2: Frontend Member Management UI
 *
 * These types align with backend invitation schemas in
 * tracehub/backend/app/schemas/invitation.py
 */

import type { OrgRole, OrganizationType } from './organization'

/**
 * Invitation status enum matching backend InvitationStatus
 */
export type InvitationStatus = 'pending' | 'accepted' | 'expired' | 'revoked'

/**
 * Invitation object returned by the API
 */
export interface Invitation {
  id: string
  organization_id: string
  organization_name?: string
  email: string
  org_role: OrgRole
  status: InvitationStatus
  created_at: string
  expires_at: string
  created_by?: string
  created_by_name?: string
  accepted_at?: string
}

/**
 * Request body for creating a new invitation
 */
export interface InvitationCreateRequest {
  email: string
  org_role: OrgRole
  message?: string
}

/**
 * Response when creating an invitation (includes URL)
 */
export interface InvitationCreateResponse {
  id: string
  organization_id: string
  organization_name: string
  email: string
  org_role: OrgRole
  status: InvitationStatus
  created_at: string
  expires_at: string
  invitation_url: string
}

/**
 * Paginated list of invitations
 */
export interface InvitationListResponse {
  items: Invitation[]
  total: number
  limit: number
  offset: number
}

/**
 * Response when resending an invitation
 */
export interface ResendInvitationResponse {
  id: string
  email: string
  org_role: OrgRole
  status: InvitationStatus
  expires_at: string
  message: string
  invitation_url: string
}

/**
 * Public invitation acceptance info (for accept page)
 */
export interface InvitationAcceptInfo {
  organization_name: string
  organization_type: OrganizationType
  email: string
  org_role: OrgRole
  expires_at: string
  invited_by_name?: string
  custom_message?: string
  requires_registration: boolean
}

/**
 * Request body for accepting an invitation
 */
export interface AcceptInvitationRequest {
  full_name?: string
  password?: string
}

/**
 * Response after accepting an invitation
 */
export interface AcceptedInvitationResponse {
  success: boolean
  message: string
  user_id: string
  organization_id: string
  organization_name: string
  org_role: OrgRole
  is_new_user: boolean
  access_token?: string
  token_type: string
}
