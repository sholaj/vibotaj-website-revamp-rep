# TraceHub Frontend Component Hierarchy

**Version:** 1.0
**Date:** 2026-01-03

This document provides a visual hierarchy and dependency map for all TraceHub React components, including existing and planned components.

---

## Component Tree

```
App (Root)
├── AuthProvider (Context)
│   └── AppRoutes
│       ├── Login (Page)
│       │   └── LoginForm
│       │
│       └── Layout (Protected)
│           ├── Header
│           │   ├── Logo
│           │   ├── Navigation
│           │   │   ├── NavItem (Dashboard, Analytics, Users)
│           │   │   └── MobileMenu [NEW]
│           │   ├── NotificationBell
│           │   │   └── NotificationDropdown
│           │   │       └── NotificationItem
│           │   ├── TenantSwitcher [FUTURE]
│           │   └── UserMenu
│           │       └── RoleBadge
│           │
│           ├── Main Content (Outlet)
│           │   │
│           │   ├── Dashboard (Page)
│           │   │   ├── DashboardHeader
│           │   │   ├── ShipmentCard (list)
│           │   │   ├── LoadingSkeleton
│           │   │   ├── ErrorDisplay
│           │   │   └── EmptyState
│           │   │
│           │   ├── Shipment (Page)
│           │   │   ├── ShipmentHeader
│           │   │   │   ├── BackButton
│           │   │   │   ├── StatusBadge
│           │   │   │   └── ActionButtons
│           │   │   │       ├── RefreshTrackingButton
│           │   │   │       └── AuditPackDownloadButton [ENHANCED]
│           │   │   │           └── AuditPackPreviewModal [NEW]
│           │   │   │
│           │   │   ├── AISummaryCard [NEW]
│           │   │   │   ├── SummaryStatusBadge
│           │   │   │   ├── RecommendedActions
│           │   │   │   └── DiscrepancyAlert
│           │   │   │
│           │   │   ├── MainContent (2-column)
│           │   │   │   ├── ShipmentInfoCard
│           │   │   │   │   ├── VesselInfo
│           │   │   │   │   ├── RouteInfo
│           │   │   │   │   ├── PartiesInfo
│           │   │   │   │   └── CargoInfo
│           │   │   │   │
│           │   │   │   ├── ContainerTrackingPanel [NEW]
│           │   │   │   │   ├── TrackingMap [NEW]
│           │   │   │   │   ├── TrackingStatusCard [NEW]
│           │   │   │   │   │   └── ETACountdown [NEW]
│           │   │   │   │   └── EventTimeline [ENHANCED]
│           │   │   │   │
│           │   │   │   └── TabsPanel
│           │   │   │       ├── TabButton (Documents, Tracking)
│           │   │   │       └── TabContent
│           │   │   │           ├── DocumentList
│           │   │   │           │   ├── DocumentCard
│           │   │   │           │   └── MissingDocumentCard
│           │   │   │           └── TrackingTimeline
│           │   │   │               └── EventCard
│           │   │   │
│           │   │   └── Sidebar
│           │   │       ├── EUDRStatusCard
│           │   │       │   ├── StatusHeader
│           │   │       │   ├── ComplianceChecklist
│           │   │       │   └── ActionButtons
│           │   │       ├── DocumentStatusCard
│           │   │       │   └── ComplianceStatus
│           │   │       ├── LiveTrackingCard
│           │   │       └── QuickActionsCard
│           │   │           ├── UploadDocumentButton
│           │   │           ├── SyncTrackingButton
│           │   │           └── DownloadAuditPackButton
│           │   │
│           │   ├── Analytics (Page)
│           │   │   ├── DashboardStats
│           │   │   │   └── StatCard
│           │   │   ├── ShipmentTrendsChart
│           │   │   ├── DocumentDistributionChart
│           │   │   ├── ComplianceMetricsCard
│           │   │   └── RecentActivityList
│           │   │       └── ActivityItem
│           │   │
│           │   ├── Users (Page)
│           │   │   ├── UserListTable
│           │   │   │   ├── UserRow
│           │   │   │   └── RoleBadge
│           │   │   ├── CreateUserModal
│           │   │   │   └── UserForm
│           │   │   └── UserActionsMenu
│           │   │
│           │   └── Settings (Page) [NEW]
│           │       ├── SettingsNavigation
│           │       ├── NotificationSettings [NEW]
│           │       │   ├── NotificationGroup
│           │       │   │   └── NotificationTypeToggle
│           │       │   └── FrequencySelector
│           │       └── TenantSettings [FUTURE]
│           │           ├── CompanyInfoForm
│           │           ├── BrandingSettings
│           │           │   └── BrandingPreview
│           │           └── FeatureToggle
│           │
│           └── Footer
│
├── Modals (Portal-rendered)
│   ├── DocumentUploadModal
│   │   ├── FileDropzone
│   │   ├── DocumentTypeSelector
│   │   └── MetadataForm
│   ├── DocumentReviewPanel (Slide-over)
│   │   ├── DocumentPreview
│   │   ├── ValidationForm
│   │   └── ActionButtons
│   ├── AuditPackPreviewModal [NEW]
│   │   ├── ContentTree
│   │   ├── MissingItemsAlert
│   │   └── DownloadButton
│   ├── DownloadProgressModal [NEW]
│   │   ├── ProgressBar
│   │   └── StatusMessage
│   ├── BottomSheet [NEW - Mobile]
│   │   └── DraggableHandle
│   └── TenantInviteModal [FUTURE]
│       └── InviteForm
│
├── Toasts (Portal-rendered)
│   ├── SuccessToast
│   ├── ErrorToast
│   ├── WarningToast
│   └── DownloadSuccessToast [NEW]
│
└── Context Providers
    ├── AuthContext
    ├── TenantContext [FUTURE]
    └── ThemeContext [FUTURE]
```

---

## Component Categories

### Pages (Routes)
Components that represent full pages and handle routing.

| Component | Route | Auth Required | Permission |
|-----------|-------|---------------|------------|
| Login | `/login` | No | Public |
| Dashboard | `/dashboard` | Yes | All roles |
| Shipment | `/shipment/:id` | Yes | All roles |
| Analytics | `/analytics` | Yes | All roles |
| Users | `/users` | Yes | `can_manage_users` |
| NotificationSettings | `/settings/notifications` | Yes | All roles |
| TenantSettings | `/admin/tenant` | Yes | `tenant_admin` |

### Layout Components
Structural components that define page layout.

| Component | Purpose | Responsive |
|-----------|---------|------------|
| Layout | Main app shell with header/footer | Yes |
| Header | Navigation and user menu | Yes - hamburger on mobile |
| Footer | App info and user context | Yes - simplified on mobile |
| MobileMenu | Slide-out navigation | Mobile only |
| Sidebar | Right sidebar for detail pages | Stacks on mobile |

### Feature Components
Business logic and domain-specific components.

#### Shipment Features
| Component | Purpose | State Management |
|-----------|---------|------------------|
| ShipmentCard | List view of shipment | Props |
| ShipmentInfoCard | Detailed shipment metadata | Props |
| ContainerTrackingPanel | Live tracking display | Local state + API |
| TrackingMap | Visual route map | Props |
| TrackingStatusCard | Current status display | Props |
| ETACountdown | Live countdown timer | Local state (interval) |
| EventTimeline | Chronological events | Props |

#### Document Features
| Component | Purpose | State Management |
|-----------|---------|------------------|
| DocumentList | Grid/list of documents | Props |
| DocumentCard | Individual document display | Props |
| DocumentUploadModal | Upload flow | Local state + API |
| DocumentReviewPanel | Validation panel | Local state + API |
| ComplianceStatus | Compliance indicators | Props |

#### EUDR Features
| Component | Purpose | State Management |
|-----------|---------|------------------|
| EUDRStatusCard | Compliance status | Local state + API |
| ComplianceChecklist | Checklist items | Props |
| OriginVerificationForm | Origin data input | Local state |

#### AI Features
| Component | Purpose | State Management |
|-----------|---------|------------------|
| AISummaryCard | AI-generated summary | Local state + API |
| SummaryStatusBadge | Visual status indicator | Props |
| RecommendedActions | Action list | Props |
| DiscrepancyAlert | Issue highlight | Props |

#### Notification Features
| Component | Purpose | State Management |
|-----------|---------|------------------|
| NotificationBell | Bell icon with badge | Local state + polling |
| NotificationDropdown | Notification list | Local state + API |
| NotificationItem | Single notification | Props |
| NotificationSettings | Preferences form | Local state + API |
| NotificationTypeToggle | Individual toggle | Props + callback |

#### Analytics Features
| Component | Purpose | State Management |
|-----------|---------|------------------|
| DashboardStats | Overview metrics | Props |
| StatCard | Individual metric | Props |
| ShipmentTrendsChart | Time series chart | Props (recharts) |
| DocumentDistributionChart | Pie/bar chart | Props (recharts) |
| RecentActivityList | Activity log | Props |

#### Multi-tenant Features (Future)
| Component | Purpose | State Management |
|-----------|---------|------------------|
| TenantSwitcher | Organization switcher | Context + API |
| TenantSettings | Admin settings | Local state + API |
| BrandingPreview | Live theme preview | Props |
| FeatureToggle | Feature enable/disable | Props + callback |

### UI Components (Reusable)
Generic, reusable UI elements.

| Component | Purpose | Props |
|-----------|---------|-------|
| Button | Primary/secondary buttons | `variant`, `size`, `disabled`, `loading` |
| Badge | Status badges | `variant`, `text` |
| Card | Container with shadow | `children`, `padding` |
| Modal | Centered modal dialog | `isOpen`, `onClose`, `title`, `children` |
| BottomSheet | Mobile modal from bottom | `isOpen`, `onClose`, `children` |
| LoadingSkeleton | Loading placeholder | `rows`, `columns` |
| EmptyState | No data placeholder | `icon`, `title`, `message`, `action` |
| ErrorDisplay | Error message | `message`, `onRetry` |
| ProgressBar | Linear progress | `progress`, `indeterminate` |
| Dropdown | Generic dropdown | `items`, `onSelect` |
| Checkbox | Checkbox input | `checked`, `onChange`, `label` |
| Toggle | Switch toggle | `enabled`, `onChange`, `label` |
| DatePicker | Date input | `value`, `onChange` |
| FileDropzone | File upload area | `onDrop`, `accept`, `maxSize` |

---

## State Management Strategy

### Component State Hierarchy

```
┌──────────────────────────────────────────────────────┐
│  App-level Context (Global)                          │
│  - AuthContext (user, permissions, login/logout)     │
│  - TenantContext (current tenant, theme) [FUTURE]    │
└──────────────────────────────────────────────────────┘
                       │
                       ├── Flows to all components
                       │
┌──────────────────────────────────────────────────────┐
│  Page-level State (Local + API)                      │
│  - Shipment page: shipment data, documents, events   │
│  - Dashboard: shipments list                         │
│  - Analytics: metrics and charts                     │
└──────────────────────────────────────────────────────┘
                       │
                       ├── Props flow down
                       │
┌──────────────────────────────────────────────────────┐
│  Component-level State (Local)                       │
│  - Modal open/close                                  │
│  - Form input values                                 │
│  - Countdown timers                                  │
│  - Loading/error states                              │
└──────────────────────────────────────────────────────┘
```

### Data Fetching Patterns

**Pattern 1: Fetch on Mount**
```typescript
// Used in: Dashboard, Shipment, Analytics pages
useEffect(() => {
  fetchData()
}, [])
```

**Pattern 2: Polling**
```typescript
// Used in: NotificationBell, ETACountdown
useEffect(() => {
  const interval = setInterval(fetchData, POLL_INTERVAL)
  return () => clearInterval(interval)
}, [])
```

**Pattern 3: Manual Refresh**
```typescript
// Used in: Tracking refresh, AI summary regeneration
const handleRefresh = async () => {
  setIsRefreshing(true)
  await fetchData()
  setIsRefreshing(false)
}
```

**Pattern 4: Optimistic Updates**
```typescript
// Used in: Notification mark read, toggle settings
const handleToggle = async (id: string) => {
  // Update UI immediately
  setItems(prev => prev.map(item =>
    item.id === id ? { ...item, enabled: !item.enabled } : item
  ))

  // Sync with backend
  try {
    await api.updateItem(id)
  } catch (error) {
    // Revert on failure
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, enabled: !item.enabled } : item
    ))
  }
}
```

---

## Component Dependencies

### External Libraries

| Component | Library | Purpose |
|-----------|---------|---------|
| TrackingMap | `recharts` (MVP) / `leaflet` (future) | Map visualization |
| EventTimeline | `lucide-react` | Icons |
| ShipmentTrendsChart | `recharts` | Charts |
| ETACountdown | `date-fns` | Date calculations |
| DocumentUploadModal | Native HTML5 | File upload |
| BrandingPreview | CSS variables | Dynamic theming |

### Internal Dependencies

| Component | Depends On | Type |
|-----------|------------|------|
| Shipment (page) | AISummaryCard, ContainerTrackingPanel, EUDRStatusCard | Child components |
| ContainerTrackingPanel | TrackingMap, EventTimeline, ETACountdown | Child components |
| NotificationBell | AuthContext | Context |
| TenantSwitcher | TenantContext | Context |
| All components | api client | Service |

---

## File Structure

```
src/
├── api/
│   └── client.ts              # API client singleton
│
├── components/
│   ├── Layout.tsx
│   ├── NotificationBell.tsx
│   ├── EUDRStatusCard.tsx
│   ├── DocumentList.tsx
│   ├── DocumentReviewPanel.tsx
│   ├── DocumentUploadModal.tsx
│   ├── TrackingTimeline.tsx
│   ├── ComplianceStatus.tsx
│   │
│   ├── tracking/              # [NEW] Tracking feature
│   │   ├── ContainerTrackingPanel.tsx
│   │   ├── TrackingMap.tsx
│   │   ├── TrackingStatusCard.tsx
│   │   ├── ETACountdown.tsx
│   │   └── EventTimeline.tsx
│   │
│   ├── ai/                    # [NEW] AI features
│   │   ├── AISummaryCard.tsx
│   │   ├── SummaryStatusBadge.tsx
│   │   ├── RecommendedActions.tsx
│   │   └── DiscrepancyAlert.tsx
│   │
│   ├── download/              # [NEW] Download features
│   │   ├── AuditPackPreviewModal.tsx
│   │   ├── AuditPackDownloadButton.tsx
│   │   ├── DownloadProgressModal.tsx
│   │   └── DownloadSuccessToast.tsx
│   │
│   ├── mobile/                # [NEW] Mobile-specific
│   │   ├── MobileMenu.tsx
│   │   ├── MobileHeader.tsx
│   │   ├── BottomSheet.tsx
│   │   └── CollapsibleSection.tsx
│   │
│   ├── settings/              # [NEW] Settings
│   │   ├── NotificationSettings.tsx
│   │   ├── NotificationTypeToggle.tsx
│   │   ├── NotificationGroup.tsx
│   │   └── FrequencySelector.tsx
│   │
│   ├── tenant/                # [FUTURE] Multi-tenant
│   │   ├── TenantSwitcher.tsx
│   │   ├── TenantSettings.tsx
│   │   ├── BrandingPreview.tsx
│   │   └── FeatureToggle.tsx
│   │
│   └── ui/                    # Reusable UI components
│       ├── Button.tsx
│       ├── Badge.tsx
│       ├── Card.tsx
│       ├── Modal.tsx
│       ├── ProgressBar.tsx
│       ├── LoadingSkeleton.tsx
│       ├── EmptyState.tsx
│       └── ErrorDisplay.tsx
│
├── contexts/
│   ├── AuthContext.tsx
│   └── TenantContext.tsx     # [FUTURE]
│
├── pages/
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   ├── Shipment.tsx
│   ├── Analytics.tsx
│   ├── Users.tsx
│   └── Settings.tsx           # [NEW]
│
├── types/
│   └── index.ts               # All TypeScript interfaces
│
├── hooks/                     # [OPTIONAL] Custom hooks
│   ├── usePolling.ts
│   ├── useCountdown.ts
│   └── useTenant.ts
│
├── utils/                     # [OPTIONAL] Utility functions
│   ├── formatting.ts
│   ├── validation.ts
│   └── constants.ts
│
├── App.tsx                    # Root component
└── main.tsx                   # Entry point
```

---

## Component Complexity Matrix

| Component | Complexity | State Management | API Calls | Child Components |
|-----------|------------|------------------|-----------|------------------|
| **Pages** |
| Login | Low | Local | 1 | 1 |
| Dashboard | Medium | Local + API | 1 | 5 |
| Shipment | High | Local + API | 5+ | 15+ |
| Analytics | Medium | Local + API | 4 | 8 |
| Users | Medium | Local + API | 2 | 4 |
| NotificationSettings | Medium | Local + API | 2 | 5 |
| **Features** |
| ContainerTrackingPanel | High | Local + API | 2 | 4 |
| AISummaryCard | Medium | Local + API | 2 | 3 |
| EUDRStatusCard | Medium | Local + API | 3 | 2 |
| NotificationBell | Medium | Local + polling | 2 | 2 |
| DocumentUploadModal | Medium | Local + API | 1 | 3 |
| **UI Components** |
| MobileMenu | Low | Local | 0 | 0 |
| BottomSheet | Low | Local | 0 | 0 |
| ProgressBar | Low | Props | 0 | 0 |

---

## Testing Strategy

### Component Testing Priorities

**High Priority (Critical Path):**
- AuthContext and authentication flow
- Shipment page and data fetching
- Document upload and validation
- API client error handling
- Mobile responsiveness (manual)

**Medium Priority:**
- AI summary generation
- Notification preferences
- EUDR validation flow
- Analytics charts

**Low Priority (Nice to Have):**
- Empty states
- Loading skeletons
- Toast notifications
- Theme switching

### Test Types

1. **Unit Tests** (Jest + React Testing Library)
   - Individual component rendering
   - Props handling
   - Event handlers
   - Utility functions

2. **Integration Tests**
   - API client with mock responses
   - Context providers with child components
   - Form submission flows
   - Navigation flows

3. **E2E Tests** (Optional: Playwright/Cypress)
   - Login to dashboard
   - Upload document
   - Download audit pack
   - Mobile navigation

4. **Visual Regression** (Optional: Chromatic/Percy)
   - Component library consistency
   - Theme variations
   - Responsive breakpoints

---

## Performance Optimization Checklist

- [ ] Lazy load pages with `React.lazy()`
- [ ] Memoize expensive calculations with `useMemo`
- [ ] Debounce search inputs
- [ ] Virtualize long lists (react-window)
- [ ] Optimize images (WebP, srcset)
- [ ] Code splitting by route
- [ ] API response caching (already implemented)
- [ ] Reduce bundle size (tree shaking)
- [ ] Service worker for offline support (future)

---

**Document Control:**
- **Author:** UI/UX Design Architect
- **Last Updated:** 2026-01-03
- **Version:** 1.0
- **Status:** Reference Guide
