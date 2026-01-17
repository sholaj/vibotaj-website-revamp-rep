# TraceHub Frontend Components

> Component API documentation for TraceHub React frontend

---

## Component Hierarchy

```
App
├── AuthProvider (context)
│   └── AppRoutes
│       ├── Login (lazy)
│       ├── AcceptInvitation (lazy)
│       └── Layout
│           ├── NotificationBell
│           └── Outlet
│               ├── Dashboard (lazy)
│               │   ├── CreateShipmentModal
│               │   ├── EditShipmentModal
│               │   └── DeleteConfirmationModal
│               ├── Shipment (lazy)
│               │   ├── DocumentList
│               │   │   └── DocumentContents
│               │   ├── DocumentUploadModal
│               │   ├── DocumentReviewPanel
│               │   ├── ShipmentValidationPanel
│               │   ├── BolCompliancePanel
│               │   ├── ComplianceStatus
│               │   ├── EUDRStatusCard
│               │   ├── OriginVerificationForm
│               │   ├── TrackingTimeline
│               │   └── ContainerSuggestion
│               ├── Analytics (lazy)
│               ├── Users (lazy)
│               │   └── PermissionGuard
│               └── Organizations (lazy)
```

---

## Core Components

### Layout

Main application shell with navigation, header, and content area.

**Props:**
```typescript
interface LayoutProps {
  onLogout: () => void
}
```

**Usage:**
```tsx
<Layout onLogout={() => logout()} />
```

---

### PermissionGuard

Conditionally renders children based on user permissions or roles. Essential for role-based access control.

**Props:**
```typescript
interface PermissionGuardProps {
  children: React.ReactNode
  /** Single permission to check */
  permission?: PermissionKey
  /** Multiple permissions to check */
  permissions?: PermissionKey[]
  /** Single role to check */
  role?: UserRole
  /** Multiple roles - any match allows access */
  roles?: UserRole[]
  /** If true, all permissions required; false = any one (default: true) */
  requireAll?: boolean
  /** What to render if denied (default: null) */
  fallback?: React.ReactNode
  /** Show "no access" message instead of hiding */
  showDenied?: boolean
}
```

**Usage:**
```tsx
// Single permission
<PermissionGuard permission="documents:validate">
  <ValidateButton />
</PermissionGuard>

// Multiple roles (any match)
<PermissionGuard roles={['admin', 'compliance']}>
  <AdminPanel />
</PermissionGuard>

// Multiple permissions (any match)
<PermissionGuard permissions={['documents:read', 'documents:update']} requireAll={false}>
  <EditButton />
</PermissionGuard>

// With fallback
<PermissionGuard permission="users:manage" fallback={<ReadOnlyView />}>
  <EditableView />
</PermissionGuard>
```

---

## Document Components

### DocumentUploadModal

Modal for uploading documents to a shipment with drag & drop support.

**Props:**
```typescript
interface DocumentUploadModalProps {
  shipmentId: string
  isOpen: boolean
  onClose: () => void
  onUploadComplete: () => void
}
```

**Usage:**
```tsx
<DocumentUploadModal
  shipmentId="123"
  isOpen={showUpload}
  onClose={() => setShowUpload(false)}
  onUploadComplete={() => refetchDocuments()}
/>
```

**Supported Document Types:**
- Bill of Lading
- Commercial Invoice
- Packing List
- Certificate of Origin
- Phytosanitary/Sanitary Certificate
- EU TRACES Certificate (Horn & Hoof)
- Veterinary Health Certificate
- EUDR Due Diligence
- And more...

---

### DocumentList

Displays list of documents with status badges and actions.

**Props:**
```typescript
interface DocumentListProps {
  shipmentId: string
  documents: Document[]
  onDocumentSelect?: (doc: Document) => void
  onRefresh: () => void
}
```

---

### DocumentContents

Displays extracted/validated content from a document.

**Props:**
```typescript
interface DocumentContentsProps {
  documentId: string
  documentType: DocumentType
}
```

---

### DocumentReviewPanel

Panel for reviewing and validating document content with AI-extracted data.

**Props:**
```typescript
interface DocumentReviewPanelProps {
  documentId: string
  onValidationComplete?: () => void
  isReadOnly?: boolean
}
```

---

## Compliance Components

### ShipmentValidationPanel

Displays validation status for a shipment with rule results.

**Props:**
```typescript
interface ShipmentValidationPanelProps {
  shipmentId: string
  onValidationComplete?: (report: ShipmentValidationReport) => void
  isAdmin?: boolean
}
```

**Features:**
- Overall status badge (valid/invalid)
- Summary stats (passed, failed, warnings)
- Individual rule results by category
- Admin override functionality

**Usage:**
```tsx
<ShipmentValidationPanel
  shipmentId="123"
  onValidationComplete={(report) => console.log(report)}
  isAdmin={user.role === 'admin'}
/>
```

---

### BolCompliancePanel

Bill of Lading compliance verification panel.

**Props:**
```typescript
interface BolCompliancePanelProps {
  shipmentId: string
  bolDocumentId?: string
}
```

---

### ComplianceStatus

Badge/indicator showing compliance status for a shipment.

**Props:**
```typescript
interface ComplianceStatusProps {
  status: 'compliant' | 'non_compliant' | 'pending' | 'not_applicable'
  showLabel?: boolean
}
```

---

### EUDRStatusCard

Card showing EUDR compliance status and requirements.

**Props:**
```typescript
interface EUDRStatusCardProps {
  shipmentId: string
  productType: ProductType
}
```

**Note:** Returns "Not Applicable" for Horn & Hoof products (HS 0506/0507).

---

## Shipment Components

### CreateShipmentModal

Modal for creating new shipments.

**Props:**
```typescript
interface CreateShipmentModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated: (shipment: Shipment) => void
}
```

---

### EditShipmentModal

Modal for editing existing shipment details.

**Props:**
```typescript
interface EditShipmentModalProps {
  shipment: Shipment
  isOpen: boolean
  onClose: () => void
  onUpdated: (shipment: Shipment) => void
}
```

---

### DeleteConfirmationModal

Generic confirmation modal for destructive actions.

**Props:**
```typescript
interface DeleteConfirmationModalProps {
  isOpen: boolean
  title: string
  message: string
  itemName?: string
  onConfirm: () => void
  onCancel: () => void
  isLoading?: boolean
}
```

**Usage:**
```tsx
<DeleteConfirmationModal
  isOpen={showDelete}
  title="Delete Shipment"
  message="Are you sure you want to delete this shipment?"
  itemName={shipment.reference}
  onConfirm={handleDelete}
  onCancel={() => setShowDelete(false)}
  isLoading={isDeleting}
/>
```

---

## Tracking Components

### TrackingTimeline

Displays container tracking events as a vertical timeline.

**Props:**
```typescript
interface TrackingTimelineProps {
  shipmentId: string
  events?: TrackingEvent[]
}
```

---

### ContainerSuggestion

Suggests container numbers based on partial input.

**Props:**
```typescript
interface ContainerSuggestionProps {
  value: string
  onSelect: (containerNumber: string) => void
}
```

---

## Origin Components

### OriginVerificationForm

Form for verifying product origin with geolocation data.

**Props:**
```typescript
interface OriginVerificationFormProps {
  originId: string
  productType: ProductType
  onVerified?: () => void
}
```

**Note:** Hides geolocation fields for Horn & Hoof products (not covered by EUDR).

---

## Utility Components

### NotificationBell

Notification icon with badge count and dropdown.

**Props:**
```typescript
// No props - uses AuthContext internally
```

---

## Design Tokens

See `FRONTEND_QUICK_REFERENCE.md` for:
- Color palette (primary, success, warning, danger)
- Typography scale
- Spacing system
- Button variants
- Form input styles

---

## State Management

Components use these context providers:
- **AuthContext** - User auth state, permissions, role checking
- Local state with `useState` for component-specific UI state
- Server state via API client functions

---

## Common Patterns

### Loading States
```tsx
{isLoading ? (
  <div className="animate-pulse">
    <div className="h-6 bg-gray-200 rounded" />
  </div>
) : (
  <ActualContent />
)}
```

### Error Handling
```tsx
{error && (
  <div className="flex items-center text-danger-600 bg-danger-50 p-3 rounded">
    <AlertCircle className="h-4 w-4 mr-2" />
    <span>{error}</span>
  </div>
)}
```

### Modal Pattern
```tsx
{isOpen && (
  <div className="fixed inset-0 z-50">
    <div className="fixed inset-0 bg-black/50" onClick={onClose} />
    <div className="relative bg-white rounded-lg shadow-xl">
      {/* Modal content */}
    </div>
  </div>
)}
```
