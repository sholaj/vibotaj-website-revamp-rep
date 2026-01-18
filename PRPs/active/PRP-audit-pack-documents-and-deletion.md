# PRP: Audit Pack Document Inclusion & Document Deletion Enhancements

**Status:** Draft
**Priority:** P1 - High
**Sprint:** 16
**Created:** 2026-01-17
**Owner:** Shola

---

## Overview

Enhance the TraceHub audit pack and document management to support compliance review workflows. This PRP addresses two key needs:

1. **Audit Pack Enhancement:** Ensure uploaded documents are clearly included and accessible in the audit pack, with visibility into which documents are included/missing
2. **Document Deletion:** Provide UI for deleting uploaded documents with proper audit trail (backend exists, frontend missing)

### Business Value

- **Compliance Review:** Buyers, compliance officers, and admins can review all uploaded documents before making compliance override decisions
- **Data Quality:** Ability to delete incorrectly uploaded or duplicate documents
- **Audit Readiness:** Complete audit trail of document additions/deletions for regulatory compliance
- **User Confidence:** Clear visibility into what documents are included in shipment packages

---

## Current State Analysis

### What Already Exists

| Feature | Backend | Frontend | Notes |
|---------|---------|----------|-------|
| Audit Pack Download | ✅ `GET /{shipment_id}/audit-pack` | ✅ Download button | **BUG: Documents NOT included due to path error** |
| Document Deletion (Single) | ✅ `DELETE /documents/{id}` | ❌ No UI | Requires `DOCUMENTS_DELETE` permission |
| Document Deletion (Bulk) | ✅ `DELETE /documents/shipment/{id}/all` | ❌ No UI | Admin only |
| Document Preview | ✅ `GET /documents/{id}/download` | ✅ Download button | In DocumentReviewPanel |
| Audit Logging | ✅ `AuditAction.AUDIT_PACK_DOWNLOAD` | ✅ Shows in audit | Tracks downloads |

### Current Audit Pack Contents

| Item | Included | Source |
|------|----------|--------|
| 00-SHIPMENT-INDEX.pdf | ✅ | Generated summary |
| NN-DOCUMENT_TYPE.{ext} | ❌ **BUG** | Path calculation wrong |
| container-tracking-log.json | ✅ | Tracking events |
| metadata.json | ✅ | Shipment data |

### CRITICAL BUG: Documents Not Included in Audit Pack

**Root Cause:** Path mismatch between upload and audit pack generation.

```
Upload saves to:     tracehub/backend/uploads/{shipment_id}/file.pdf
                     (settings.upload_dir = "./uploads")

Audit pack looks in: tracehub/uploads/{shipment_id}/file.pdf
                     (UPLOAD_BASE_DIR goes to tracehub/, missing backend/)
```

**In `audit_pack.py` line 35:**
```python
UPLOAD_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Result: tracehub/ (4 levels up from tracehub/backend/app/services/audit_pack.py)
```

**In `audit_pack.py` line 61:**
```python
full_path = os.path.join(UPLOAD_BASE_DIR, doc.file_path)
# Result: tracehub/./uploads/... instead of tracehub/backend/uploads/...
```

**Fix Required:** Change path resolution in `audit_pack.py`.

### Gap Analysis

1. **CRITICAL BUG:** Documents not included in audit pack due to wrong path
2. **Frontend Document Deletion:** Backend exists but no UI to delete documents
3. **Pre-Download Preview:** No visibility into which documents will be included before download
4. **Missing Document Indicators:** No clear indication if a document file is missing from disk
5. **Deletion Audit Trail UI:** Deletions logged but not visible to users

---

## Requirements

### Functional Requirements

#### FR-1: Document List with Inclusion Status (NEW)
- [ ] Show document list with "Will be included in Audit Pack" indicator
- [ ] Mark documents missing from disk as "File Missing"
- [ ] Show document file size and type
- [ ] Group documents by type matching required document checklist

#### FR-2: Document Deletion UI (NEW)
- [ ] Add delete button to document list (admin/compliance roles only)
- [ ] Require confirmation before deletion
- [ ] Show deletion reason input (required)
- [ ] Display success/error feedback
- [ ] Refresh document list after deletion

#### FR-3: Audit Pack Preview (NEW)
- [ ] Show preview modal before audit pack download
- [ ] List all documents that will be included
- [ ] Warn if any required documents are missing
- [ ] Show estimated ZIP file size
- [ ] Allow proceeding or canceling download

#### FR-4: Document Deletion Audit Trail (ENHANCE)
- [ ] Log deletion with reason to audit trail
- [ ] Include deleted document metadata in log
- [ ] Show recent deletions in audit summary

#### FR-5: Soft Delete Option (FUTURE/OPTIONAL)
- [ ] Mark documents as "archived" instead of hard delete
- [ ] Keep file on disk for 30 days
- [ ] Allow restoration within retention period

### Non-Functional Requirements

#### NFR-1: Performance
- [ ] Document list loads in < 200ms
- [ ] Deletion completes in < 500ms
- [ ] Audit pack preview generates in < 1 second

#### NFR-2: Security
- [ ] Document deletion requires `DOCUMENTS_DELETE` permission
- [ ] Multi-tenancy: Can only delete own organization's documents
- [ ] Audit trail is immutable (append-only)

#### NFR-3: Idempotency
- [ ] All database migrations use `IF NOT EXISTS` / `column_exists()` checks
- [ ] API operations are idempotent where possible
- [ ] Re-running migrations does not cause errors

#### NFR-4: Type Safety
- [ ] All API schemas use Pydantic models
- [ ] Frontend uses TypeScript types from API
- [ ] No `any` types in frontend code

---

## Technical Approach

### TDD Implementation Workflow

All features will be implemented using **Test-Driven Development (TDD)**:

1. **RED:** Write failing test first
2. **GREEN:** Implement minimum code to pass
3. **REFACTOR:** Clean up while keeping tests green

### Phase 0: Fix Critical Bug - Documents Not in Audit Pack (P0)

**Priority:** Must fix FIRST before any other work.

#### 0.1 Write Failing Test

```python
# tests/test_audit_pack.py

def test_audit_pack_includes_uploaded_documents():
    """GIVEN a shipment with uploaded documents
    WHEN audit pack is generated
    THEN documents are included in the ZIP file."""
    # Create shipment
    # Upload document with known file
    # Generate audit pack
    # Assert document file is in ZIP
    # Assert file content matches uploaded file
```

#### 0.2 Fix Path Resolution in audit_pack.py

**Current (broken):**
```python
# tracehub/backend/app/services/audit_pack.py line 35
UPLOAD_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
```

**Fixed:**
```python
# Option 1: Use settings.upload_dir (RECOMMENDED)
from ..config import get_settings
settings = get_settings()

def get_full_path(file_path: str) -> str:
    """Resolve document file path to absolute path."""
    if os.path.isabs(file_path):
        return file_path
    # Relative paths are relative to backend working directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(backend_dir, file_path)
```

**In document loop (line 59-66):**
```python
for i, doc in enumerate(documents, 1):
    if doc.file_path:
        full_path = get_full_path(doc.file_path)  # Use helper function
        if os.path.exists(full_path):
            ext = os.path.splitext(doc.file_name or doc.file_path)[1]
            filename = f"{i:02d}-{doc.document_type.value}{ext}"
            zip_file.write(full_path, filename)
```

#### 0.3 Also Fix in Document Deletion (documents.py)

Check that deletion also uses correct path resolution:

```python
# In delete_document endpoint
if document.file_path:
    full_path = get_full_path(document.file_path)  # Same helper
    if os.path.exists(full_path):
        os.remove(full_path)
```

### Phase 1: Backend API Enhancements

#### 1.1 Document List with Inclusion Status

**New Endpoint:** `GET /api/documents/shipment/{shipment_id}/audit-status`

```python
# app/schemas/documents.py

class DocumentAuditStatus(BaseModel):
    """Document status for audit pack inclusion."""
    id: UUID
    name: str
    document_type: str
    status: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_exists: bool  # True if file is on disk
    will_be_included: bool  # True if will be in audit pack
    missing_reason: Optional[str] = None  # Why not included

    model_config = ConfigDict(from_attributes=True)


class ShipmentAuditStatusResponse(BaseModel):
    """Response for shipment audit status."""
    shipment_id: UUID
    shipment_reference: str
    total_documents: int
    included_count: int
    missing_count: int
    documents: List[DocumentAuditStatus]
    required_document_types: List[str]
    missing_required_types: List[str]

    model_config = ConfigDict(from_attributes=True)
```

**Implementation:**
```python
# app/routers/documents.py

@router.get("/shipment/{shipment_id}/audit-status", response_model=ShipmentAuditStatusResponse)
async def get_shipment_audit_status(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get document audit pack inclusion status for a shipment."""
    shipment = get_accessible_shipment(db, shipment_id, current_user)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    documents = db.query(Document).filter(
        Document.shipment_id == shipment_id
    ).all()

    # Check file existence and build status
    doc_statuses = []
    for doc in documents:
        file_exists = bool(doc.file_path and os.path.exists(
            os.path.join(UPLOAD_BASE_DIR, doc.file_path)
        ))
        doc_statuses.append(DocumentAuditStatus(
            id=doc.id,
            name=doc.name,
            document_type=doc.document_type.value,
            status=doc.status.value,
            file_name=doc.file_name,
            file_size=doc.file_size,
            file_exists=file_exists,
            will_be_included=file_exists,
            missing_reason="File not found on disk" if not file_exists else None
        ))

    # Get required document types for this product type
    required_types = get_required_documents_by_product_type(shipment.product_type)
    present_types = {doc.document_type for doc in documents}
    missing_required = [t.value for t in required_types if t not in present_types]

    return ShipmentAuditStatusResponse(
        shipment_id=shipment.id,
        shipment_reference=shipment.reference,
        total_documents=len(documents),
        included_count=sum(1 for d in doc_statuses if d.will_be_included),
        missing_count=sum(1 for d in doc_statuses if not d.will_be_included),
        documents=doc_statuses,
        required_document_types=[t.value for t in required_types],
        missing_required_types=missing_required
    )
```

#### 1.2 Enhanced Document Deletion

**Existing Endpoint Enhanced:** `DELETE /api/documents/{document_id}`

```python
# app/schemas/documents.py

class DocumentDeleteRequest(BaseModel):
    """Request body for document deletion."""
    reason: str = Field(..., min_length=5, description="Reason for deletion")

    model_config = ConfigDict(from_attributes=True)


class DocumentDeleteResponse(BaseModel):
    """Response for document deletion."""
    success: bool
    message: str
    document_id: UUID
    document_name: str
    deleted_by: str
    deleted_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Enhanced Implementation:**
```python
@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: UUID,
    delete_request: DocumentDeleteRequest,  # Now requires reason
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Delete a document with audit trail.

    Requires: documents:delete permission (admin role)
    """
    check_permission(current_user, Permission.DOCUMENTS_DELETE)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == current_user.organization_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Store metadata before deletion for audit
    doc_metadata = {
        "document_id": str(document.id),
        "document_name": document.name,
        "document_type": document.document_type.value,
        "file_name": document.file_name,
        "shipment_id": str(document.shipment_id),
        "deletion_reason": delete_request.reason
    }

    # Delete file if exists
    if document.file_path:
        full_path = os.path.join(UPLOAD_BASE_DIR, document.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    doc_name = document.name
    db.delete(document)

    # Log deletion to audit trail
    audit_logger.log(
        action="document.delete",
        resource_type="document",
        resource_id=str(document_id),
        username=current_user.email,
        organization_id=str(current_user.organization_id),
        success=True,
        details=doc_metadata,
        db=db
    )

    db.commit()

    return DocumentDeleteResponse(
        success=True,
        message=f"Document '{doc_name}' deleted successfully",
        document_id=document_id,
        document_name=doc_name,
        deleted_by=current_user.email,
        deleted_at=datetime.utcnow()
    )
```

### Phase 2: Frontend Implementation

#### 2.1 Document Audit Status Component

```typescript
// frontend/src/types/index.ts (additions)

export interface DocumentAuditStatus {
  id: string;
  name: string;
  document_type: string;
  status: string;
  file_name: string | null;
  file_size: number | null;
  file_exists: boolean;
  will_be_included: boolean;
  missing_reason: string | null;
}

export interface ShipmentAuditStatusResponse {
  shipment_id: string;
  shipment_reference: string;
  total_documents: number;
  included_count: number;
  missing_count: number;
  documents: DocumentAuditStatus[];
  required_document_types: string[];
  missing_required_types: string[];
}
```

```typescript
// frontend/src/components/AuditPackPreview.tsx

interface AuditPackPreviewProps {
  shipmentId: string;
  onClose: () => void;
  onDownload: () => void;
}

export default function AuditPackPreview({
  shipmentId,
  onClose,
  onDownload,
}: AuditPackPreviewProps) {
  const [status, setStatus] = useState<ShipmentAuditStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAuditStatus();
  }, [shipmentId]);

  const loadAuditStatus = async () => {
    try {
      const data = await api.getShipmentAuditStatus(shipmentId);
      setStatus(data);
    } catch (err) {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  // Render document list with inclusion indicators
  // Show warning if missing required documents
  // Download button proceeds to audit pack download
}
```

#### 2.2 Document Delete Button Component

```typescript
// frontend/src/components/DocumentDeleteButton.tsx

interface DocumentDeleteButtonProps {
  documentId: string;
  documentName: string;
  onDelete: () => void;
}

export default function DocumentDeleteButton({
  documentId,
  documentName,
  onDelete,
}: DocumentDeleteButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!reason.trim() || reason.length < 5) {
      setError('Please provide a deletion reason (at least 5 characters)');
      return;
    }

    try {
      setLoading(true);
      await api.deleteDocument(documentId, reason);
      onDelete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    } finally {
      setLoading(false);
    }
  };

  // Render delete button with confirmation modal
  // Requires reason input before deletion
}
```

### Phase 3: Database Migration (Idempotent)

No new database columns required for this feature. The existing schema supports all functionality.

If future soft-delete is needed:

```python
# alembic/versions/YYYYMMDD_XXXX_add_document_soft_delete.py

"""Add soft delete fields to documents.

IDEMPOTENT: Safe to run multiple times.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Add soft delete fields (idempotent)
    if not column_exists('documents', 'deleted_at'):
        op.add_column(
            'documents',
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )

    if not column_exists('documents', 'deleted_by'):
        op.add_column(
            'documents',
            sa.Column('deleted_by', sa.String(255), nullable=True)
        )

    if not column_exists('documents', 'deletion_reason'):
        op.add_column(
            'documents',
            sa.Column('deletion_reason', sa.String(500), nullable=True)
        )


def downgrade() -> None:
    if column_exists('documents', 'deletion_reason'):
        op.drop_column('documents', 'deletion_reason')
    if column_exists('documents', 'deleted_by'):
        op.drop_column('documents', 'deleted_by')
    if column_exists('documents', 'deleted_at'):
        op.drop_column('documents', 'deleted_at')
```

---

## Files to Modify

### Backend

| File | Changes |
|------|---------|
| `app/services/audit_pack.py` | **BUG FIX** - Fix path resolution for uploaded documents |
| `app/services/file_utils.py` | **NEW** - Shared `get_full_path()` helper |
| `app/schemas/documents.py` | Add `DocumentAuditStatus`, `ShipmentAuditStatusResponse`, `DocumentDeleteRequest`, `DocumentDeleteResponse` |
| `app/routers/documents.py` | Add `GET /shipment/{id}/audit-status`, enhance `DELETE /{id}` with reason, use shared path helper |
| `app/services/audit_log.py` | Add `DOCUMENT_DELETE` action constant |
| `tests/test_audit_pack.py` | **NEW** - TDD tests for audit pack document inclusion |
| `tests/test_documents_audit_status.py` | **NEW** - TDD tests for audit status endpoint |
| `tests/test_documents_deletion.py` | **NEW** - TDD tests for deletion with reason |

### Frontend

| File | Changes |
|------|---------|
| `src/types/index.ts` | Add `DocumentAuditStatus`, `ShipmentAuditStatusResponse` types |
| `src/api/client.ts` | Add `getShipmentAuditStatus()`, update `deleteDocument()` |
| `src/components/AuditPackPreview.tsx` | **NEW** - Audit pack preview modal |
| `src/components/DocumentDeleteButton.tsx` | **NEW** - Delete with confirmation |
| `src/components/DocumentReviewPanel.tsx` | Add delete button |
| `src/pages/Shipment.tsx` | Integrate audit pack preview |

### Database

| File | Changes |
|------|---------|
| None required | Existing schema sufficient |
| Future: `YYYYMMDD_add_document_soft_delete.py` | Optional soft delete fields |

---

## Test Requirements (TDD)

### Backend Unit Tests

```python
# tests/test_documents_audit_status.py

class TestGetShipmentAuditStatus:
    """TDD tests for audit status endpoint."""

    def test_returns_document_list_with_inclusion_status(self):
        """GIVEN shipment with documents
        WHEN GET /shipment/{id}/audit-status
        THEN returns documents with will_be_included flag."""

    def test_marks_missing_files_as_not_included(self):
        """GIVEN document with missing file on disk
        WHEN audit status checked
        THEN file_exists=False and will_be_included=False."""

    def test_lists_missing_required_document_types(self):
        """GIVEN shipment missing required documents
        WHEN audit status checked
        THEN missing_required_types populated."""

    def test_requires_authentication(self):
        """GIVEN unauthenticated request
        WHEN audit status requested
        THEN returns 401."""

    def test_enforces_multi_tenancy(self):
        """GIVEN shipment from different org
        WHEN audit status requested
        THEN returns 404."""


class TestDeleteDocumentWithReason:
    """TDD tests for deletion with reason."""

    def test_requires_deletion_reason(self):
        """GIVEN delete request without reason
        WHEN DELETE called
        THEN returns 422 validation error."""

    def test_logs_deletion_to_audit_trail(self):
        """GIVEN valid delete request
        WHEN document deleted
        THEN audit log entry created with reason."""

    def test_requires_admin_permission(self):
        """GIVEN non-admin user
        WHEN delete attempted
        THEN returns 403."""

    def test_deletes_file_from_disk(self):
        """GIVEN document with file on disk
        WHEN deleted
        THEN file removed from disk."""

    def test_returns_deletion_metadata(self):
        """GIVEN successful deletion
        WHEN response returned
        THEN includes deleted_by and deleted_at."""
```

### Frontend Tests

```typescript
// tests/AuditPackPreview.test.tsx

describe('AuditPackPreview', () => {
  it('shows included document count');
  it('warns when required documents are missing');
  it('shows file missing indicator for documents without files');
  it('calls onDownload when proceed clicked');
});

// tests/DocumentDeleteButton.test.tsx

describe('DocumentDeleteButton', () => {
  it('requires confirmation before delete');
  it('requires reason input (min 5 chars)');
  it('calls API with reason on confirm');
  it('shows error message on failure');
  it('calls onDelete callback on success');
});
```

### Integration Tests

- [ ] Test full flow: View audit status → Delete document → Verify audit log
- [ ] Test audit pack download includes remaining documents
- [ ] Test multi-tenancy isolation for deletion
- [ ] Test cascade deletion of DocumentContent and ComplianceResult

---

## Compliance Check

**Product HS Codes Affected:** None - This is document management, not product-specific
**EUDR Applicable:** N/A - Not product compliance related
**Multi-Tenancy:** ✅ All endpoints filter by organization_id

**Security Considerations:**
- Document deletion requires admin permission
- Deletion reason required for audit compliance
- Audit trail is immutable
- Files deleted from disk cannot be recovered (consider soft delete for future)

---

## Dependencies

### Internal Dependencies
- `app/services/audit_log.py` - Audit logging service (exists)
- `app/services/compliance.py` - Required document types (exists)
- `app/routers/auth.py` - Authentication/authorization (exists)

### External Dependencies
- None - All dependencies are internal

---

## Acceptance Criteria

### Phase 0 (P0 Bug Fix)
- [ ] **Uploaded documents ARE included in audit pack ZIP**
- [ ] Test downloads audit pack and verifies document files present
- [ ] Both staging and production verified working
- [ ] Buyers can see uploaded documents when they download audit pack

### Must Have
- [ ] `GET /shipment/{id}/audit-status` returns document inclusion status
- [ ] Delete requires reason parameter
- [ ] Deletion logged to audit trail with reason
- [ ] Frontend shows delete button for admin users
- [ ] Confirmation required before deletion
- [ ] All Pydantic schemas with `model_config = ConfigDict(from_attributes=True)`
- [ ] All migrations are idempotent

### Should Have
- [ ] Audit pack preview modal before download
- [ ] Missing document warnings in preview
- [ ] File size shown for included documents

### Could Have
- [ ] Soft delete with 30-day retention
- [ ] Bulk delete selected documents
- [ ] Restore deleted documents within retention

### Won't Have (This Sprint)
- [ ] Document versioning
- [ ] External storage (S3) migration

---

## Security Considerations

### Threats
1. **Unauthorized Deletion:** Non-admin users deleting documents
2. **Cross-Tenant Access:** Deleting other organization's documents
3. **Audit Trail Tampering:** Modifying deletion records

### Mitigations
1. **Permission Check:** `check_permission(current_user, Permission.DOCUMENTS_DELETE)`
2. **Multi-Tenancy Filter:** `Document.organization_id == current_user.organization_id`
3. **Immutable Audit:** Audit log uses append-only pattern

### Checklist
- [ ] No hardcoded secrets
- [ ] Input validation (reason min length)
- [ ] SQL injection prevented (SQLAlchemy ORM)
- [ ] Authorization checks in all endpoints
- [ ] Audit trail for all destructive operations

---

## Rollout Plan

### Phase 0: Critical Bug Fix (Immediate - Day 1)
1. Write failing test for audit pack document inclusion
2. Create `app/services/file_utils.py` with `get_full_path()` helper
3. Fix `audit_pack.py` path resolution
4. Fix `documents.py` deletion path resolution
5. Deploy to staging, verify documents appear in audit pack
6. Deploy to production

### Phase 1: Backend Enhancements (Sprint 16 - Week 1)
1. Write failing tests for audit status endpoint
2. Implement `GET /shipment/{id}/audit-status`
3. Write failing tests for deletion enhancement
4. Enhance `DELETE /{id}` with reason requirement
5. All backend tests pass

### Phase 2: Frontend (Sprint 16 - Week 2)
1. Add TypeScript types
2. Implement AuditPackPreview component
3. Implement DocumentDeleteButton component
4. Integrate into DocumentReviewPanel and Shipment page
5. Manual testing on staging

### Phase 3: Integration & Deploy
1. Run full integration tests
2. Deploy to staging
3. UAT with stakeholders
4. Deploy to production
5. Monitor audit logs

### Rollback Plan
- Phase 0 bug fix: Low risk, only changes path calculation
- Revert frontend changes (delete button hidden)
- Backend changes are backward compatible (reason becomes optional if needed)
- No database migration to rollback

---

## Tier Connectivity Verification

### Backend ↔ Database
- [x] Document model has all required fields
- [x] Cascade deletes configured for related records
- [x] Audit log table supports deletion events

### Backend ↔ Frontend
- [x] Pydantic schemas match TypeScript types
- [x] API endpoints return consistent response format
- [x] Error responses follow standard format

### Frontend ↔ User
- [x] Delete button visible only to authorized users
- [x] Confirmation prevents accidental deletion
- [x] Clear feedback on success/failure

---

## Analyst Review Checklist

Before implementation, verify:

- [ ] **Purpose Clear:** Does this PRP solve the stated business need?
- [ ] **Scope Appropriate:** Not too large, not too small for one sprint?
- [ ] **Backend Complete:** All endpoints defined with schemas?
- [ ] **Frontend Complete:** All components and API calls specified?
- [ ] **Database Safe:** Migrations idempotent, no breaking changes?
- [ ] **Tests Defined:** TDD tests cover all new functionality?
- [ ] **Security Reviewed:** Permissions, multi-tenancy, audit trail?
- [ ] **Tiers Connected:** Backend/Frontend/DB changes are consistent?

---

**Last Updated:** 2026-01-17
**Status:** Draft - Pending Review
