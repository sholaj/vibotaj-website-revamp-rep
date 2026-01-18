# PRP-019: Add Delete User Button to User Management

**Status:** Ready for Implementation  
**Priority:** P2 - Medium  
**Sprint:** 17  
**Created:** 2026-01-18  
**Owner:** Shola  

---

## Overview

Add a "Delete" button to the User Management page (`/users`) to allow administrators to delete users. The backend functionality already exists, and a `UserDeleteModal` component is already implemented in the Organizations section—this PRP focuses on wiring it up to the Users page.

### Business Value
- **Complete User Lifecycle:** Admins can properly remove users, not just deactivate them
- **GDPR Compliance:** Support for hard delete when users request data removal
- **Audit Trail:** Soft delete preserves records for compliance while marking users as deleted
- **Consistency:** User deletion available from both Users page and Organization Members

---

## Current State Analysis

### Backend: ✅ COMPLETE

The delete endpoint exists in `backend/app/routers/users.py`:

```
DELETE /api/users/{user_id}?hard=false&reason=string
```

**Features:**
- **Soft Delete:** Marks user as deleted, preserves record (default)
- **Hard Delete:** Permanently removes user, anonymizes audit logs
- **Reason Required:** Audit trail for deletion reason
- **Authorization:** Admin only

**Response Schema:** `UserDeleteResponse`
- `user_id`, `email`, `deleted_at`, `is_hard_delete`, `message`

### Frontend: ⚠️ PARTIAL

| Component | Location | Status |
|-----------|----------|--------|
| `UserDeleteModal` | `components/organizations/` | ✅ Exists |
| `api.deleteUser()` | `api/client.ts` | ✅ Exists |
| Delete button in Users.tsx | `pages/Users.tsx` | ❌ **Missing** |

### Screenshot Analysis

From the attached screenshot of the Users page:
- Shows user list with columns: User, Role, Organization, Status, Last Login, Actions
- Actions column only has "Deactivate" button
- **No Delete button present**

---

## Functional Requirements

### FR-1: Add Delete Button to User Actions
- [ ] Add "Delete" button next to existing "Deactivate" button
- [ ] Button should be red/destructive styling (trash icon)
- [ ] Only visible to users with `USERS_DELETE` permission
- [ ] Hidden for the current logged-in user (cannot delete self)

### FR-2: Integrate UserDeleteModal
- [ ] Import existing `UserDeleteModal` component
- [ ] Pass selected user data to modal
- [ ] Handle deletion success (refresh user list)
- [ ] Handle deletion error (show error message)

### FR-3: Confirmation Flow
- [ ] Require typing user's email to confirm
- [ ] Require deletion reason (minimum 10 characters)
- [ ] Show soft/hard delete toggle (collapsed by default)
- [ ] Warn if deleting last admin

---

## Technical Approach

### Step 1: Add State for Delete Modal

```tsx
// In Users.tsx
const [showDeleteModal, setShowDeleteModal] = useState(false)
const [userToDelete, setUserToDelete] = useState<User | null>(null)
```

### Step 2: Add Delete Button in Actions Column

```tsx
<td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
  {/* Existing Deactivate button */}
  <PermissionGuard permission={Permission.USERS_UPDATE}>
    <button onClick={(e) => handleToggleActive(user, e)} ...>
      {user.is_active ? 'Deactivate' : 'Activate'}
    </button>
  </PermissionGuard>

  {/* NEW: Delete button */}
  <PermissionGuard permission={Permission.USERS_DELETE}>
    {user.id !== currentUser?.id && (
      <button
        onClick={() => handleDeleteClick(user)}
        className="text-sm px-3 py-1 rounded text-red-600 hover:bg-red-50"
        title="Delete user"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    )}
  </PermissionGuard>
</td>
```

### Step 3: Add Handler Functions

```tsx
const handleDeleteClick = (user: User) => {
  setUserToDelete(user)
  setShowDeleteModal(true)
}

const handleDeleteCompleted = (response: UserDeleteResponse) => {
  setShowDeleteModal(false)
  setUserToDelete(null)
  fetchUsers() // Refresh the list
  // Optionally show success toast
}
```

### Step 4: Add Modal Component

```tsx
{/* Delete User Modal */}
<UserDeleteModal
  isOpen={showDeleteModal}
  onClose={() => {
    setShowDeleteModal(false)
    setUserToDelete(null)
  }}
  member={userToDelete ? {
    user_id: userToDelete.id,
    user_email: userToDelete.email,
    user_name: userToDelete.full_name,
    org_role: userToDelete.role,
  } as OrganizationMember : null}
  organizationId={currentUser?.organization_id || ''}
  isLastAdmin={/* check if last admin */}
  onDeleted={handleDeleteCompleted}
/>
```

### Step 5: Check for Last Admin

```tsx
const isLastAdmin = useMemo(() => {
  if (!userToDelete || userToDelete.role !== 'admin') return false
  const adminCount = users.filter(u => u.role === 'admin' && u.is_active).length
  return adminCount <= 1
}, [userToDelete, users])
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/pages/Users.tsx` | Add delete button, modal integration, handlers |

### Dependencies (Already Exist)
- `UserDeleteModal` component
- `api.deleteUser()` API client method
- `Permission.USERS_DELETE` permission constant

---

## Test Requirements

### Manual Testing Checklist

- [ ] Delete button appears for admin users
- [ ] Delete button hidden for non-admin users
- [ ] Delete button hidden for current user (can't delete self)
- [ ] Clicking Delete opens modal
- [ ] Modal shows correct user details
- [ ] Must type email correctly to enable Delete
- [ ] Must enter reason (min 10 chars)
- [ ] Soft delete works, user marked as deleted
- [ ] Hard delete works (if toggled)
- [ ] User list refreshes after deletion
- [ ] Cannot delete last admin (warning shown)

### Unit Tests (Optional)

```tsx
describe('Users Page Delete', () => {
  it('shows delete button for admin users')
  it('hides delete button for current user')
  it('opens delete modal on click')
  it('refreshes list after successful delete')
})
```

---

## Permission Check

**Required Permission:** `USERS_DELETE` (or `USERS_UPDATE` - verify in backend)

From the existing code, `USERS_UPDATE` is used for deactivation. Check if separate `USERS_DELETE` exists or if deletion falls under `USERS_UPDATE`.

---

## Acceptance Criteria

- [ ] Delete button visible in Actions column for each user (except self)
- [ ] Delete button only visible to admins
- [ ] Clicking Delete opens UserDeleteModal
- [ ] Type-to-confirm prevents accidental deletion
- [ ] Reason field required for audit trail
- [ ] Soft delete marks user as deleted (default)
- [ ] Hard delete option available in advanced section
- [ ] User list refreshes after successful deletion
- [ ] Error handling for failed deletions
- [ ] Cannot delete the last admin in the system

---

## Rollout Plan

### Phase 1: Implementation (This Sprint)
1. Add state variables for delete modal
2. Add Delete button in Actions column
3. Import and integrate UserDeleteModal
4. Add handler functions
5. Test locally

### Phase 2: Testing
1. Test on staging environment
2. Verify permissions work correctly
3. Test soft and hard delete flows

### Phase 3: Deployment
1. Deploy to production
2. Announce to admin users

---

## Estimated Effort

| Task | Time |
|------|------|
| Add delete button and state | 15 min |
| Integrate UserDeleteModal | 15 min |
| Add handlers and last-admin check | 15 min |
| Testing | 30 min |
| **Total** | **~1.5 hours** |

---

## Notes

- The `UserDeleteModal` component was built for the Organization Members panel but is generic enough to reuse
- May need to adapt the `OrganizationMember` type to work with `User` type from Users page
- Consider adding a "Deleted Users" tab to view soft-deleted users (future enhancement)

---

**Last Updated:** 2026-01-18  
**Status:** Ready for Implementation
