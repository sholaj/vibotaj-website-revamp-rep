# Sprint 13: Organization Member Management

**Sprint:** Sprint 13 - Organization Member Management
**Version:** 1.4.0
**Date:** 2026-01-11
**Status:** IN PROGRESS

---

## Executive Summary

Sprint 13 implements complete organization member management, enabling:
- Inviting new users to organizations via email
- Managing existing member roles and access
- Self-service invitation acceptance
- Organization-level admin permissions

This addresses the gap identified where organizations could be created but members couldn't be added or managed through the UI.

---

## Sprint Goals

1. **Enable invitation workflow** - Org admins can invite users by email
2. **Complete member management** - Add, update roles, remove members via UI
3. **Self-service signup** - Invited users can accept and create accounts
4. **Decentralize admin** - Org admins manage their own orgs (not just system admins)

---

## Sprint Breakdown

### 13.1 Backend Invitation Endpoints

**Estimated Effort:** 2-3 hours

#### Tasks:

| Task | Description | Deliverable |
|------|-------------|-------------|
| 13.1.1 | Create invitation service | `services/invitation.py` with business logic |
| 13.1.2 | Add invitation CRUD endpoints | POST, GET, DELETE for invitations |
| 13.1.3 | Add public acceptance endpoint | POST `/invitations/{token}/accept` |
| 13.1.4 | Add invitation email service | Email template and sending logic |
| 13.1.5 | Add invitation tests | `tests/test_invitations.py` |

#### Endpoints to Implement:

```
POST   /api/organizations/{org_id}/invitations
       - Create invitation, generate token, (optionally) send email
       - Input: { email, org_role, message? }
       - Returns: invitation details (without token)

GET    /api/organizations/{org_id}/invitations
       - List invitations for organization
       - Filter by status (pending, accepted, expired, revoked)
       - Paginated response

DELETE /api/organizations/{org_id}/invitations/{invitation_id}
       - Revoke/delete invitation
       - Only pending invitations can be revoked

POST   /api/organizations/{org_id}/invitations/{invitation_id}/resend
       - Resend invitation email (resets expiration)

GET    /api/invitations/accept/{token}
       - Public endpoint to get invitation details by token
       - Returns: org name, invited email, role (not sensitive data)

POST   /api/invitations/accept/{token}
       - Accept invitation
       - If user exists: add to org membership
       - If new user: create account + add membership
       - Input: { full_name?, password? } (for new users)
```

#### Expected Outcomes:
- [ ] Invitation CRUD working via API
- [ ] Token-based acceptance flow
- [ ] Email notifications sent (or logged if no SMTP)
- [ ] 90%+ test coverage on invitation endpoints

---

### 13.2 Frontend Member Management UI

**Estimated Effort:** 3-4 hours

#### Tasks:

| Task | Description | Deliverable |
|------|-------------|-------------|
| 13.2.1 | Add API client methods | `api/client.ts` invitation methods |
| 13.2.2 | Create InviteMemberModal | Modal for email + role input |
| 13.2.3 | Create MemberManagementPanel | Full member list with actions |
| 13.2.4 | Add role update functionality | Dropdown to change member roles |
| 13.2.5 | Add remove member functionality | Confirmation + removal |
| 13.2.6 | Add pending invitations display | List with resend/revoke buttons |

#### UI Components:

```
Organizations.tsx (enhanced)
├── OrganizationDetailPanel
│   ├── MemberManagementPanel (NEW)
│   │   ├── MemberList
│   │   │   ├── MemberRow (role dropdown, remove button)
│   │   │   └── EmptyState
│   │   ├── PendingInvitationsList (NEW)
│   │   │   ├── InvitationRow (resend, revoke buttons)
│   │   │   └── EmptyState
│   │   └── InviteMemberButton
│   └── InviteMemberModal (NEW)
│       ├── EmailInput
│       ├── RoleSelect
│       ├── MessageInput (optional)
│       └── SendButton
```

#### Expected Outcomes:
- [ ] "Invite Member" button in org detail panel
- [ ] Modal with email input and role selection
- [ ] Pending invitations listed with resend/revoke actions
- [ ] Existing members show role dropdown and remove button
- [ ] All actions show loading states and error handling

---

### 13.3 Invitation Acceptance Workflow

**Estimated Effort:** 2-3 hours

#### Tasks:

| Task | Description | Deliverable |
|------|-------------|-------------|
| 13.3.1 | Create AcceptInvitation page | Public page at `/accept-invitation/:token` |
| 13.3.2 | Handle existing user flow | Login prompt → auto-accept |
| 13.3.3 | Handle new user flow | Account creation form |
| 13.3.4 | Add success/error states | Clear feedback messages |
| 13.3.5 | Add route and navigation | React Router setup |

#### Acceptance Flows:

**Flow A: New User**
```
1. User clicks invitation link
2. Page shows: "You've been invited to join [Org Name]"
3. User fills: Name, Password, Confirm Password
4. User clicks "Accept & Create Account"
5. Account created, membership active, redirected to dashboard
```

**Flow B: Existing User (Not Logged In)**
```
1. User clicks invitation link
2. Page shows: "You've been invited to join [Org Name]"
3. System detects email matches existing account
4. User clicks "Log in to accept"
5. After login, membership automatically created
6. Redirected to dashboard
```

**Flow C: Existing User (Logged In)**
```
1. User clicks invitation link (already logged in)
2. If email matches: Membership created, redirect to dashboard
3. If email mismatch: "This invitation is for a different email"
```

#### Expected Outcomes:
- [ ] Public acceptance page working at `/accept-invitation/:token`
- [ ] New user can create account and join org in one flow
- [ ] Existing user can accept via login
- [ ] Clear error states for expired/invalid/revoked invitations

---

### 13.4 Role-Based Organization Permissions

**Estimated Effort:** 1-2 hours

#### Tasks:

| Task | Description | Deliverable |
|------|-------------|-------------|
| 13.4.1 | Update permission checks | Org admin can manage their org's members |
| 13.4.2 | Add org-level permission helpers | `can_manage_org_members(user, org_id)` |
| 13.4.3 | Update frontend authorization | Show/hide based on org role |
| 13.4.4 | Add permission tests | Test org admin vs system admin access |

#### Permission Matrix:

| Action | System Admin | Org Admin | Org Manager | Org Member | Org Viewer |
|--------|-------------|-----------|-------------|------------|------------|
| View org members | ✅ | ✅ | ✅ | ✅ | ✅ |
| Invite new members | ✅ | ✅ | ❌ | ❌ | ❌ |
| Update member roles | ✅ | ✅* | ❌ | ❌ | ❌ |
| Remove members | ✅ | ✅* | ❌ | ❌ | ❌ |
| Revoke invitations | ✅ | ✅ | ❌ | ❌ | ❌ |

*Org Admin cannot modify other admins or themselves

#### Expected Outcomes:
- [ ] Org admins can manage their own org's members
- [ ] System admins can manage all orgs
- [ ] Role hierarchy enforced (admin > manager > member > viewer)
- [ ] Frontend hides actions user cannot perform

---

## Implementation Order

1. **Sprint 13.1** - Backend first (endpoints are blocking)
2. **Sprint 13.4** - Permissions (affects backend behavior)
3. **Sprint 13.2** - Frontend member management
4. **Sprint 13.3** - Acceptance workflow (uses all above)

---

## Database Changes

**No schema changes required** - The Invitation model already exists from Sprint 8.

Existing schema supports:
- `invitations.token_hash` - Secure token storage
- `invitations.status` - PENDING, ACCEPTED, EXPIRED, REVOKED
- `invitations.organization_id` - Target organization
- `invitations.invited_email` - Recipient email
- `invitations.org_role` - Role to assign on acceptance
- `invitations.expires_at` - Expiration timestamp
- `invitations.created_by` - Inviting user
- `invitations.accepted_by` - Accepting user (after acceptance)

---

## API Changes Summary

### New Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/organizations/{id}/invitations` | Org Admin+ | Create invitation |
| GET | `/api/organizations/{id}/invitations` | Org Admin+ | List invitations |
| DELETE | `/api/organizations/{id}/invitations/{inv_id}` | Org Admin+ | Revoke invitation |
| POST | `/api/organizations/{id}/invitations/{inv_id}/resend` | Org Admin+ | Resend email |
| GET | `/api/invitations/accept/{token}` | Public | Get invitation info |
| POST | `/api/invitations/accept/{token}` | Public | Accept invitation |

### Modified Endpoints

| Method | Path | Change |
|--------|------|--------|
| GET | `/api/organizations/{id}/members` | Allow Org Admin (not just System Admin) |
| POST | `/api/organizations/{id}/members` | Allow Org Admin (not just System Admin) |
| PATCH | `/api/organizations/{id}/members/{uid}` | Allow Org Admin (not just System Admin) |
| DELETE | `/api/organizations/{id}/members/{uid}` | Allow Org Admin (not just System Admin) |

---

## Frontend Changes Summary

### New Components

| Component | Location | Description |
|-----------|----------|-------------|
| `InviteMemberModal` | `components/organizations/` | Email + role invite form |
| `MemberManagementPanel` | `components/organizations/` | Full member list with actions |
| `PendingInvitationsList` | `components/organizations/` | Invitation status display |
| `AcceptInvitationPage` | `pages/` | Public acceptance page |

### Modified Components

| Component | Change |
|-----------|--------|
| `Organizations.tsx` | Add member management to detail panel |
| `api/client.ts` | Add invitation API methods |
| `App.tsx` | Add `/accept-invitation/:token` route |

---

## Testing Plan

### Unit Tests
- [ ] `test_invitations.py` - All invitation endpoints
- [ ] `test_org_permissions.py` - Permission matrix verification

### Integration Tests
- [ ] Create invitation → Accept → Verify membership
- [ ] Expired invitation rejection
- [ ] Role hierarchy enforcement

### Manual Tests
- [ ] Invite new user → email received → create account → dashboard access
- [ ] Invite existing user → login → org appears in dropdown
- [ ] Org admin can manage members but not other admins
- [ ] Error states (expired, revoked, invalid token)

---

## Success Criteria

1. **Functional**
   - [ ] Org admin can invite users by email
   - [ ] Invited users can accept and join
   - [ ] Member roles can be changed
   - [ ] Members can be removed
   - [ ] Invitations can be resent/revoked

2. **Security**
   - [ ] Tokens are hashed (not stored plaintext)
   - [ ] Invitations expire after 7 days
   - [ ] Only org admins+ can manage members
   - [ ] Role hierarchy prevents privilege escalation

3. **UX**
   - [ ] Clear success/error feedback
   - [ ] Loading states on all actions
   - [ ] Confirmation dialogs for destructive actions
   - [ ] Mobile-responsive UI

---

## Rollback Plan

If issues arise:
1. Revert merge commit on main
2. No database migration needed (schema unchanged)
3. Redeploy previous version

---

## Timeline

| Phase | Tasks | Status |
|-------|-------|--------|
| Planning | Sprint 13 plan | ✅ Complete |
| Implementation | 13.1 Backend | ⏳ Next |
| Implementation | 13.4 Permissions | ⏳ Pending |
| Implementation | 13.2 Frontend UI | ⏳ Pending |
| Implementation | 13.3 Acceptance | ⏳ Pending |
| Testing | All tests pass | ⏳ Pending |
| Deployment | Staging → Production | ⏳ Pending |

---

**Document Version:** 1.0
**Last Updated:** 2026-01-11
**Author:** Claude Opus 4.5
