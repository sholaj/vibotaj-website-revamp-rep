# PRD-010: Auth Pages — PropelAuth UI + Org Switcher

**Status:** Specified
**Complexity:** Medium
**Target:** Week 5
**Dependencies:** PRD-003 (PropelAuth integration), PRD-009 (design system)
**Branch:** `feature/prd-010-auth-pages`

---

## Problem

PRD-003 set up PropelAuth infrastructure (middleware, provider, hooks, API callbacks) but the app has no auth-aware UI. There's no user menu, no org switcher for multi-org users, no post-login redirect, and no account settings page. The sidebar shows a static nav with no indication of who's logged in or which organization they're working in. Users who belong to multiple organizations (e.g., VIBOTAJ admin + HAGES buyer) have no way to switch context.

## Acceptance Criteria

### User Menu (Header)
1. User dropdown menu in the header replaces the placeholder User icon button
2. Dropdown shows: user name, email, current role badge (using StatusBadge from PRD-009)
3. Menu items: "Account Settings" (links to PropelAuth hosted account page), "Logout"
4. Logout calls PropelAuth's logout function and redirects to login

### Org Switcher (Sidebar)
5. Org switcher dropdown at the top of the sidebar (below the TraceHub logo)
6. Shows current organization name + logo (or initials fallback)
7. Lists all organizations the user belongs to (via PropelAuth's user.getOrgs())
8. Switching org updates: sidebar nav (role-based filtering per org role), all data queries (org context), URL (no change — org is session state, not URL)
9. Current org stored in React context, accessible via `useCurrentOrg()` hook
10. Default org on login: first org in the list (or last-used org from localStorage)

### Auth-Aware Layout
11. Layout passes user's role in current org to AppSidebar for role-based nav filtering
12. If user has no orgs (edge case — invited but org deleted), show an empty state with "Contact your administrator"
13. Loading state while auth is initializing (skeleton sidebar + header)

### Post-Login Redirect
14. After PropelAuth login callback, redirect to `/dashboard` (or the originally requested URL)
15. If user was visiting `/shipments/123` before auth redirect, return them there after login

### Account Settings
16. `/settings/account` page with link to PropelAuth hosted account page (password change, MFA, etc.)
17. Display current user info: name, email, role, org memberships
18. No custom password/MFA forms — delegate to PropelAuth hosted pages

### Testing
19. User menu tests: renders user info, logout calls PropelAuth, role badge shows correct role
20. Org switcher tests: lists orgs, switching org updates context, default org selection
21. Auth context tests: provides current user + org, handles loading/error states
22. Layout integration: sidebar receives correct role from auth context

## API Changes

None — all auth data comes from PropelAuth client SDK.

## Database Changes

None.

## Frontend Changes

### New Files
```
v2/frontend/src/
  lib/auth/
    org-context.tsx              # OrgProvider + useCurrentOrg() hook
    types.ts                     # TraceHub auth types (CurrentOrg, UserRole)
  components/layout/
    user-menu.tsx                # User dropdown in header
    org-switcher.tsx             # Org switcher in sidebar
    auth-loading.tsx             # Full-page loading skeleton during auth init
  app/
    (dashboard)/                 # Route group for authenticated pages
      layout.tsx                 # Auth-aware layout (wraps sidebar + header)
    settings/
      account/
        page.tsx                 # Account settings page
  lib/auth/__tests__/
    org-context.test.tsx
  components/layout/__tests__/
    user-menu.test.tsx
    org-switcher.test.tsx
```

### Modified Files
```
v2/frontend/src/
  components/layout/header.tsx   # Replace User icon with UserMenu
  components/layout/app-sidebar.tsx  # Add OrgSwitcher, wire role from auth context
  app/layout.tsx                 # Add OrgProvider wrapper
```

## Compliance Impact

None — auth pages have no compliance logic.

## Org Switcher Design

```
┌──────────────────────────┐
│ ⬡ VIBOTAJ Global    ▾   │  ← current org + dropdown trigger
├──────────────────────────┤
│ ✓ VIBOTAJ Global         │  ← active org (checkmark)
│   HAGES GmbH             │  ← other org
│   Witatrade BV            │  ← other org
└──────────────────────────┘
```

- Uses Shadcn `DropdownMenu` inside `SidebarHeader`
- Org logo/avatar: Shadcn `Avatar` with initials fallback
- Active org shows checkmark icon

## User Menu Design

```
┌─────────────────────────┐
│ 👤 Shola Adebowale      │
│ shola@vibotaj.com        │
│ [Admin] badge            │
├─────────────────────────┤
│ ⚙ Account Settings      │
│ 🚪 Log out              │
└─────────────────────────┘
```

- Uses Shadcn `DropdownMenu` with `Avatar` trigger
- Role badge uses StatusBadge variant="role"

## Auth Context Flow

```
PropelAuth Provider (PRD-003)
  └── OrgProvider (PRD-010)
       ├── useCurrentOrg() → { org, orgId, role, switchOrg }
       └── Sidebar + Header consume org context
```

```typescript
interface CurrentOrgContext {
  org: OrgMemberInfo | null;
  orgId: string | null;
  role: UserRole;
  orgs: OrgMemberInfo[];
  switchOrg: (orgId: string) => void;
  isLoading: boolean;
}
```

## Testing Strategy

- **User menu:** Mock PropelAuth useUser() → render menu → verify name/email/role → click logout → verify logout called
- **Org switcher:** Mock user with 3 orgs → render → verify all orgs listed → click org B → verify switchOrg called with org B id
- **Org context:** Provider with mock user → useCurrentOrg() returns correct org/role → switchOrg updates context → localStorage stores last org
- **Auth loading:** Render with loading=true → verify skeleton shown → loading=false → verify content shown
- **No-org edge case:** User with empty orgs array → verify "Contact administrator" message

## Out of Scope

- Custom login/signup forms (PropelAuth hosted pages handle this)
- Invitation accept flow (deferred — PRD-003 handles via PropelAuth)
- Organization creation/management UI (that's PRD-015)
- SAML/SSO configuration (Phase 4)
