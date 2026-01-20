# TraceHub UI/UX Design System

> A calm, confident control tower for container tracking and compliance

**Version:** 1.0
**Created:** 2026-01-20
**Status:** Active

---

## Design Philosophy

TraceHub is not a generic SaaS dashboard. It is a **control tower** for exporters and buyers making time-critical shipment and compliance decisions. Every design choice serves three promises:

| Promise | Meaning |
|---------|---------|
| **Speed** | Pages load instantly; actions complete without waiting |
| **Clarity** | The most important information is always visible first |
| **Confidence** | Users trust the data and know what to do next |

### Core Principles

1. **Opinionated and Calm** — One clear way to do things, not endless options
2. **Exceptions First** — Problems surface immediately; healthy shipments fade back
3. **Dense but Scannable** — Logistics users work in data-heavy environments
4. **Purposeful Motion** — Animation shows state change, never decoration
5. **Accessible by Default** — Works in harsh lighting, for colour-blind users, with keyboards

---

## 1. Visual Identity

### Brand Attributes

| Attribute | Expression |
|-----------|------------|
| **Trust** | Professional palette, solid typography, no playfulness |
| **Modernity** | Clean lines, generous whitespace, contemporary icons |
| **Calm Control** | Muted backgrounds, clear hierarchy, no visual noise |

### Colour System

```
┌─────────────────────────────────────────────────────────────────┐
│                     TraceHub Colour Palette                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRIMARY (Action Blue)                                           │
│  ─────────────────────                                           │
│  50:  #EFF6FF   Background tints                                 │
│  100: #DBEAFE   Hover states                                     │
│  500: #3B82F6   Secondary buttons                                │
│  600: #2563EB   Primary buttons, links                           │
│  700: #1D4ED8   Pressed states                                   │
│  900: #1E3A8A   Dark mode primary                                │
│                                                                  │
│  SEMANTIC COLOURS                                                │
│  ───────────────                                                 │
│  Success:  #059669 (Emerald 600) — Completed, compliant          │
│  Warning:  #D97706 (Amber 600)   — Attention needed, pending     │
│  Danger:   #DC2626 (Red 600)     — Blocked, failed, overdue      │
│  Info:     #0891B2 (Cyan 600)    — Informational, tracking       │
│                                                                  │
│  NEUTRAL (Slate)                                                 │
│  ──────────────                                                  │
│  50:  #F8FAFC   Page background                                  │
│  100: #F1F5F9   Card backgrounds, hover                          │
│  200: #E2E8F0   Borders, dividers                                │
│  400: #94A3B8   Placeholder text, disabled                       │
│  500: #64748B   Secondary text, icons                            │
│  700: #334155   Body text                                        │
│  900: #0F172A   Headings, primary text                           │
│                                                                  │
│  DARK MODE (when implemented)                                    │
│  ─────────────────────────────                                   │
│  Background:    #0F172A (Slate 900)                              │
│  Surface:       #1E293B (Slate 800)                              │
│  Border:        #334155 (Slate 700)                              │
│  Text Primary:  #F1F5F9 (Slate 100)                              │
│  Text Secondary: #94A3B8 (Slate 400)                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Colour Usage Rules

| Context | Colour | Usage |
|---------|--------|-------|
| Primary action buttons | Primary 600 | "Create Shipment", "Upload", "Save" |
| Secondary buttons | Slate 100 + Slate 700 text | "Cancel", "Back", filters |
| Destructive actions | Danger 600 | "Delete", "Remove" |
| Success indicators | Success 600 | Checkmarks, "Complete", "Compliant" |
| Warning indicators | Warning 600 | "Pending", "Attention", "Expiring" |
| Error states | Danger 600 | Validation errors, failed uploads |
| Links | Primary 600 | Navigation, inline links |
| Disabled states | Slate 400 + Slate 200 bg | Inactive buttons, unavailable options |

### Accessibility Requirements

- **Contrast ratio:** Minimum 4.5:1 for normal text, 3:1 for large text (WCAG AA)
- **Focus indicators:** 2px solid Primary 600 outline with 2px offset
- **Colour-blind safe:** Never use colour alone to convey meaning; always pair with icons/text
- **Motion sensitivity:** Respect `prefers-reduced-motion` media query

---

## 2. Typography

### Font Stack

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

**Why Inter?** Optimized for screens, excellent legibility at small sizes, professional appearance, variable font support.

### Type Scale

| Name | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| `display` | 36px | 700 | 1.2 | Marketing pages only |
| `h1` | 30px | 700 | 1.25 | Page titles |
| `h2` | 24px | 600 | 1.3 | Section headers |
| `h3` | 20px | 600 | 1.35 | Card titles |
| `h4` | 16px | 600 | 1.4 | Subsections |
| `body-lg` | 16px | 400 | 1.5 | Important body text |
| `body` | 14px | 400 | 1.5 | Default body text |
| `body-sm` | 13px | 400 | 1.5 | Dense tables, secondary |
| `caption` | 12px | 500 | 1.4 | Labels, metadata |
| `overline` | 11px | 600 | 1.3 | Category labels (uppercase) |

### Typography Rules

1. **Page titles:** One H1 per page, always describes the current view
2. **Sentence case:** All headings and buttons use sentence case, not Title Case
3. **Monospace:** Use for reference numbers, container IDs, timestamps
4. **Truncation:** Use ellipsis for overflow; show full text on hover
5. **Line length:** Maximum 75 characters for readable body text

---

## 3. Spacing & Layout

### Spacing Scale (8px base)

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight internal padding |
| `space-2` | 8px | Icon margins, dense lists |
| `space-3` | 12px | Form field gaps |
| `space-4` | 16px | Card padding, section gaps |
| `space-5` | 20px | Medium section separation |
| `space-6` | 24px | Large card padding |
| `space-8` | 32px | Section separation |
| `space-10` | 40px | Major section breaks |
| `space-12` | 48px | Page-level spacing |

### Layout Grid

```
Desktop (1280px+):
┌──────────────────────────────────────────────────────────────────┐
│  Sidebar (240px fixed)  │        Main Content (fluid)            │
│                         │  ┌──────────────────────────────────┐  │
│  Logo                   │  │  Page Header                     │  │
│  ─────────              │  ├──────────────────────────────────┤  │
│  Navigation             │  │                                  │  │
│  • Shipments            │  │  Content Area                    │  │
│  • Documents            │  │  (max-width: 1200px centered)    │  │
│  • Analytics            │  │                                  │  │
│  • Organizations        │  │                                  │  │
│  ─────────              │  │                                  │  │
│  User Menu              │  │                                  │  │
│                         │  └──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘

Tablet (768px - 1279px):
┌──────────────────────────────────────────────────────────────────┐
│  Collapsed Sidebar (64px)  │      Main Content (fluid)          │
│  Icons only                │                                     │
└──────────────────────────────────────────────────────────────────┘

Mobile (<768px):
┌─────────────────────────────┐
│  Top Bar + Hamburger Menu   │
├─────────────────────────────┤
│                             │
│  Full-width Content         │
│                             │
├─────────────────────────────┤
│  Bottom Navigation (fixed)  │
│  4-5 primary destinations   │
└─────────────────────────────┘
```

### Content Width Guidelines

| Content Type | Max Width | Reasoning |
|--------------|-----------|-----------|
| Forms | 640px | Optimal reading width |
| Data tables | 100% | Need full width for columns |
| Detail views | 960px | Balance density and readability |
| Dashboard cards | 1200px | Grid of 3-4 cards per row |

---

## 4. Component Library

### Using shadcn/ui + Radix

We adopt **shadcn/ui** as our component foundation because:
- Accessible by default (Radix primitives)
- Fully customizable (copy-paste, not npm dependency)
- TypeScript-first
- Tailwind-native
- Actively maintained

### Core Components

#### Buttons

```tsx
// Primary - Main actions
<Button>Create shipment</Button>

// Secondary - Supporting actions
<Button variant="secondary">Cancel</Button>

// Destructive - Dangerous actions
<Button variant="destructive">Delete</Button>

// Ghost - Tertiary actions
<Button variant="ghost">Learn more</Button>

// Icon button
<Button variant="ghost" size="icon">
  <RefreshCw className="h-4 w-4" />
</Button>

// Loading state
<Button disabled>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  Uploading...
</Button>
```

**Button Rules:**
- One primary button per view/modal
- Destructive actions require confirmation
- Always show loading state for async actions
- Minimum touch target: 44px × 44px on mobile

#### Status Badges

```tsx
// Shipment status badges
<Badge variant="success">Delivered</Badge>
<Badge variant="warning">In transit</Badge>
<Badge variant="danger">Delayed</Badge>
<Badge variant="info">Customs</Badge>
<Badge variant="secondary">Draft</Badge>

// Document status
<Badge variant="success" className="gap-1">
  <CheckCircle className="h-3 w-3" />
  Validated
</Badge>
```

**Badge Colour Mapping:**

| Status | Variant | Meaning |
|--------|---------|---------|
| Delivered, Compliant, Validated | `success` | No action needed |
| In transit, Processing | `info` | Normal progress |
| Pending, Attention needed | `warning` | User action may be needed |
| Delayed, Failed, Blocked | `danger` | Requires immediate attention |
| Draft, Inactive | `secondary` | Not yet active |

#### Cards

```tsx
// Standard content card
<Card>
  <CardHeader>
    <CardTitle>Shipment TH-2026-0042</CardTitle>
    <CardDescription>Lagos → Rotterdam</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Main content */}
  </CardContent>
  <CardFooter>
    <Button variant="secondary">View details</Button>
  </CardFooter>
</Card>

// Metric card (dashboard)
<Card className="p-6">
  <div className="flex items-center justify-between">
    <div>
      <p className="text-sm text-slate-500">Active shipments</p>
      <p className="text-3xl font-bold text-slate-900">24</p>
    </div>
    <div className="p-3 bg-primary-50 rounded-full">
      <Ship className="h-6 w-6 text-primary-600" />
    </div>
  </div>
  <p className="text-xs text-slate-500 mt-2">
    <span className="text-success-600">+3</span> from last week
  </p>
</Card>
```

#### Data Tables

```tsx
// Shipment list table
<Table>
  <TableHeader>
    <TableRow>
      <TableHead className="w-[120px]">Reference</TableHead>
      <TableHead>Container</TableHead>
      <TableHead>Route</TableHead>
      <TableHead>Status</TableHead>
      <TableHead>ETA</TableHead>
      <TableHead className="text-right">Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow className="cursor-pointer hover:bg-slate-50">
      <TableCell className="font-mono font-medium">TH-2026-0042</TableCell>
      <TableCell className="font-mono">MSCU1234567</TableCell>
      <TableCell>Lagos → Rotterdam</TableCell>
      <TableCell><Badge variant="info">In transit</Badge></TableCell>
      <TableCell>Jan 28, 2026</TableCell>
      <TableCell className="text-right">
        <Button variant="ghost" size="sm">View</Button>
      </TableCell>
    </TableRow>
  </TableBody>
</Table>
```

**Table Design Rules:**
- Sticky header on scroll
- Row hover state (slate-50)
- Clickable rows navigate to detail
- Actions column right-aligned
- Monospace for IDs and references
- Sort indicators on sortable columns

#### Forms

```tsx
// Form field pattern
<div className="space-y-2">
  <Label htmlFor="container">Container number</Label>
  <Input
    id="container"
    placeholder="e.g. MSCU1234567"
    className="font-mono"
  />
  <p className="text-xs text-slate-500">
    11-character ISO container code
  </p>
</div>

// With validation error
<div className="space-y-2">
  <Label htmlFor="email" className="text-danger-600">Email</Label>
  <Input
    id="email"
    className="border-danger-300 focus:ring-danger-500"
    aria-invalid="true"
    aria-describedby="email-error"
  />
  <p id="email-error" className="text-xs text-danger-600">
    Please enter a valid email address
  </p>
</div>
```

**Form Rules:**
- Labels always visible (no placeholder-only fields)
- Helper text below fields
- Errors appear inline, not in toasts
- Group related fields with fieldsets
- Progressive disclosure for advanced options

#### Modals & Dialogs

```tsx
// Confirmation dialog
<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">Delete shipment</Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Delete this shipment?</AlertDialogTitle>
      <AlertDialogDescription>
        This will permanently delete shipment TH-2026-0042 and all
        associated documents. This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction className="bg-danger-600">
        Delete shipment
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

**Modal Rules:**
- Maximum width: 480px for forms, 640px for content
- Focus trapped inside modal
- ESC to close (unless destructive action in progress)
- Backdrop click to close (configurable)
- Stack modals carefully; prefer routing instead

---

## 5. Navigation & Information Architecture

### Primary Navigation

```
┌─────────────────────────────────────────────────────────────────┐
│  TRACEHUB                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📦 Shipments          ← Primary workspace                       │
│  📄 Documents          ← Document management                     │
│  📊 Analytics          ← Reports & insights                      │
│  🏢 Organizations      ← Team & partner management               │
│                                                                  │
│  ─────────────────────                                           │
│                                                                  │
│  ⚙️ Settings           ← Personal & org settings                 │
│  ❓ Help               ← Documentation & support                 │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  👤 Shola Jibodu                                                 │
│  VIBOTAJ · Admin                                                │
│  [Switch organization ▾]                                        │
└─────────────────────────────────────────────────────────────────┘
```

### URL Structure

```
/                           → Redirects to /shipments
/shipments                  → Shipment list
/shipments/new              → Create shipment
/shipments/[id]             → Shipment detail
/shipments/[id]/documents   → Shipment documents tab
/shipments/[id]/tracking    → Shipment tracking tab

/documents                  → All documents across shipments
/documents/[id]             → Document detail/preview

/analytics                  → Dashboard
/analytics/compliance       → Compliance reports
/analytics/performance      → Performance metrics

/organizations              → Organization list (admin)
/organizations/[id]         → Organization detail
/organizations/[id]/members → Member management

/settings                   → User settings
/settings/profile           → Profile settings
/settings/notifications     → Notification preferences
/settings/api               → API keys (if applicable)
```

### Breadcrumbs

```tsx
// Always show context
<Breadcrumb>
  <BreadcrumbItem>
    <BreadcrumbLink href="/shipments">Shipments</BreadcrumbLink>
  </BreadcrumbItem>
  <BreadcrumbSeparator />
  <BreadcrumbItem>
    <BreadcrumbPage>TH-2026-0042</BreadcrumbPage>
  </BreadcrumbItem>
</Breadcrumb>
```

---

## 6. Key Screens & Layouts

### Dashboard (Shipments List)

```
┌─────────────────────────────────────────────────────────────────┐
│  Shipments                                    [+ Create shipment]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ 24 Active   │ │ 3 Attention │ │ 8 In transit│ │ 142 Total  │ │
│  │ shipments   │ │ needed  ⚠️   │ │ 🚢          │ │ this year  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🔍 Search shipments...    [Status ▾] [Date ▾] [Product ▾] │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Reference    Container      Route           Status    ETA │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ TH-2026-0042 MSCU1234567   Lagos→Rotterdam ⚠️ Delayed Jan28│  │
│  │ TH-2026-0041 TCLU7654321   Lagos→Antwerp   🚢 In transit Feb2│  │
│  │ TH-2026-0040 MSKU9876543   Lagos→Hamburg   ✅ Delivered  Jan15│  │
│  │ ...                                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Showing 1-20 of 142                         [← Prev] [Next →]  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Design Notes:**
- Attention card is **red/orange** if there are blocked shipments
- Table rows are clickable → navigate to detail
- Sort by clicking column headers
- Filters persist in URL for shareability

### Shipment Detail

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Shipments / TH-2026-0042                                     │
│                                                                  │
│  ┌────────────────────────────────────────┐ ┌─────────────────┐ │
│  │  Shipment TH-2026-0042                 │ │  Compliance     │ │
│  │  ─────────────────────                 │ │  ─────────────  │ │
│  │  Container: MSCU1234567                │ │  ████████░░ 80% │ │
│  │  B/L Number: MSCULGROT2026001          │ │                 │ │
│  │  Product: Horn & Hoof (HS 0506)        │ │  ⚠️ Missing:    │ │
│  │                                        │ │  • Packing list │ │
│  │  Route                                 │ │                 │ │
│  │  Lagos (NGLOS) → Rotterdam (NLRTM)     │ │  [View all →]   │ │
│  │                                        │ └─────────────────┘ │
│  │  Parties                               │                     │
│  │  Exporter: VIBOTAJ Global              │ ┌─────────────────┐ │
│  │  Buyer: HAGES GmbH                     │ │  Quick Actions  │ │
│  │                                        │ │  ─────────────  │ │
│  │  Timeline                              │ │  📥 Audit pack  │ │
│  │  ETD: Jan 10, 2026 ✓                   │ │  🔄 Sync track  │ │
│  │  ETA: Jan 28, 2026                     │ │  ✏️ Edit        │ │
│  └────────────────────────────────────────┘ └─────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  [📄 Documents (6)]  [🚢 Tracking (12)]  [📋 Validation]    ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │  Documents                                    [+ Upload]    ││
│  │  ──────────                                                 ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           ││
│  │  │ 📄 B/L  │ │ 📄 Inv  │ │ 📄 CoO  │ │ 📄 Vet  │           ││
│  │  │ ✅ Valid│ │ ✅ Valid│ │ ✅ Valid│ │ ⚠️ Exp  │           ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (Shipment List)

```
┌─────────────────────────────┐
│  ☰  Shipments          🔔 2 │
├─────────────────────────────┤
│                             │
│  🔍 Search...               │
│                             │
│  ┌─────────────────────────┐│
│  │  TH-2026-0042           ││
│  │  MSCU1234567            ││
│  │  Lagos → Rotterdam      ││
│  │  ⚠️ Delayed · ETA Jan 28││
│  │                    →    ││
│  └─────────────────────────┘│
│                             │
│  ┌─────────────────────────┐│
│  │  TH-2026-0041           ││
│  │  TCLU7654321            ││
│  │  Lagos → Antwerp        ││
│  │  🚢 In transit · Feb 2  ││
│  │                    →    ││
│  └─────────────────────────┘│
│                             │
├─────────────────────────────┤
│  📦    📄    📊    ⚙️      │
│  Ship  Docs  Stats  More   │
└─────────────────────────────┘
```

---

## 7. Motion & Animation

### Animation Principles

1. **Purposeful:** Every animation communicates a state change
2. **Fast:** Most animations complete in 150-200ms
3. **Subtle:** Users should feel motion, not watch it
4. **Interruptible:** Users can act before animations complete

### Timing Tokens

```css
--duration-instant: 50ms;   /* Micro-interactions */
--duration-fast: 150ms;     /* Buttons, toggles */
--duration-normal: 200ms;   /* Panels, modals */
--duration-slow: 300ms;     /* Page transitions */

--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
```

### Standard Animations

```tsx
// Fade in (new content appearing)
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.2 }}
>

// Slide up (modals, toasts)
<motion.div
  initial={{ opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.2, ease: "easeOut" }}
>

// Scale in (popovers, dropdowns)
<motion.div
  initial={{ opacity: 0, scale: 0.95 }}
  animate={{ opacity: 1, scale: 1 }}
  transition={{ duration: 0.15 }}
>

// Skeleton pulse (loading states)
<div className="animate-pulse bg-slate-200 rounded h-4 w-32" />

// Spinner (indeterminate loading)
<Loader2 className="h-4 w-4 animate-spin" />
```

### Loading States

| Context | Pattern | Duration Threshold |
|---------|---------|-------------------|
| Button action | Inline spinner + disabled | Show after 100ms |
| Page navigation | Skeleton screen | Show immediately |
| Data refresh | Subtle overlay + spinner | Show after 300ms |
| Background sync | Toast notification | Show on complete |

**Skeleton Screen Example:**
```tsx
// Shipment card skeleton
<Card className="animate-pulse">
  <CardHeader>
    <div className="h-5 bg-slate-200 rounded w-32" />
    <div className="h-4 bg-slate-200 rounded w-24 mt-2" />
  </CardHeader>
  <CardContent>
    <div className="h-4 bg-slate-200 rounded w-full" />
    <div className="h-4 bg-slate-200 rounded w-3/4 mt-2" />
  </CardContent>
</Card>
```

---

## 8. Feedback & Notifications

### Toast Notifications

```tsx
// Success toast
toast.success("Shipment created", {
  description: "TH-2026-0043 has been created successfully.",
});

// Error toast
toast.error("Upload failed", {
  description: "The file exceeds the 50MB limit.",
  action: {
    label: "Try again",
    onClick: () => retryUpload(),
  },
});

// Info toast (background action)
toast.info("Syncing tracking data...", {
  duration: Infinity, // Dismiss manually
});
```

**Toast Rules:**
- Success: 3 seconds auto-dismiss
- Error: Persist until dismissed
- Info: Context-dependent duration
- Maximum 3 toasts visible at once
- Stack from bottom-right (desktop) or top (mobile)

### Inline Feedback

```tsx
// Form validation
<Input
  aria-invalid={!!errors.email}
  aria-describedby="email-error"
/>
{errors.email && (
  <p id="email-error" className="text-sm text-danger-600 mt-1">
    {errors.email.message}
  </p>
)}

// Success state in form
<div className="flex items-center gap-2 text-success-600">
  <CheckCircle className="h-4 w-4" />
  <span>Document validated successfully</span>
</div>

// Empty state
<div className="text-center py-12">
  <FileQuestion className="h-12 w-12 text-slate-300 mx-auto" />
  <h3 className="mt-4 text-lg font-medium text-slate-900">
    No documents yet
  </h3>
  <p className="mt-2 text-sm text-slate-500">
    Upload your first document to get started.
  </p>
  <Button className="mt-4">Upload document</Button>
</div>
```

---

## 9. Accessibility Checklist

### Keyboard Navigation

- [ ] All interactive elements are focusable
- [ ] Focus order follows visual order
- [ ] Focus is visible with 2px outline
- [ ] Modals trap focus
- [ ] ESC closes modals/dropdowns
- [ ] Enter activates buttons
- [ ] Arrow keys navigate lists/menus
- [ ] Tab moves between form fields

### Screen Readers

- [ ] All images have alt text
- [ ] Icons have aria-labels or are aria-hidden
- [ ] Form fields have associated labels
- [ ] Errors are announced with aria-live
- [ ] Headings follow hierarchy (h1 → h2 → h3)
- [ ] Tables have proper headers
- [ ] Dynamic content uses aria-live regions

### Visual

- [ ] 4.5:1 contrast for normal text
- [ ] 3:1 contrast for large text
- [ ] No information conveyed by colour alone
- [ ] Focus indicators are visible
- [ ] Touch targets are minimum 44×44px
- [ ] Text can be zoomed to 200%

---

## 10. Implementation Guide

### Technology Stack

```
Next.js 14 (App Router)
├── TypeScript 5.x
├── Tailwind CSS 3.4
├── shadcn/ui (Radix primitives)
├── Framer Motion (animations)
├── Lucide React (icons)
├── React Hook Form + Zod (forms)
├── TanStack Table (data tables)
├── TanStack Query (data fetching)
└── date-fns (date formatting)
```

### Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth layout group
│   │   ├── sign-in/
│   │   └── sign-up/
│   ├── (dashboard)/       # Main app layout group
│   │   ├── shipments/
│   │   ├── documents/
│   │   ├── analytics/
│   │   └── settings/
│   ├── layout.tsx
│   └── globals.css
│
├── components/
│   ├── ui/                # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── layout/            # Layout components
│   │   ├── sidebar.tsx
│   │   ├── header.tsx
│   │   └── mobile-nav.tsx
│   ├── shipments/         # Feature components
│   │   ├── shipment-card.tsx
│   │   ├── shipment-table.tsx
│   │   └── create-shipment-form.tsx
│   ├── documents/
│   └── shared/            # Shared components
│       ├── empty-state.tsx
│       ├── loading-skeleton.tsx
│       └── status-badge.tsx
│
├── lib/
│   ├── api/               # API client
│   ├── utils/             # Utility functions
│   └── validations/       # Zod schemas
│
├── hooks/                 # Custom hooks
│   ├── use-shipments.ts
│   └── use-documents.ts
│
├── types/                 # TypeScript types
│
└── styles/
    └── design-tokens.css  # CSS custom properties
```

### Design Tokens CSS

```css
/* styles/design-tokens.css */

:root {
  /* Colours */
  --color-primary-50: 239 246 255;
  --color-primary-600: 37 99 235;
  --color-primary-700: 29 78 216;

  --color-success-600: 5 150 105;
  --color-warning-600: 217 119 6;
  --color-danger-600: 220 38 38;

  --color-slate-50: 248 250 252;
  --color-slate-900: 15 23 42;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Radii */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);

  /* Animation */
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: var(--color-slate-900);
    --color-foreground: var(--color-slate-50);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 11. Quality Checklist

### Before Every PR

- [ ] Components render correctly at all breakpoints
- [ ] All interactive elements are keyboard accessible
- [ ] Loading and error states are implemented
- [ ] Animations respect reduced motion preference
- [ ] No console errors or warnings
- [ ] TypeScript has no errors
- [ ] Storybook stories are updated (if applicable)

### Before Every Release

- [ ] Lighthouse accessibility score > 90
- [ ] Lighthouse performance score > 80
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)
- [ ] Mobile tested on real devices
- [ ] Screen reader tested with VoiceOver/NVDA
- [ ] All critical user flows tested

---

## 12. Future Considerations

### Dark Mode

- Implement with CSS custom properties
- Use `next-themes` for system preference detection
- Test all components in dark mode
- Ensure sufficient contrast ratios

### Internationalisation

- Use `next-intl` for translations
- Design for text expansion (German ~30% longer)
- Support RTL layouts for Arabic markets
- Date/number formatting with user locale

### White-Labelling

- Expose primary colour as tenant setting
- Support logo replacement
- Allow custom domain per tenant
- Maintain accessibility regardless of brand colours

---

*This design system is a living document. Update it as patterns evolve and new requirements emerge.*

*Document maintained by TraceHub Engineering Team*
