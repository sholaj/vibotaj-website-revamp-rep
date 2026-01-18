/**
 * Member Management Panel Component
 *
 * Sprint 13.2: Frontend Member Management UI
 *
 * Panel showing organization members and pending invitations with:
 * - Member list with role management
 * - Pending invitations with resend/revoke actions
 * - Invite member button
 * - Loading states and error handling
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Users,
  UserPlus,
  Mail,
  RefreshCw,
  Clock,
  Shield,
  Trash2,
  Send,
  XCircle,
  Loader2,
  AlertTriangle,
  ChevronDown,
  RotateCcw,
} from 'lucide-react'
import api, { ApiClientError } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import InviteMemberModal from './InviteMemberModal'
import UserDeleteModal from './UserDeleteModal'
import type { OrganizationMember, Invitation, OrgRole, UserDeleteResponse } from '../../types'

interface MemberManagementPanelProps {
  organizationId: string
  organizationName: string
  canManageMembers: boolean // Based on user's org role (admin only)
}

// Role badge styling
const roleBadgeStyles: Record<OrgRole, string> = {
  admin: 'bg-purple-100 text-purple-800',
  manager: 'bg-blue-100 text-blue-800',
  member: 'bg-gray-100 text-gray-800',
  viewer: 'bg-green-100 text-green-800',
}

const roleLabels: Record<OrgRole, string> = {
  admin: 'Admin',
  manager: 'Manager',
  member: 'Member',
  viewer: 'Viewer',
}

// Invitation status badge styling
const invitationStatusStyles: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  accepted: 'bg-green-100 text-green-800',
  expired: 'bg-gray-100 text-gray-500',
  revoked: 'bg-red-100 text-red-800',
}

export default function MemberManagementPanel({
  organizationId,
  organizationName,
  canManageMembers,
}: MemberManagementPanelProps) {
  const { user } = useAuth()

  // State
  const [members, setMembers] = useState<OrganizationMember[]>([])
  const [invitations, setInvitations] = useState<Invitation[]>([])
  const [membersLoading, setMembersLoading] = useState(true)
  const [invitationsLoading, setInvitationsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal state
  const [showInviteModal, setShowInviteModal] = useState(false)

  // Action states
  const [processingMemberId, setProcessingMemberId] = useState<string | null>(null)
  const [processingInvitationId, setProcessingInvitationId] = useState<string | null>(null)

  // Delete modal state
  const [memberToDelete, setMemberToDelete] = useState<OrganizationMember | null>(null)
  const [restoringMemberId, setRestoringMemberId] = useState<string | null>(null)

  // Confirmation dialogs
  const [confirmRevoke, setConfirmRevoke] = useState<Invitation | null>(null)

  // Role change dropdown
  const [roleDropdownOpen, setRoleDropdownOpen] = useState<string | null>(null)

  // Load members
  const loadMembers = useCallback(async () => {
    setMembersLoading(true)
    try {
      const response = await api.getOrganizationMembers(organizationId)
      setMembers(response.items)
    } catch (err) {
      console.error('Failed to load members:', err)
      if (err instanceof ApiClientError) {
        setError(err.message)
      }
    } finally {
      setMembersLoading(false)
    }
  }, [organizationId])

  // Load invitations
  const loadInvitations = useCallback(async () => {
    if (!canManageMembers) {
      setInvitationsLoading(false)
      return
    }

    setInvitationsLoading(true)
    try {
      const response = await api.getInvitations(organizationId, { status: 'pending' })
      setInvitations(response.items)
    } catch (err) {
      console.error('Failed to load invitations:', err)
      // Don't show error for invitations as it might be a permission issue
    } finally {
      setInvitationsLoading(false)
    }
  }, [organizationId, canManageMembers])

  // Initial load
  useEffect(() => {
    loadMembers()
    loadInvitations()
  }, [loadMembers, loadInvitations])

  // Handle role change
  const handleRoleChange = async (member: OrganizationMember, newRole: OrgRole) => {
    setRoleDropdownOpen(null)

    if (newRole === member.org_role) return

    // Prevent changing own role
    if (member.user_id === user?.id) {
      setError("You cannot change your own role")
      return
    }

    setProcessingMemberId(member.user_id)
    try {
      await api.updateMemberRole(organizationId, member.user_id, { org_role: newRole })
      await loadMembers()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to update role')
      }
    } finally {
      setProcessingMemberId(null)
    }
  }

  // Count active admins in the organization
  const countActiveAdmins = useCallback(() => {
    return members.filter(
      (m) => m.org_role === 'admin' && !m.deleted_at
    ).length
  }, [members])

  // Check if a member is the last active admin
  const isLastAdmin = useCallback(
    (member: OrganizationMember) => {
      return member.org_role === 'admin' && countActiveAdmins() <= 1
    },
    [countActiveAdmins]
  )

  // Handle deletion completion
  const handleDeleteCompleted = (response: UserDeleteResponse) => {
    // Show success message
    console.log('User deleted:', response)
    // Reload members list
    loadMembers()
  }

  // Handle user restore
  const handleRestoreUser = async (member: OrganizationMember) => {
    setRestoringMemberId(member.user_id)
    try {
      await api.restoreUser(member.user_id)
      await loadMembers()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to restore user')
      }
    } finally {
      setRestoringMemberId(null)
    }
  }

  // Handle invitation revoke
  const handleRevokeInvitation = async () => {
    if (!confirmRevoke) return

    setProcessingInvitationId(confirmRevoke.id)
    try {
      await api.revokeInvitation(organizationId, confirmRevoke.id)
      setConfirmRevoke(null)
      await loadInvitations()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to revoke invitation')
      }
    } finally {
      setProcessingInvitationId(null)
    }
  }

  // Handle invitation resend
  const handleResendInvitation = async (invitation: Invitation) => {
    setProcessingInvitationId(invitation.id)
    try {
      await api.resendInvitation(organizationId, invitation.id)
      await loadInvitations()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to resend invitation')
      }
    } finally {
      setProcessingInvitationId(null)
    }
  }

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  // Combined loading state (unused for now, keeping for future use)
  // const isLoading = membersLoading && invitationsLoading

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <div className="flex items-start space-x-2 text-danger-600 bg-danger-50 p-3 rounded-lg">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-2 text-xs underline hover:no-underline"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Header with Invite Button */}
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900 flex items-center">
          <Users className="h-5 w-5 mr-2 text-gray-500" />
          Members ({members.length})
        </h4>
        {canManageMembers && (
          <button
            onClick={() => setShowInviteModal(true)}
            className="btn-primary text-sm flex items-center"
          >
            <UserPlus className="h-4 w-4 mr-1" />
            Invite
          </button>
        )}
      </div>

      {/* Members List */}
      <div className="bg-gray-50 rounded-lg divide-y divide-gray-200">
        {membersLoading ? (
          <div className="p-4 text-center text-gray-500">
            <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
            Loading members...
          </div>
        ) : members.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            No members found
          </div>
        ) : (
          members.map((member) => (
            <div
              key={member.id}
              className="p-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className={`font-medium truncate ${member.deleted_at ? 'text-gray-400 line-through' : 'text-gray-900'}`}>
                    {member.full_name}
                  </span>
                  {member.deleted_at && (
                    <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                      Deleted
                    </span>
                  )}
                  {member.is_primary && (
                    <span title="Primary member">
                      <Shield className="h-4 w-4 text-purple-500" />
                    </span>
                  )}
                  {member.user_id === user?.id && (
                    <span className="text-xs text-gray-500">(you)</span>
                  )}
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Mail className="h-3 w-3" />
                  <span className="truncate">{member.email}</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-400 mt-1">
                  <Clock className="h-3 w-3" />
                  <span>Joined {formatDate(member.joined_at)}</span>
                </div>
              </div>

              <div className="flex items-center space-x-2 ml-4">
                {/* Role Badge/Dropdown */}
                {canManageMembers && member.user_id !== user?.id ? (
                  <div className="relative">
                    <button
                      onClick={() =>
                        setRoleDropdownOpen(
                          roleDropdownOpen === member.user_id ? null : member.user_id
                        )
                      }
                      disabled={processingMemberId === member.user_id}
                      className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${
                        roleBadgeStyles[member.org_role]
                      } hover:opacity-80 transition-opacity`}
                    >
                      {processingMemberId === member.user_id ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <>
                          <span>{roleLabels[member.org_role]}</span>
                          <ChevronDown className="h-3 w-3" />
                        </>
                      )}
                    </button>

                    {/* Role Dropdown */}
                    {roleDropdownOpen === member.user_id && (
                      <>
                        <div
                          className="fixed inset-0 z-10"
                          onClick={() => setRoleDropdownOpen(null)}
                        />
                        <div className="absolute right-0 mt-1 w-32 bg-white rounded-lg shadow-lg border border-gray-200 z-20 py-1">
                          {(Object.keys(roleLabels) as OrgRole[]).map((role) => (
                            <button
                              key={role}
                              onClick={() => handleRoleChange(member, role)}
                              className={`w-full px-3 py-1.5 text-left text-sm hover:bg-gray-100 ${
                                member.org_role === role
                                  ? 'font-medium text-primary-600'
                                  : 'text-gray-700'
                              }`}
                            >
                              {roleLabels[role]}
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                ) : (
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      roleBadgeStyles[member.org_role]
                    }`}
                  >
                    {roleLabels[member.org_role]}
                  </span>
                )}

                {/* Delete/Restore buttons */}
                {canManageMembers && member.user_id !== user?.id && !member.is_primary && (
                  <>
                    {member.deleted_at ? (
                      <button
                        onClick={() => handleRestoreUser(member)}
                        disabled={restoringMemberId === member.user_id}
                        className="p-1 text-gray-400 hover:text-green-600 transition-colors disabled:opacity-50"
                        title="Restore user"
                      >
                        {restoringMemberId === member.user_id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <RotateCcw className="h-4 w-4" />
                        )}
                      </button>
                    ) : (
                      <button
                        onClick={() => setMemberToDelete(member)}
                        disabled={processingMemberId === member.user_id}
                        className="p-1 text-gray-400 hover:text-danger-600 transition-colors disabled:opacity-50"
                        title="Delete user"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pending Invitations Section */}
      {canManageMembers && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900 flex items-center">
              <Mail className="h-5 w-5 mr-2 text-gray-500" />
              Pending Invitations ({invitations.length})
            </h4>
            <button
              onClick={loadInvitations}
              disabled={invitationsLoading}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Refresh invitations"
            >
              <RefreshCw
                className={`h-4 w-4 ${invitationsLoading ? 'animate-spin' : ''}`}
              />
            </button>
          </div>

          <div className="bg-gray-50 rounded-lg divide-y divide-gray-200">
            {invitationsLoading ? (
              <div className="p-4 text-center text-gray-500">
                <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
                Loading invitations...
              </div>
            ) : invitations.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No pending invitations
              </div>
            ) : (
              invitations.map((invitation) => (
                <div
                  key={invitation.id}
                  className="p-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-gray-900 truncate">
                        {invitation.email}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          invitationStatusStyles[invitation.status]
                        }`}
                      >
                        {invitation.status}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                      <span className={`${roleBadgeStyles[invitation.org_role]} px-1.5 py-0.5 rounded`}>
                        {roleLabels[invitation.org_role]}
                      </span>
                      <span>Sent {formatDate(invitation.created_at)}</span>
                      <span>Expires {formatDate(invitation.expires_at)}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    {/* Resend button */}
                    <button
                      onClick={() => handleResendInvitation(invitation)}
                      disabled={processingInvitationId === invitation.id}
                      className="p-1 text-gray-400 hover:text-primary-600 transition-colors disabled:opacity-50"
                      title="Resend invitation"
                    >
                      {processingInvitationId === invitation.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </button>

                    {/* Revoke button */}
                    <button
                      onClick={() => setConfirmRevoke(invitation)}
                      disabled={processingInvitationId === invitation.id}
                      className="p-1 text-gray-400 hover:text-danger-600 transition-colors disabled:opacity-50"
                      title="Revoke invitation"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Invite Member Modal */}
      <InviteMemberModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        organizationId={organizationId}
        organizationName={organizationName}
        onInviteSent={() => {
          loadInvitations()
        }}
      />

      {/* User Delete Modal */}
      <UserDeleteModal
        isOpen={memberToDelete !== null}
        onClose={() => setMemberToDelete(null)}
        member={memberToDelete}
        organizationId={organizationId}
        isLastAdmin={memberToDelete ? isLastAdmin(memberToDelete) : false}
        onDeleted={handleDeleteCompleted}
      />

      {/* Revoke Invitation Confirmation Dialog */}
      {confirmRevoke && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div
            className="fixed inset-0 bg-black bg-opacity-50"
            onClick={() => setConfirmRevoke(null)}
          />
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-sm w-full p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Revoke Invitation
              </h3>
              <p className="text-gray-600 mb-4">
                Are you sure you want to revoke the invitation for{' '}
                <span className="font-medium">{confirmRevoke.email}</span>? The
                invitation link will no longer work.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setConfirmRevoke(null)}
                  className="btn-secondary"
                  disabled={processingInvitationId === confirmRevoke.id}
                >
                  Cancel
                </button>
                <button
                  onClick={handleRevokeInvitation}
                  disabled={processingInvitationId === confirmRevoke.id}
                  className="bg-danger-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-danger-700 transition-colors disabled:opacity-50 flex items-center"
                >
                  {processingInvitationId === confirmRevoke.id ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Revoking...
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4 mr-2" />
                      Revoke
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export { MemberManagementPanel }
