# TraceHub Frontend UI/UX Feature Specifications

**Version:** 1.0
**Date:** 2026-01-03
**Status:** Planning Phase

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Feature 1: Container Tracking Dashboard](#feature-1-container-tracking-dashboard)
3. [Feature 2: Audit Pack Download UI](#feature-2-audit-pack-download-ui)
4. [Feature 3: Mobile Responsiveness](#feature-3-mobile-responsiveness)
5. [Feature 4: Email Notification Preferences UI](#feature-4-email-notification-preferences-ui)
6. [Feature 5: AI Summary Display](#feature-5-ai-summary-display)
7. [Feature 6: Multi-tenant UI](#feature-6-multi-tenant-ui)
8. [Sprint Allocation](#sprint-allocation)
9. [Accessibility Considerations](#accessibility-considerations)
10. [Design System Additions](#design-system-additions)

---

## Current State Assessment

### Existing Stack
- **Framework:** React 18.2 with TypeScript
- **Styling:** Tailwind CSS 3.4
- **Routing:** React Router DOM 6.21
- **Charts:** Recharts 2.10
- **Icons:** Lucide React 0.303
- **Date Handling:** date-fns 3.0.6
- **HTTP:** Axios 1.6.2
 - **Testing:** Vitest 1.6.x, @vitest/ui 1.6.x, @vitest/coverage-v8 1.6.x, jsdom 23, Testing Library
 - **Build Tool:** Vite 5 (requires Node 18)

### Installation Requirements

For consistent installation across macOS and CI:

- Use Node 18.x and npm 9+
- Ensure `tracehub/frontend/.nvmrc` contains `18`
- `package.json` defines engines: `node>=18`, `npm>=9`
- Always install with `npm ci` (uses `package-lock.json`)
- Keep Vitest-related packages on the same minor version (1.6.x)

Quick start:

```bash
cd tracehub/frontend
nvm use 18            # if using nvm
npm ci
npm test -- --run
npm run test:coverage
npm run build
```

### Existing Pages
1. **Login** - OAuth2 authentication
2. **Dashboard** - Shipments list with status badges
3. **Shipment Detail** - Comprehensive shipment view with tabs
4. **Analytics** - Metrics and charts
5. **Users** - User management (admin only)

### Existing Components
- `Layout` - Navigation header with role badges
- `NotificationBell` - Dropdown with real-time updates
- `EUDRStatusCard` - Compliance status display
- `DocumentList` - Document grid/list view
- `DocumentReviewPanel` - Document validation panel
- `DocumentUploadModal` - Multi-step upload flow
- `TrackingTimeline` - Container events timeline
- `ComplianceStatus` - Document compliance indicators

### Design Patterns Established
- **Color System:** Primary (blue), Success (green), Warning (yellow), Danger (red), Gray scale
- **Badge Classes:** `.badge-info`, `.badge-success`, `.badge-warning`, `.badge-danger`
- **Button Classes:** `.btn-primary`, `.btn-secondary`
- **Card Class:** `.card` with consistent padding and shadows
- **Loading States:** Skeleton screens with pulse animation
- **Error States:** Centered error display with retry actions
- **Empty States:** Icon + message + optional action

---

## Feature 1: Container Tracking Dashboard

### Overview
Real-time visualization of container location and movement with map integration, timeline view, and ETA countdown.

### User Stories
1. As a **buyer**, I want to see where my container is on a map so I can plan for arrival.
2. As a **compliance officer**, I want to see all container events in chronological order so I can verify transit compliance.
3. As a **supplier**, I want to know the ETA and any delays so I can communicate with customers.

### Wireframe Description

#### Layout: Full-width panel in Shipment Detail page

```
┌─────────────────────────────────────────────────────────────┐
│  Container Tracking                                    [Sync]│
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────┐  ┌────────────────────────┐   │
│  │                          │  │  Current Status         │   │
│  │    MAP VIEW             │  │  In Transit             │   │
│  │                          │  │                         │   │
│  │  [Origin] ────▶ [Dest]  │  │  Current Location       │   │
│  │     ●            ◉       │  │  Port of Hamburg        │   │
│  │                          │  │                         │   │
│  │                          │  │  ETA Countdown          │   │
│  │                          │  │  ⏰ 3 days 14 hours    │   │
│  └──────────────────────────┘  │                         │   │
│                                 │  Vessel                 │   │
│                                 │  MSC MARIA / V123      │   │
│  ┌──────────────────────────┐  └────────────────────────┘   │
│  │  EVENT TIMELINE          │                               │
│  │                          │                               │
│  │  ● Departed POL          │  Dec 20, 2025 14:30          │
│  │  │                       │  Lagos, Nigeria              │
│  │  ●                       │                               │
│  │  │ Transshipment         │  Dec 28, 2025 08:15          │
│  │  ●                       │  Tangier, Morocco            │
│  │  │                       │                               │
│  │  ◉ Current               │  Jan 2, 2026 16:45           │
│  │    At Sea                │  North Atlantic              │
│  │                          │                               │
│  └──────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### New Components

1. **`ContainerTrackingPanel`**
   - Parent container component
   - Manages tracking data state
   - Handles refresh logic
   - Props: `shipmentId: string`, `containerNumber: string`

2. **`TrackingMap`**
   - Interactive map visualization
   - Shows route from POL to POD
   - Current location marker
   - Technology: Simple SVG path for MVP, future: Leaflet or Mapbox
   - Props: `origin: LocationInfo`, `destination: LocationInfo`, `currentLocation: LocationInfo`

3. **`TrackingStatusCard`**
   - Real-time status display
   - ETA countdown with live update
   - Vessel information
   - Delay alerts
   - Props: `liveTracking: LiveTracking`

4. **`ETACountdown`**
   - Live countdown timer
   - Color-coded urgency (green: >7 days, yellow: 3-7 days, red: <3 days)
   - Shows delays prominently
   - Props: `eta: string`, `delayHours?: number`

5. **`EventTimeline`** (Enhanced version of existing TrackingTimeline)
   - Vertical timeline with icons
   - Past events (completed)
   - Current location (highlighted)
   - Future expected events (predicted)
   - Props: `events: ContainerEvent[]`, `currentStatus: string`

### API Dependencies

**Existing:**
- `GET /tracking/live/{container_number}` - Live tracking data
- `GET /shipments/{id}/events` - Container events
- `POST /tracking/refresh/{shipment_id}` - Sync with carrier API

**New/Enhanced:**
None required - all endpoints exist

### Complexity Estimate
**Medium-High** (8-12 hours)
- Map visualization: 4 hours
- Timeline enhancements: 2 hours
- ETA countdown: 2 hours
- Integration and state management: 3 hours
- Responsive design: 2 hours

### Implementation Notes
1. Use React hooks for live countdown timer (`useEffect` with interval)
2. Implement optimistic updates when refreshing tracking
3. Handle offline/no-data gracefully (show last known position)
4. Use `recharts` for simple route visualization initially
5. Mobile: Stack map and status card vertically

### Accessibility
- ARIA labels for all interactive elements
- Keyboard navigation for timeline
- Screen reader announcements for ETA changes
- High contrast mode support for map markers

---

## Feature 2: Audit Pack Download UI

### Overview
Enhanced download experience with progress indication, preview of contents, and success confirmation.

### User Stories
1. As a **buyer**, I want to preview what's included in the audit pack before downloading.
2. As a **compliance officer**, I want clear feedback that my download is processing and complete.
3. As a **supplier**, I want to know if documents are missing before generating the pack.

### Wireframe Description

#### Location: Shipment Detail page, Quick Actions sidebar + Header

```
┌────────────────────────────────────────────────────────┐
│  Download Audit Pack                           [Close] │
├────────────────────────────────────────────────────────┤
│                                                         │
│  📦 VIBO-2026-001 Audit Pack Contents                  │
│                                                         │
│  ✓ Shipment Metadata                                   │
│    └─ Reference, container, B/L, parties               │
│                                                         │
│  ✓ Documents (12/12 complete)                          │
│    ✓ Bill of Lading                                    │
│    ✓ Commercial Invoice                                │
│    ✓ Packing List                                      │
│    ✓ Certificate of Origin                             │
│    ✓ Phytosanitary Certificate                         │
│    ✓ EUDR Due Diligence Statement                      │
│    ... (6 more)                                         │
│                                                         │
│  ✓ Container Events (8 events)                         │
│    └─ Full timeline from gate-in to delivery           │
│                                                         │
│  ✓ EUDR Compliance Report                              │
│    └─ Risk assessment and validation results           │
│                                                         │
│  ⚠ Missing Items                                       │
│    └─ None - all required documents present            │
│                                                         │
│  Estimated Size: ~4.2 MB                                │
│  Format: ZIP archive with PDF index                    │
│                                                         │
│  [Cancel]                    [Download Audit Pack]     │
└────────────────────────────────────────────────────────┘

// During download:
┌────────────────────────────────────────────────────────┐
│  Generating Audit Pack...                              │
│                                                         │
│  ████████████████░░░░░░░░  67%                         │
│                                                         │
│  Preparing documents...                                │
│  Your download will start automatically.               │
└────────────────────────────────────────────────────────┘

// Success:
┌────────────────────────────────────────────────────────┐
│  ✓ Audit Pack Downloaded Successfully                  │
│                                                         │
│  VIBO-2026-001-audit-pack.zip (4.2 MB)                 │
│                                                         │
│  The audit pack has been saved to your downloads       │
│  folder.                                                │
│                                                         │
│  [View Another Shipment]           [Close]             │
└────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### New Components

1. **`AuditPackPreviewModal`**
   - Modal dialog showing pack contents
   - Tree view of included items
   - Missing items warnings
   - File size estimate
   - Props: `shipmentId: string`, `isOpen: boolean`, `onClose: () => void`

2. **`AuditPackDownloadButton`** (Enhanced)
   - Button with progress states
   - Shows preview modal on first click
   - Direct download on subsequent clicks
   - Props: `shipmentId: string`, `shipmentReference: string`

3. **`DownloadProgressModal`**
   - Progress bar (indeterminate for now, determinate in future)
   - Status messages
   - Auto-closes on success or shows error
   - Props: `isDownloading: boolean`, `progress?: number`, `error?: string`

4. **`DownloadSuccessToast`**
   - Non-blocking success notification
   - Auto-dismiss after 5 seconds
   - Link to re-download if needed
   - Props: `fileName: string`, `fileSize: number`

### API Dependencies

**Existing:**
- `GET /shipments/{id}/audit-pack` - Download audit pack (returns blob)

**New:**
- `GET /shipments/{id}/audit-pack/preview` - Get pack contents metadata
  ```typescript
  interface AuditPackPreview {
    shipment_reference: string
    total_documents: number
    missing_documents: DocumentType[]
    included_sections: {
      shipment_metadata: boolean
      documents: boolean
      events: boolean
      eudr_report: boolean
      compliance_summary: boolean
    }
    estimated_size_bytes: number
    document_list: Array<{
      document_type: DocumentType
      name: string
      included: boolean
    }>
    event_count: number
  }
  ```

### Complexity Estimate
**Medium** (6-8 hours)
- Preview modal and content tree: 3 hours
- Download progress states: 2 hours
- Success/error handling: 1 hour
- Backend preview endpoint: 2 hours

### Implementation Notes
1. Cache preview data for 1 minute to avoid repeated calls
2. Use browser download API (`<a>` element with `download` attribute)
3. Show file size in human-readable format (KB/MB)
4. Handle large files (>10MB) with warning about download time
5. Provide option to download individual sections in future

### Accessibility
- Modal follows WAI-ARIA dialog pattern
- Focus trap in modal
- ESC key closes modal
- Screen reader announces download progress
- High contrast for progress bar

---

## Feature 3: Mobile Responsiveness

### Overview
Optimize all pages and components for mobile devices (320px - 768px) with touch-friendly interactions.

### User Stories
1. As a **buyer on mobile**, I want to check shipment status while traveling.
2. As a **supplier on mobile**, I want to upload documents from my phone camera.
3. As a **user on tablet**, I want full functionality without horizontal scrolling.

### Breakpoints Strategy

```css
/* Tailwind defaults - use these */
sm: 640px   /* Small devices */
md: 768px   /* Tablets */
lg: 1024px  /* Laptops */
xl: 1280px  /* Desktops */
2xl: 1536px /* Large screens */
```

### Component-Level Responsive Patterns

#### 1. Layout Component
**Current Issues:**
- Navigation items hidden on mobile
- User info truncated
- Logo and actions cramped

**Solutions:**
```
Mobile (<640px):
┌─────────────────────────┐
│ ☰  TraceHub      🔔  👤 │  <- Hamburger menu
└─────────────────────────┘

Tablet (640px - 1024px):
┌─────────────────────────────────────────┐
│ TraceHub  Dashboard Analytics  🔔  👤  │
└─────────────────────────────────────────┘

Desktop (>1024px):
┌───────────────────────────────────────────────────────┐
│ TraceHub  Dashboard  Analytics  Users  🔔  John Doe  │
└───────────────────────────────────────────────────────┘
```

**Implementation:**
- Add hamburger menu (`<MobileMenu>`) for navigation on small screens
- Show user initials instead of full name on mobile
- Stack notifications and user menu vertically in dropdown

#### 2. Dashboard Page
**Current Issues:**
- Shipment cards too wide with horizontal scroll
- 4-column grid breaks on mobile

**Solutions:**
```
Mobile:
┌─────────────────────┐
│ VIBO-2026-001      │
│ 🏷️ In Transit      │
│ 📦 ABCD1234567     │
│ 🚢 Lagos → Hamburg  │
│ 📅 ETA: Jan 15     │
└─────────────────────┘

Tablet:
┌────────────────────────────────┐
│ VIBO-2026-001     🏷️ Transit   │
│ 📦 ABCD  🚢 Lagos → Hamburg    │
│ 📅 ETA: Jan 15, 2026           │
└────────────────────────────────┘
```

**Implementation:**
- Stack shipment info vertically on mobile
- Use 2-column grid on mobile, 4-column on desktop
- Touch-friendly card height (min 80px)

#### 3. Shipment Detail Page
**Current Issues:**
- 3-column layout too cramped
- Tabs hard to tap
- Map too small

**Solutions:**
```
Mobile (Single column):
1. Header (back, title, status)
2. Quick actions (collapsible)
3. Tracking status card
4. Map (full width)
5. Tabs (documents/tracking)
6. Tab content
7. Compliance cards (stacked)

Desktop (2 + 1 column):
1-2. Main content | 3. Sidebar
```

**Implementation:**
- Change from `lg:grid-cols-3` to single column on mobile
- Increase tab button height to 48px (touch target)
- Full-width map on mobile, 60% on desktop
- Collapsible sections with accordion pattern

#### 4. Document Upload
**Current Issues:**
- Modal too wide for mobile
- Form fields cramped

**Solutions:**
- Modal takes full screen on mobile (100vh)
- Larger file picker button
- Native camera integration (`accept="image/*" capture="environment"`)
- Bottom sheet pattern instead of centered modal

#### 5. Tables (Analytics, Users)
**Current Issues:**
- Tables overflow on mobile
- Too many columns visible

**Solutions:**
- Card-based layout on mobile instead of table
- Horizontal scroll with sticky first column
- Hide non-essential columns on mobile
- "View More" expandable rows

### Touch Interactions

**Minimum Touch Targets:** 44x44px (Apple HIG) / 48x48px (Material)

**Gestures:**
- Swipe to refresh on lists
- Pull to refresh on dashboard
- Swipe to delete notifications
- Pinch to zoom on maps (future)
- Long press for context menu (future)

### Mobile-Specific Components

#### New Components

1. **`MobileMenu`**
   - Slide-out navigation drawer
   - Full-height overlay
   - Touch-friendly list items
   - Props: `isOpen: boolean`, `onClose: () => void`

2. **`MobileHeader`**
   - Compact header with hamburger
   - Sticky positioning
   - Props: `title: string`, `onMenuOpen: () => void`

3. **`BottomSheet`**
   - Mobile-optimized modal from bottom
   - Draggable handle
   - Swipe to dismiss
   - Props: `isOpen: boolean`, `children: ReactNode`, `onClose: () => void`

4. **`CollapsibleSection`**
   - Accordion-style content
   - Smooth animations
   - Props: `title: string`, `defaultOpen: boolean`, `children: ReactNode`

### Testing Checklist

- [ ] iPhone SE (375x667) - smallest modern iPhone
- [ ] iPhone 14 Pro (393x852)
- [ ] iPad Mini (744x1133)
- [ ] Samsung Galaxy S21 (360x800)
- [ ] Surface Pro (912x1368)
- [ ] Landscape orientation for all devices

### Complexity Estimate
**High** (16-24 hours)
- Layout responsive refactor: 6 hours
- Dashboard and shipment pages: 4 hours
- Mobile menu and navigation: 3 hours
- Forms and modals: 3 hours
- Tables and lists: 2 hours
- Touch interactions: 2 hours
- Testing and refinement: 4 hours

### Implementation Notes
1. Mobile-first approach: Write mobile styles first, then add `md:` and `lg:` modifiers
2. Use Tailwind's responsive utilities extensively
3. Test with real devices, not just browser emulation
4. Consider network conditions (slower on mobile)
5. Use native inputs for dates, times (better UX on mobile)
6. Lazy load images and heavy components

### Accessibility
- Touch targets minimum 44px
- Adequate spacing between interactive elements
- No hover-only interactions
- Keyboard navigation still works with external keyboards
- Zoom up to 200% without loss of functionality

---

## Feature 4: Email Notification Preferences UI

### Overview
User settings page for managing email notification subscriptions and frequency preferences.

### User Stories
1. As a **buyer**, I want to disable document upload notifications but keep ETA change alerts.
2. As a **compliance officer**, I want daily digest emails instead of real-time notifications.
3. As a **supplier**, I want to opt out of all emails but keep in-app notifications.

### Wireframe Description

#### New Page: `/settings/notifications`

```
┌─────────────────────────────────────────────────────────────┐
│  Settings > Notification Preferences                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Email Notifications                                          │
│  Control which events trigger email notifications            │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Shipment Events                                        │ │
│  │                                                         │ │
│  │ ☑ Shipment departed            [Email] [In-App]       │ │
│  │   Notify when a container departs from origin         │ │
│  │                                                         │ │
│  │ ☑ Shipment arrived             [Email] [In-App]       │ │
│  │   Notify when a container arrives at destination      │ │
│  │                                                         │ │
│  │ ☑ ETA changed                  [Email] [In-App]       │ │
│  │   Notify when estimated time of arrival changes       │ │
│  │                                                         │ │
│  │ ☐ Shipment delivered           [Email] [In-App]       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Document Events                                        │ │
│  │                                                         │ │
│  │ ☑ Document uploaded            [Email] [In-App]       │ │
│  │ ☑ Document validated           [Email] [In-App]       │ │
│  │ ☐ Document rejected            [Email] [In-App]       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Compliance Alerts                                      │ │
│  │                                                         │ │
│  │ ☑ EUDR compliance issue        [Email] [In-App]       │ │
│  │ ☑ Certificate expiring soon    [Email] [In-App]       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Notification Frequency                                       │
│  ○ Real-time (immediate emails)                              │
│  ● Daily digest (once per day at 08:00)                     │
│  ○ Weekly summary (Monday mornings)                          │
│  ○ Disabled (in-app only)                                    │
│                                                               │
│  Digest Time: [08:00] ▼  Timezone: [UTC] ▼                  │
│                                                               │
│  [Cancel]                            [Save Preferences]       │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### New Components

1. **`NotificationSettingsPage`**
   - Main settings page container
   - Loads user preferences
   - Handles save/cancel actions
   - Route: `/settings/notifications`

2. **`NotificationTypeToggle`**
   - Individual notification setting
   - Email + In-app toggles
   - Description text
   - Props: `type: NotificationType`, `label: string`, `description: string`, `emailEnabled: boolean`, `inAppEnabled: boolean`, `onChange: (channel: 'email' | 'in-app', enabled: boolean) => void`

3. **`NotificationGroup`**
   - Collapsible group of related notifications
   - "Enable/disable all" toggle
   - Props: `title: string`, `children: ReactNode`, `defaultOpen: boolean`

4. **`FrequencySelector`**
   - Radio button group for digest frequency
   - Time picker for digest time
   - Timezone selector
   - Props: `frequency: 'realtime' | 'daily' | 'weekly' | 'disabled'`, `digestTime?: string`, `timezone?: string`, `onChange: (settings) => void`

### API Dependencies

**New Endpoints Required:**

1. `GET /users/me/notification-preferences`
   ```typescript
   interface NotificationPreferences {
     user_id: string
     preferences: {
       [key in NotificationType]: {
         email: boolean
         in_app: boolean
       }
     }
     frequency: 'realtime' | 'daily' | 'weekly' | 'disabled'
     digest_time?: string // "08:00"
     timezone?: string // "UTC"
     updated_at: string
   }
   ```

2. `PUT /users/me/notification-preferences`
   - Body: Same as response above
   - Returns: Updated preferences + success message

3. `GET /notifications/types` (for metadata)
   ```typescript
   interface NotificationTypeMetadata {
     type: NotificationType
     label: string
     description: string
     category: 'shipment' | 'document' | 'compliance' | 'system'
     default_enabled: boolean
   }
   ```

### Complexity Estimate
**Medium** (8-10 hours)
- Settings page UI: 3 hours
- Toggle components: 2 hours
- Frequency selector: 1 hour
- Backend preferences model: 2 hours
- Backend API endpoints: 2 hours
- Testing and validation: 2 hours

### Implementation Notes
1. Save preferences to database (new `user_notification_preferences` table)
2. Use optimistic updates for toggle changes
3. Show "Saved" indicator after successful update
4. Reset to defaults option
5. Preview digest email format (future enhancement)
6. Consider adding quiet hours (e.g., no emails 10pm-7am)

### Accessibility
- Keyboard navigation for all toggles
- ARIA labels for switch components
- Visual and auditory feedback on save
- Clear error messages for validation failures
- Screen reader announces preference changes

---

## Feature 5: AI Summary Display

### Overview
Display AI-generated summaries for shipments, compliance status, and document discrepancies with prominent visual indicators.

### User Stories
1. As a **buyer**, I want a plain-English summary of shipment status without reading all details.
2. As a **compliance officer**, I want AI to highlight potential issues before I review documents.
3. As a **supplier**, I want to quickly understand what's missing or needs attention.

### Wireframe Description

#### Location: Shipment Detail page, top of main content area

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 AI Summary                                      [Refresh]│
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Shipment VIBO-2026-001 is in good standing and on track    │
│  for delivery. All required documents have been uploaded     │
│  and validated. EUDR compliance verified with low risk.      │
│                                                               │
│  📊 Status: On Schedule                                      │
│  ✓ Documents: 12/12 complete                                │
│  ✓ EUDR: Compliant (low risk)                               │
│  ⚠ Attention: Certificate of Origin expires in 45 days      │
│                                                               │
│  Generated 5 minutes ago                                     │
└─────────────────────────────────────────────────────────────┘

// With Issues:
┌─────────────────────────────────────────────────────────────┐
│  🤖 AI Summary                                      [Refresh]│
├─────────────────────────────────────────────────────────────┤
│  ⚠️ Action Required                                          │
│                                                               │
│  Shipment VIBO-2026-002 has 3 issues requiring immediate    │
│  attention. Container tracking shows a 2-day delay due to    │
│  port congestion. EUDR compliance is pending origin data.    │
│                                                               │
│  🚨 Critical Issues:                                         │
│  • Phytosanitary certificate is missing                     │
│  • Origin geolocation coordinates not verified              │
│  • ETA changed from Jan 10 to Jan 12 (2 days delay)        │
│                                                               │
│  ⚡ Recommended Actions:                                     │
│  1. Upload phytosanitary certificate immediately            │
│  2. Verify origin coordinates with supplier                 │
│  3. Notify buyer of revised ETA                             │
│                                                               │
│  Generated 2 minutes ago                                     │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### New Components

1. **`AISummaryCard`**
   - Main summary display component
   - Color-coded based on severity (green/yellow/red)
   - Expandable for detailed breakdown
   - Props: `shipmentId: string`, `autoRefresh?: boolean`

2. **`SummaryStatusBadge`**
   - Visual status indicator
   - Icons for different states
   - Props: `status: 'excellent' | 'good' | 'attention' | 'critical'`

3. **`RecommendedActions`**
   - Numbered list of AI-suggested actions
   - Clickable items that navigate to relevant section
   - Priority indicators
   - Props: `actions: ActionItem[]`

4. **`DiscrepancyAlert`**
   - Inline alert for specific issues
   - Links to problematic document/field
   - Props: `discrepancy: DiscrepancyItem`, `onClick?: () => void`

5. **`SummaryLoadingState`**
   - Skeleton with "Analyzing..." message
   - Animated shimmer effect
   - Props: none

### Data Model

```typescript
interface AISummary {
  shipment_id: string
  generated_at: string
  summary_text: string
  status: 'excellent' | 'good' | 'attention' | 'critical'

  metrics: {
    documents_complete: number
    documents_total: number
    eudr_status: EUDRValidationStatus
    tracking_status: string
    on_schedule: boolean
  }

  issues: Array<{
    severity: 'critical' | 'warning' | 'info'
    category: 'document' | 'compliance' | 'tracking' | 'expiry'
    message: string
    affected_item?: string
  }>

  recommendations: Array<{
    priority: 1 | 2 | 3
    action: string
    target_url?: string
  }>

  confidence_score: number // 0-1
}
```

### API Dependencies

**New Endpoints Required:**

1. `GET /ai/summary/{shipment_id}`
   - Returns: `AISummary` object
   - Cache: 5 minutes (can force refresh)

2. `POST /ai/summary/{shipment_id}/regenerate`
   - Force regeneration with latest data
   - Returns: Updated `AISummary`

**Future Enhancement:**
- `POST /ai/analyze/document/{document_id}` - Analyze specific document
- `POST /ai/chat` - Conversational interface for questions

### AI Generation Logic (Backend)

**Phase 1: Rule-Based (Current Sprint)**
```python
def generate_summary(shipment: Shipment) -> AISummary:
    """
    Generate summary using business rules and templates
    """
    issues = []
    recommendations = []

    # Document completeness check
    doc_summary = get_document_summary(shipment.id)
    if doc_summary.missing:
        issues.append({
            'severity': 'critical',
            'category': 'document',
            'message': f'{len(doc_summary.missing)} required documents missing'
        })
        recommendations.append({
            'priority': 1,
            'action': f'Upload missing documents: {", ".join(doc_summary.missing)}'
        })

    # EUDR compliance check
    eudr_status = get_eudr_status(shipment.id)
    if eudr_status.overall_status != 'compliant':
        issues.append({
            'severity': 'critical',
            'category': 'compliance',
            'message': 'EUDR compliance validation failed'
        })

    # ETA tracking
    if shipment.eta and shipment.delay_hours:
        issues.append({
            'severity': 'warning',
            'category': 'tracking',
            'message': f'Container delayed by {shipment.delay_hours} hours'
        })

    # Generate natural language summary
    summary_text = generate_summary_text(shipment, issues, recommendations)

    return AISummary(...)
```

**Phase 2: LLM-Powered (Future)**
```python
def generate_summary_llm(shipment: Shipment) -> AISummary:
    """
    Use Claude API to generate intelligent summary
    """
    context = {
        'shipment': shipment.dict(),
        'documents': get_documents(shipment.id),
        'events': get_events(shipment.id),
        'eudr': get_eudr_status(shipment.id)
    }

    prompt = f"""
    Analyze this shipment and provide:
    1. Brief status summary (2-3 sentences)
    2. Critical issues requiring attention
    3. Recommended actions in priority order

    Shipment data: {json.dumps(context)}
    """

    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse response and structure as AISummary
    return parse_llm_response(response)
```

### Complexity Estimate
**Medium** (10-14 hours)
- Summary card UI: 3 hours
- Backend rule-based logic: 4 hours
- API endpoints: 2 hours
- Recommendation actions: 2 hours
- Testing and refinement: 3 hours

**Future LLM Integration:** +8 hours

### Implementation Notes
1. Start with template-based summaries (rules engine)
2. Cache summaries for 5 minutes to reduce computation
3. Use background job for regeneration if heavy
4. Log all AI suggestions for future training
5. Allow users to provide feedback on usefulness
6. Consider A/B testing different summary styles

### Accessibility
- ARIA live region for dynamic updates
- Clear visual hierarchy (headings)
- Color not sole indicator (use icons too)
- High contrast for readability
- Screen reader friendly action lists

---

## Feature 6: Multi-tenant UI (Future)

### Overview
Enable multiple organizations to use TraceHub with isolated data, custom branding, and tenant-level administration.

### User Stories
1. As a **platform admin**, I want to onboard new exporters without code changes.
2. As a **tenant admin**, I want to customize our company logo and colors.
3. As a **user**, I want to switch between companies I work with (if multi-tenant access).

### Wireframe Description

#### Tenant Switcher (Header)
```
┌─────────────────────────────────────────────┐
│ [VIBOTAJ Logo] ▼  Dashboard  Analytics  🔔 │
└─────────────────────────────────────────────┘
       ↓ (Click to expand)
┌────────────────────────────┐
│ Your Organizations         │
├────────────────────────────┤
│ ● VIBOTAJ GmbH            │
│   (Current)                │
│                            │
│   Acme Export Ltd          │
│   Global Logistics Co      │
├────────────────────────────┤
│ + Add Organization         │
└────────────────────────────┘
```

#### Tenant Admin Dashboard (`/admin/tenant`)
```
┌─────────────────────────────────────────────────────────────┐
│  Tenant Settings                                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Company Information                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Company Name: [VIBOTAJ GmbH              ]            │ │
│  │ Primary Contact: [John Doe               ]            │ │
│  │ Email: [info@vibotaj.de                  ]            │ │
│  │ Country: [Germany               ▼]                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Branding                                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Logo: [Upload Logo]  [Preview]                        │ │
│  │       ┌─────────┐                                      │ │
│  │       │ VIBOTAJ │                                      │ │
│  │       └─────────┘                                      │ │
│  │                                                         │ │
│  │ Primary Color: [#0066CC] ⬛                            │ │
│  │ Secondary Color: [#FF9900] ⬛                          │ │
│  │                                                         │ │
│  │ [Preview Theme]                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Features                                                     │
│  ☑ Document Management                                      │
│  ☑ Container Tracking                                       │
│  ☑ EUDR Compliance                                          │
│  ☐ AI Summaries (Premium)                                   │
│  ☐ Advanced Analytics (Premium)                             │
│                                                               │
│  Subscription                                                 │
│  Plan: Professional                                           │
│  Users: 12/25                                                │
│  Storage: 4.2 GB / 50 GB                                     │
│  [Upgrade Plan]                                              │
│                                                               │
│  [Cancel]                            [Save Changes]          │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Considerations

#### Data Isolation
```typescript
// Every API request includes tenant context
interface RequestContext {
  user_id: string
  tenant_id: string  // Added
  role: UserRole
}

// All database queries filtered by tenant
SELECT * FROM shipments WHERE tenant_id = :tenant_id
```

#### Tenant Context Provider
```typescript
interface TenantContext {
  id: string
  name: string
  logo_url?: string
  theme: {
    primary_color: string
    secondary_color: string
    logo_position: 'left' | 'center'
  }
  features: {
    ai_summaries: boolean
    advanced_analytics: boolean
    custom_workflows: boolean
  }
  subscription: {
    plan: 'free' | 'professional' | 'enterprise'
    max_users: number
    max_storage_gb: number
  }
}

// React context
const { tenant, switchTenant } = useTenant()
```

#### Theming System
```typescript
// Dynamic CSS variables based on tenant
:root {
  --primary-color: var(--tenant-primary, #0066CC);
  --secondary-color: var(--tenant-secondary, #FF9900);
  --logo-url: var(--tenant-logo);
}
```

### Component Breakdown

#### New Components

1. **`TenantSwitcher`**
   - Dropdown in header
   - Shows user's accessible tenants
   - Switches context without full reload
   - Props: `currentTenant: TenantContext`, `availableTenants: TenantContext[]`, `onSwitch: (tenantId: string) => void`

2. **`TenantAdminPage`**
   - Settings page for tenant admins
   - Company info, branding, features
   - Route: `/admin/tenant`
   - Permission: `tenant_admin` role

3. **`BrandingPreview`**
   - Live preview of theme changes
   - Shows header, buttons, cards with new colors
   - Props: `theme: TenantTheme`

4. **`FeatureToggle`**
   - Enable/disable features per tenant
   - Shows plan restrictions
   - Props: `feature: string`, `enabled: boolean`, `requiresPlan?: string`

5. **`TenantInviteModal`**
   - Invite new users to tenant
   - Email + role selection
   - Props: `tenantId: string`, `isOpen: boolean`, `onClose: () => void`

### Database Schema Changes

```sql
-- New table
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    logo_url TEXT,
    theme JSONB DEFAULT '{}',
    features JSONB DEFAULT '{}',
    subscription_plan VARCHAR(50) DEFAULT 'free',
    max_users INTEGER DEFAULT 5,
    max_storage_gb INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Modify existing tables
ALTER TABLE users ADD COLUMN default_tenant_id UUID REFERENCES tenants(id);
ALTER TABLE shipments ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE documents ADD COLUMN tenant_id UUID REFERENCES tenants(id);
-- ... (all resource tables need tenant_id)

-- User-tenant association (many-to-many)
CREATE TABLE user_tenants (
    user_id UUID REFERENCES users(id),
    tenant_id UUID REFERENCES tenants(id),
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, tenant_id)
);
```

### API Dependencies

**New Endpoints:**

1. `GET /tenants` - List user's accessible tenants
2. `GET /tenants/{id}` - Get tenant details
3. `PUT /tenants/{id}` - Update tenant (admin only)
4. `POST /tenants/{id}/invite` - Invite user to tenant
5. `POST /tenants/switch/{id}` - Switch active tenant context
6. `GET /tenants/{id}/usage` - Get storage/user usage stats

### Complexity Estimate
**Very High** (40-60 hours)
- Database schema migration: 8 hours
- Backend tenant context: 10 hours
- Multi-tenancy middleware: 6 hours
- Tenant admin UI: 8 hours
- Tenant switcher: 4 hours
- Theming system: 6 hours
- Data migration for existing data: 4 hours
- Testing and security audit: 10 hours
- Documentation: 4 hours

### Implementation Notes
1. **Phase 1:** Single-tenant with database structure (prepare for multi-tenant)
2. **Phase 2:** Tenant switching and isolation
3. **Phase 3:** Custom branding and themes
4. **Phase 4:** Feature flags and plans
5. Consider subdomain routing (vibotaj.tracehub.com)
6. Implement row-level security (RLS) in PostgreSQL
7. Careful authorization checks (user can only access own tenant data)
8. Audit logging for all tenant-level changes

### Security Considerations
- Validate tenant_id on every request
- Prevent cross-tenant data leakage
- Tenant isolation in file storage (separate S3 buckets/prefixes)
- Rate limiting per tenant
- Session invalidation on tenant switch
- GDPR/data residency compliance (future)

### Accessibility
- Clear indication of current tenant
- Keyboard accessible switcher
- Screen reader announces tenant switch
- High contrast for branding preview
- Form validation and error messages

---

## Sprint Allocation

### Sprint 1: Foundation & High Priority (2 weeks)
**Goal:** Improve core user experience with tracking and mobile support

**Features:**
1. Container Tracking Dashboard (10 hours)
2. Mobile Responsiveness - Phase 1 (12 hours)
   - Layout, Dashboard, Shipment pages
   - Mobile menu
   - Touch interactions

**Total:** ~22 hours (~11 hours/week)

**Deliverables:**
- Live container map and timeline
- Mobile-optimized layouts for main pages
- Touch-friendly navigation

---

### Sprint 2: Downloads & Settings (2 weeks)
**Goal:** Enhanced download experience and user preferences

**Features:**
1. Audit Pack Download UI (8 hours)
2. Email Notification Preferences UI (10 hours)
3. Mobile Responsiveness - Phase 2 (8 hours)
   - Forms, modals, tables
   - Bottom sheet implementation

**Total:** ~26 hours (~13 hours/week)

**Deliverables:**
- Preview and progress for audit pack downloads
- User notification settings page
- Fully responsive forms and modals

---

### Sprint 3: AI & Intelligence (2 weeks)
**Goal:** Add intelligent summaries and insights

**Features:**
1. AI Summary Display (12 hours)
   - Rule-based summary generation
   - Recommendation engine
   - Discrepancy alerts

**Total:** ~12 hours (~6 hours/week)

**Deliverables:**
- AI-powered shipment summaries
- Actionable recommendations
- Issue detection and highlighting

---

### Sprint 4: Multi-tenancy (4 weeks)
**Goal:** Enable platform for multiple organizations

**Features:**
1. Multi-tenant UI (50 hours)
   - Database migration
   - Tenant context and switching
   - Admin dashboard
   - Theming system

**Total:** ~50 hours (~12.5 hours/week)

**Deliverables:**
- Tenant switcher in header
- Tenant admin settings
- Custom branding support
- Full data isolation

---

## Accessibility Considerations

### WCAG 2.1 AA Compliance Checklist

#### Perceivable
- [ ] All images have alt text
- [ ] Color contrast ratios ≥ 4.5:1 for normal text
- [ ] Color contrast ratios ≥ 3:1 for large text
- [ ] Color not used as sole indicator
- [ ] Text resizable up to 200% without loss of functionality
- [ ] Captions for video content (future)

#### Operable
- [ ] All functionality keyboard accessible
- [ ] No keyboard traps
- [ ] Skip navigation links
- [ ] Focus indicators visible
- [ ] Touch targets ≥ 44x44px
- [ ] Enough time for timed actions (can be extended)
- [ ] Pause/stop for auto-updating content

#### Understandable
- [ ] Language of page declared (`<html lang="en">`)
- [ ] Consistent navigation across pages
- [ ] Form labels and instructions clear
- [ ] Error messages specific and helpful
- [ ] Error prevention (confirmations for destructive actions)

#### Robust
- [ ] Valid HTML markup
- [ ] ARIA landmarks used appropriately
- [ ] ARIA live regions for dynamic content
- [ ] Compatible with assistive technologies

### Testing Tools
- **Automated:** axe DevTools, Lighthouse
- **Manual:** Keyboard navigation, screen reader (NVDA/VoiceOver)
- **User Testing:** Involve users with disabilities

---

## Design System Additions

### New Color Utilities

```css
/* AI/Intelligence themed colors */
.text-ai-primary { color: #7C3AED; }
.bg-ai-primary { background-color: #7C3AED; }
.text-ai-secondary { color: #A78BFA; }
.bg-ai-secondary { background-color: #A78BFA; }

/* Status colors for summaries */
.status-excellent { color: #059669; background-color: #D1FAE5; }
.status-good { color: #0891B2; background-color: #CFFAFE; }
.status-attention { color: #F59E0B; background-color: #FEF3C7; }
.status-critical { color: #DC2626; background-color: #FEE2E2; }
```

### New Component Classes

```css
/* Bottom sheet */
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(100%);
  transition: transform 0.3s ease;
}

.bottom-sheet.open {
  transform: translateY(0);
}

/* Mobile menu */
.mobile-menu {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 280px;
  background: white;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  z-index: 1000;
}

.mobile-menu.open {
  transform: translateX(0);
}

/* Progress bar */
.progress-bar {
  height: 8px;
  background: #E5E7EB;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3B82F6, #2563EB);
  transition: width 0.3s ease;
}

/* Countdown timer */
.countdown-timer {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}

/* AI summary card */
.ai-summary-card {
  border-left: 4px solid var(--ai-primary);
  background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
}
```

### Icon Additions

**Lucide React icons to add:**
- `Sparkles` - AI/automation indicator
- `Target` - Goals/recommendations
- `TrendingUp` / `TrendingDown` - Performance indicators
- `Layers` - Multi-tenant/organization
- `Palette` - Theming/branding
- `Settings2` - Advanced settings
- `Zap` - Quick actions
- `Timer` - Countdown/urgency

---

## Summary of Deliverables

### Immediate Value (Sprints 1-2)
1. **Container Tracking Dashboard** - Real-time visibility
2. **Mobile Responsiveness** - Access on-the-go
3. **Audit Pack Download UI** - Better download experience
4. **Notification Preferences** - User control

### Medium-term Value (Sprint 3)
5. **AI Summaries** - Intelligence layer

### Long-term Value (Sprint 4)
6. **Multi-tenant UI** - Platform scalability

### Total Effort Estimate
- **Sprint 1:** 22 hours
- **Sprint 2:** 26 hours
- **Sprint 3:** 12 hours
- **Sprint 4:** 50 hours
- **TOTAL:** ~110 hours (~14 working days)

---

## Next Steps

1. **Review and Prioritize:** Stakeholder review of feature specs
2. **Design Mockups:** High-fidelity designs for key screens (optional)
3. **API Contracts:** Finalize new endpoint specifications with backend team
4. **Component Library:** Set up Storybook for component documentation (optional)
5. **Sprint Planning:** Assign features to developers
6. **Kickoff Sprint 1:** Start with Container Tracking Dashboard

---

**Document Control:**
- **Author:** UI/UX Design Architect
- **Last Updated:** 2026-01-03
- **Version:** 1.0
- **Status:** Ready for Review
