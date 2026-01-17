# PRP-017: Multi-Tenancy Hardening & API Response Refactoring

## Status: ✅ COMPLETE (All Phases - 2026-01-17)
## Priority: P0 (Security)
## Sprint: 13
## Created: 2026-01-16

---

## Problem Statement

Recent bugs have exposed systemic issues with multi-tenancy implementation:

1. **Missing `organization_id`** when creating entities (Products, Documents)
2. **Missing tenant filters** in database queries (security vulnerability)
3. **Manual dict building** in API responses causing forgotten fields
4. **No centralized entity creation** - multiple code paths create same entities

### Recent Incidents

| Date | Bug | Root Cause |
|------|-----|------------|
| 2026-01-16 | Document upload 500 error | Product creation missing `organization_id` |
| 2026-01-16 | Wrong document requirements | `get_required_documents()` not using `product_type` |
| 2026-01-16 | EUDR card showing for Horn/Hoof | API response missing `product_type` field |

---

## Audit Findings

### 1. Security: Missing Organization Filters (HIGH PRIORITY)

**File: `documents.py`** - 6 vulnerable endpoints

| Line | Endpoint | Issue |
|------|----------|-------|
| 131 | `POST /documents/upload` | Shipment lookup missing org filter |
| 850 | `GET /documents/expiring` | Global query, no org filter |
| 887 | `GET /documents/workflow/summary` | Shipment lookup missing org filter |
| 1361 | `POST /documents/{id}/extract` | Shipment lookup missing org filter |
| 1439 | `POST /documents/{id}/preview-extraction` | Shipment lookup missing org filter |
| 1553 | `POST /documents/{id}/bol/parse` | Shipment lookup missing org filter |
| 1678 | `POST /documents/{id}/bol/check-compliance` | Shipment lookup missing org filter |
| 1832 | `POST /documents/{id}/bol/sync-preview` | Shipment lookup missing org filter |
| 1904 | `POST /documents/{id}/bol/sync` | Shipment lookup missing org filter |

**File: `eudr.py`** - 2 timing issues

| Line | Endpoint | Issue |
|------|----------|-------|
| 393 | `POST /eudr/origin/{id}/verify` | Direct origin query before org check |
| 505 | `GET /eudr/origin/{id}/risk` | Direct origin query before org check |

### 2. Manual Dict Building (causes forgotten fields)

| File | Line | Pattern | Status |
|------|------|---------|--------|
| `shipments.py` | 262 | `shipment_dict = {` - 30+ fields manually listed | ✅ Fixed - uses model_validate() |
| `documents.py` | 346 | `response = {` | N/A - custom API response |
| `documents.py` | 481 | `response = {` | N/A - custom API response |
| `documents.py` | 1561 | `response = {` | N/A - custom API response |
| `documents.py` | 1692 | `response = {` | N/A - custom API response |

### 3. Entity Creation Points (need `organization_id`)

| File | Line | Entity | Status |
|------|------|--------|--------|
| `main.py` | 104 | Product | ✅ Has org_id |
| `shipment_enrichment.py` | 304 | Product | ✅ Fixed 2026-01-16 |
| `shipments.py` | Various | Shipment | ✅ OK |
| `documents.py` | Various | Document | ✅ OK |

---

## Solution Design

### Phase 1: Security Fixes (Immediate)

Fix all missing `organization_id` filters in database queries.

**Pattern to apply:**
```python
# BEFORE (vulnerable)
shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()

# AFTER (secure)
shipment = db.query(Shipment).filter(
    Shipment.id == shipment_id,
    Shipment.organization_id == current_user.organization_id
).first()
```

**Files to update:**
- [x] `documents.py` - 9 locations (verified 2026-01-17 - all have org filters)
- [x] `eudr.py` - 2 locations (verified 2026-01-17 - use secure JOIN queries)

### Phase 2: Pydantic Response Models

Replace manual dict building with Pydantic model serialization.

**Current Problem:**
```python
# Manual dict - easy to forget fields
shipment_dict = {
    "id": shipment.id,
    "reference": shipment.reference,
    # ... 30 more fields, easy to miss one
}
```

**Solution - Use Pydantic's `model_validate`:**
```python
# Automatic serialization - all fields included
from pydantic import ConfigDict

class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reference: str
    product_type: Optional[ProductType] = None
    # ... all fields defined once in schema

# In router:
return ShipmentResponse.model_validate(shipment)
```

**Benefits:**
- All fields automatically included
- Type validation
- OpenAPI schema generation
- Single source of truth for response shape

**Files to update:**
- [x] `backend/app/schemas/shipment.py` - Add `from_attributes` config + Field aliases ✅
- [x] `backend/app/routers/shipments.py` - Use `model_validate()` ✅
- [x] `backend/app/routers/documents.py` - Reviewed: response dicts are custom API responses, not ORM serializations ✅

### Phase 3: Service Layer for Entity Creation ✅ Complete

Create centralized factory functions that always set required fields.

**Status:** Implemented 2026-01-17
- [x] Created `entity_factory.py` with `create_product()` and `create_document()`
- [x] Refactored `main.py` to use `create_product()`
- [x] Refactored `shipment_enrichment.py` to use `create_product()`
- [x] Refactored `documents.py` to use `create_document()`

**New file: `backend/app/services/entity_factory.py`**

```python
"""
Centralized entity creation with required fields.
Always use these functions instead of direct Model() instantiation.
"""
from uuid import UUID
from ..models import Product, Document, Shipment

def create_product(
    shipment: Shipment,
    hs_code: str,
    description: str,
    **kwargs
) -> Product:
    """Create a Product with all required fields."""
    return Product(
        shipment_id=shipment.id,
        organization_id=shipment.organization_id,  # Always set
        hs_code=hs_code,
        description=description,
        **kwargs
    )

def create_document(
    shipment: Shipment,
    document_type: DocumentType,
    name: str,
    file_path: str,
    **kwargs
) -> Document:
    """Create a Document with all required fields."""
    return Document(
        shipment_id=shipment.id,
        organization_id=shipment.organization_id,  # Always set
        document_type=document_type,
        name=name,
        file_path=file_path,
        status=DocumentStatus.UPLOADED,
        **kwargs
    )
```

**Usage:**
```python
# BEFORE
product = Product(
    shipment_id=shipment.id,
    # Easy to forget organization_id!
    hs_code=hs_code,
)

# AFTER
from app.services.entity_factory import create_product
product = create_product(shipment, hs_code=hs_code, description=desc)
```

---

## Implementation Plan

### Sprint 13 - Week 1

| Task | Est. Hours | Owner |
|------|------------|-------|
| Phase 1: Fix 11 missing org filters | 2h | - |
| Add integration tests for tenant isolation | 2h | - |
| Phase 2: Update Pydantic schemas | 3h | - |
| Phase 2: Refactor shipments.py responses | 2h | - |
| Phase 2: Refactor documents.py responses | 3h | - |

### Sprint 13 - Week 2

| Task | Est. Hours | Owner |
|------|------------|-------|
| Phase 3: Create entity_factory.py | 1h | - |
| Phase 3: Refactor all Product creation | 1h | - |
| Phase 3: Refactor all Document creation | 2h | - |
| Update CLAUDE.md with new patterns | 1h | - |
| Documentation & code review | 2h | - |

**Total Estimated: 19 hours**

---

## Testing Requirements

### Security Tests (New)

```python
# tests/test_multi_tenancy_security.py

def test_cannot_upload_document_to_other_org_shipment(client, org_a_user, org_b_shipment):
    """Users cannot upload documents to shipments from other organizations."""
    response = client.post(
        f"/api/documents/upload",
        data={"shipment_id": str(org_b_shipment.id)},
        files={"file": ("test.pdf", b"content", "application/pdf")},
        headers={"Authorization": f"Bearer {org_a_user.token}"}
    )
    assert response.status_code == 404  # Not 500, not 200

def test_expiring_documents_only_shows_own_org(client, org_a_user, org_b_document):
    """Users only see expiring documents from their organization."""
    response = client.get(
        "/api/documents/expiring",
        headers={"Authorization": f"Bearer {org_a_user.token}"}
    )
    doc_ids = [d["id"] for d in response.json()]
    assert str(org_b_document.id) not in doc_ids
```

### Response Schema Tests

```python
def test_shipment_response_includes_product_type(client, auth_headers, horn_hoof_shipment):
    """Shipment response must include product_type field."""
    response = client.get(f"/api/shipments/{horn_hoof_shipment.id}", headers=auth_headers)
    data = response.json()
    assert "product_type" in data["shipment"]
    assert data["shipment"]["product_type"] == "horn_hoof"
```

---

## Files Changed

### Modified
- `backend/app/routers/documents.py` - Security fixes + Pydantic responses
- `backend/app/routers/shipments.py` - Pydantic responses
- `backend/app/routers/eudr.py` - Security fixes
- `backend/app/schemas/shipment.py` - Add `from_attributes` config
- `backend/app/schemas/document.py` - Add `from_attributes` config
- `CLAUDE.md` - Update patterns documentation

### New
- `backend/app/services/entity_factory.py` - Centralized entity creation
- `backend/tests/test_multi_tenancy_security.py` - Security tests

---

## Success Criteria

1. **Zero cross-tenant data access** - All queries filter by organization_id
2. **No manual dict building** - All API responses use Pydantic models
3. **Single entity creation path** - All entities created via factory functions
4. **100% test coverage** for tenant isolation scenarios
5. **Updated documentation** in CLAUDE.md

---

## Rollback Plan

All changes are backwards compatible. If issues arise:
1. Revert to previous commit
2. No database migrations required
3. No API contract changes (responses include same/more fields)

---

## References

- [CLAUDE.md Multi-Tenancy Section](/CLAUDE.md#multi-tenancy-implementation---important)
- [ADR-008 Multi-Tenancy Architecture](/tracehub/docs/architecture/ADR-008-multi-tenancy-architecture.md)
- [Sprint 8 Multi-Tenancy Migration](/tracehub/docs/sprints/sprint-8/)
