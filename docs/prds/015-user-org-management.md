# PRD-015: User & Organization Management

## Problem Statement

The v2 frontend has navigation routes for `/users`, `/organizations`, and `/settings` but no pages built. Admins cannot manage team members, roles, or organization settings from the v2 interface. The v1 backend has full CRUD endpoints for users, organizations, members, and invitations that are already production-tested.

## Dependencies

- PRD-009 (Design system — DataTable, StatusBadge, ConfirmDialog)
- PRD-010 (Auth pages — PropelAuth hooks, org context)

## Scope

**In scope:**
- `/users` page — list users in current org, search/filter by role, status badges
- User detail panel — view/edit role, activate/deactivate, invite new member
- `/organizations` page — list orgs (admin only), org type/status badges, member counts
- Org detail panel — view org info, member list, invite member
- Member invitation modal — email + role selection, sends via backend
- Role management — change member role inline
- Profile/settings integration — link to PropelAuth hosted account page

**Out of scope:**
- PropelAuth dashboard replacement (PropelAuth manages auth operations)
- SAML/SCIM configuration (managed in PropelAuth dashboard)
- Org creation (admin-only, done via PropelAuth + backend seed)
- Password reset flow (handled by PropelAuth hosted pages)

## Acceptance Criteria

1. `/users` page lists all members of current org with name, email, role badge, status
2. Admin can change a member's role via dropdown
3. Admin can activate/deactivate members
4. Admin can invite new member (email + role)
5. `/organizations` page lists all orgs with type, status, member count
6. Org detail panel shows org info and member list
7. All pages gated by admin role — non-admins see access denied
8. Loading skeletons and error states with retry
9. All components have Vitest tests

## API Integration

Uses existing v1 backend endpoints:

| Endpoint | Hook | Used By |
|----------|------|---------|
| `GET /api/users` | `useOrgMembers` | Users page |
| `GET /api/users/roles` | `useRoles` | Role dropdown |
| `PATCH /api/users/{id}` | `useUpdateUser` | Edit role, activate/deactivate |
| `GET /api/organizations` | `useOrganizations` | Orgs page |
| `GET /api/organizations/{id}` | `useOrganization` | Org detail |
| `GET /api/organizations/{id}/members` | `useOrgDetailMembers` | Org member list |
| `POST /api/organizations/{id}/invitations` | `useInviteMember` | Invite modal |
| `GET /api/organizations/{id}/invitations` | `usePendingInvitations` | Pending invites list |
| `DELETE /api/organizations/{id}/invitations/{id}` | `useRevokeInvitation` | Revoke invite |

## Frontend Changes

### New Files
- `src/lib/api/user-types.ts` — Member, Role, OrgInfo, Invitation types
- `src/lib/api/users.ts` — React Query hooks for user/org/invitation endpoints
- `src/components/users/member-table.tsx` — DataTable with role badges, status, actions
- `src/components/users/role-select.tsx` — Role dropdown with permission gating
- `src/components/users/invite-member-modal.tsx` — Email + role invite form
- `src/components/users/member-detail-panel.tsx` — Sheet with member info + actions
- `src/components/organizations/org-table.tsx` — Orgs DataTable
- `src/components/organizations/org-detail-panel.tsx` — Sheet with org info + members
- `src/app/users/page.tsx` — Users management page
- `src/app/organizations/page.tsx` — Organizations management page

## Database Changes

None — uses existing v1 backend endpoints.

## Compliance Impact

None — user management does not affect shipment compliance.

## Testing

- `user-types.test.ts` — Type helper tests
- `member-table.test.tsx` — Renders members, role badges, action buttons
- `role-select.test.tsx` — Renders roles, permission gating
- `invite-member-modal.test.tsx` — Form validation, submit handler
- `org-table.test.tsx` — Renders orgs, type/status badges
- `alert for non-admin access` — Access denied state test
