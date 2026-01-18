# PRP-020: Add Delete Organization Button to Organization Management

**Status:** Ready for Implementation  
**Priority:** P2 - Medium  
**Sprint:** 17  
**Created:** 2026-01-18  
**Owner:** Shola  

---

## Overview

Add a "Delete" button to the Organization Management page (`/organizations`) to allow administrators to delete organizations. Unlike the user delete feature, the backend endpoint for deleting organizations does NOT exist yet and must be created.

### Business Value
- **Complete Organization Lifecycle:** Admins can remove outdated or test organizations
- **Data Cleanup:** Allow removal of incorrectly created organizations
- **Consistency:** Organization management matches the pattern established for user management

---

## Current State Analysis

### Backend: ❌ NOT IMPLEMENTED

The delete endpoint does NOT exist in `backend/app/routers/organizations.py`:

**Existing Organization Endpoints:**
- `POST /api/organizations` - Create organization ✅
- `GET /api/organizations` - List organizations ✅
- `GET /api/organizations/{org_id}` - Get organization details ✅
- `PATCH /api/organizations/{org_id}` - Update organization ✅
- `DELETE /api/organizations/{org_id}` - Delete organization ❌ **MISSING**

**Existing Member Endpoints:**
- `DELETE /api/organizations/{org_id}/members/{user_id}` - Remove member ✅

### Frontend: ❌ NOT IMPLEMENTED

| Component | Location | Status |
|-----------|----------|--------|
| `OrganizationDeleteModal` | `components/organizations/` | ❌ Needed |
| `api.deleteOrganization()` | `api/client.ts` | ❌ Needed |
| Delete button in Organizations.tsx | `pages/Organizations.tsx` | ❌ Needed |

### Screenshot Analysis

From the attached screenshot of the Organizations page:
- Shows organization list with columns: Organization, Type, Status, Members, Created
- Row click opens detail panel on the right
- **No Delete button present anywhere**

---

## Database Constraints

The database has `RESTRICT` constraints on organization deletion to prevent data loss:

```python
# From migration: 20260106_0006_add_multitenancy_constraints.py
ondelete='RESTRICT'  # Prevent organization deletion if data exists
```

This means:
1. **Cannot delete organizations with:**
   - Active shipments
   - Users assigned (organization_id FK)
   - Active memberships
   
2. **Soft delete is recommended** (set status to "suspended" or "deleted")

---

## Functional Requirements

### FR-1: Backend Delete Endpoint
- [ ] Add `DELETE /api/organizations/{org_id}` endpoint
- [ ] Support soft delete (change status to `suspended`) - default
- [ ] Prevent deletion of VIBOTAJ organization
- [ ] Prevent deletion of organizations with active shipments
- [ ] Require admin permission
- [ ] Accept optional `reason` parameter for audit trail

### FR-2: Add Delete Button to Organization Row
- [ ] Add "Delete" button/icon in organization row or detail panel
- [ ] Button should be red/destructive styling (trash icon)
- [ ] Only visible to users with `SYSTEM_ADMIN` permission
- [ ] Hidden for VIBOTAJ organization (cannot delete self)

### FR-3: Create OrganizationDeleteModal
- [ ] Create new modal component similar to `UserDeleteModal`
- [ ] Require typing organization's slug to confirm
- [ ] Show warning about what will be affected:
  - Number of members that will lose access
  - Note that shipments must be reassigned first if any exist
- [ ] Require deletion reason (minimum 10 characters)

### FR-4: API Client Method
- [ ] Add `deleteOrganization(orgId, reason)` method to `api/client.ts`

---

## Technical Approach

### Backend Implementation

#### Step 1: Add Delete Response Schema

In `backend/app/schemas/organization.py`:

```python
class OrganizationDeleteResponse(BaseModel):
    """Response schema for organization deletion."""
    organization_id: UUID
    name: str
    slug: str
    deleted_at: datetime
    message: str
    members_affected: int
```

#### Step 2: Add Delete Endpoint

In `backend/app/routers/organizations.py`:

```python
@router.delete("/{org_id}", response_model=OrganizationDeleteResponse)
async def delete_organization(
    org_id: UUID,
    reason: str = Query(..., min_length=10, description="Reason for deletion"),
    current_user: CurrentUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete (soft) an organization. Admin only.
    
    - Cannot delete VIBOTAJ organization
    - Cannot delete organizations with active shipments
    - Will deactivate all members
    """
    check_admin_permission(current_user)
    
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Prevent deletion of VIBOTAJ
    if org.type == OrgTypeModel.VIBOTAJ:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete the VIBOTAJ organization"
        )
    
    # Check for active shipments
    from ..models.shipment import Shipment
    shipment_count = db.query(Shipment).filter(
        Shipment.organization_id == org_id
    ).count()
    
    if shipment_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete organization with {shipment_count} shipments. Reassign or delete shipments first."
        )
    
    # Count affected members
    member_count = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.status == MemberStatusModel.ACTIVE
    ).count()
    
    # Soft delete: set status to suspended
    org.status = OrgStatusModel.SUSPENDED
    org.updated_at = datetime.utcnow()
    
    # Deactivate all memberships
    db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id
    ).update({
        OrganizationMembership.status: MemberStatusModel.INACTIVE
    })
    
    db.commit()
    
    return OrganizationDeleteResponse(
        organization_id=org.id,
        name=org.name,
        slug=org.slug,
        deleted_at=datetime.utcnow(),
        message=f"Organization '{org.name}' has been suspended",
        members_affected=member_count
    )
```

### Frontend Implementation

#### Step 3: Add API Client Method

In `frontend/src/api/client.ts`:

```typescript
interface OrganizationDeleteResponse {
  organization_id: string
  name: string
  slug: string
  deleted_at: string
  message: string
  members_affected: number
}

async deleteOrganization(orgId: string, reason: string): Promise<OrganizationDeleteResponse> {
  return this.request<OrganizationDeleteResponse>(
    `organizations/${orgId}?reason=${encodeURIComponent(reason)}`,
    { method: 'DELETE' }
  )
}
```

#### Step 4: Create OrganizationDeleteModal Component

Create `frontend/src/components/organizations/OrganizationDeleteModal.tsx`:

```tsx
interface OrganizationDeleteModalProps {
  organization: {
    id: string
    name: string
    slug: string
    type: OrganizationType
    member_count: number
  }
  isOpen: boolean
  onClose: () => void
  onDeleted: (response: OrganizationDeleteResponse) => void
}

export function OrganizationDeleteModal({ organization, isOpen, onClose, onDeleted }: OrganizationDeleteModalProps) {
  const [confirmSlug, setConfirmSlug] = useState('')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const canDelete = confirmSlug === organization.slug && reason.length >= 10
  
  const handleDelete = async () => {
    if (!canDelete) return
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.deleteOrganization(organization.id, reason)
      onDeleted(response)
      onClose()
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError('Failed to delete organization')
      }
    } finally {
      setLoading(false)
    }
  }
  
  // ... modal UI similar to UserDeleteModal
}
```

#### Step 5: Add Delete Button to Organizations.tsx

Option A: Add in organization row actions (before the chevron):

```tsx
<td className="px-6 py-4 text-right flex items-center justify-end space-x-2">
  {org.type !== 'vibotaj' && (
    <button
      onClick={(e) => {
        e.stopPropagation()
        setOrgToDelete(org)
      }}
      className="text-red-600 hover:bg-red-50 p-1 rounded"
      title="Delete organization"
    >
      <Trash2 className="h-4 w-4" />
    </button>
  )}
  <ChevronRight className="h-5 w-5 text-gray-400" />
</td>
```

Option B: Add in OrganizationDetailPanel (preferred - more context):

```tsx
{/* Add at bottom of detail panel, above close button */}
{orgDetails?.type !== 'vibotaj' && (
  <div className="border-t mt-4 pt-4">
    <button
      onClick={() => setShowDeleteModal(true)}
      className="w-full btn-danger flex items-center justify-center"
    >
      <Trash2 className="h-4 w-4 mr-2" />
      Delete Organization
    </button>
  </div>
)}
```

---

## Testing Requirements

### Backend Tests

In `tests/test_organizations.py`:

```python
def test_delete_organization_success(client, admin_headers, db):
    """Test successful organization deletion."""
    # Create test org
    org = create_test_organization(db, name="Test Org", slug="test-org")
    
    response = client.delete(
        f"/api/organizations/{org.id}?reason=No longer needed for testing",
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test-org"
    assert data["message"].startswith("Organization")
    
def test_delete_organization_vibotaj_forbidden(client, admin_headers, db):
    """Cannot delete VIBOTAJ organization."""
    vibotaj_org = db.query(Organization).filter(Organization.type == "vibotaj").first()
    
    response = client.delete(
        f"/api/organizations/{vibotaj_org.id}?reason=Testing deletion",
        headers=admin_headers
    )
    
    assert response.status_code == 400
    assert "VIBOTAJ" in response.json()["detail"]

def test_delete_organization_with_shipments_forbidden(client, admin_headers, db):
    """Cannot delete organization with active shipments."""
    org = create_test_organization_with_shipments(db)
    
    response = client.delete(
        f"/api/organizations/{org.id}?reason=Testing deletion",
        headers=admin_headers
    )
    
    assert response.status_code == 400
    assert "shipments" in response.json()["detail"].lower()
```

### Manual UI Testing

1. **Navigate to Organizations page**
2. **Click on a non-VIBOTAJ organization** to open detail panel
3. **Verify Delete button is visible** for admin users
4. **Click Delete button** - modal should open
5. **Try to submit without confirmation** - button should be disabled
6. **Type wrong slug** - button should remain disabled
7. **Type correct slug and reason** - button should enable
8. **Submit** - organization should be removed from list
9. **Verify VIBOTAJ org has no delete button**

---

## Security Considerations

1. **Admin Only:** Delete endpoint requires `SYSTEM_ADMIN` permission
2. **Cannot Self-Delete:** VIBOTAJ organization is protected
3. **Data Protection:** Soft delete preserves historical data
4. **Audit Trail:** Reason is logged for compliance
5. **Cascading Prevention:** Must reassign/delete shipments first

---

## Acceptance Criteria

- [ ] Backend `DELETE /api/organizations/{org_id}` endpoint created
- [ ] Endpoint prevents VIBOTAJ deletion
- [ ] Endpoint prevents deletion of orgs with shipments
- [ ] `OrganizationDeleteModal` component created
- [ ] Delete button visible in organization detail panel for non-VIBOTAJ orgs
- [ ] Confirmation requires typing organization slug
- [ ] Deletion reason required (min 10 chars)
- [ ] Organization list refreshes after deletion
- [ ] Success toast/message shown after deletion
- [ ] All backend tests pass
- [ ] UI tested in Chrome

---

## Files to Modify

### Backend
| File | Changes |
|------|---------|
| `backend/app/routers/organizations.py` | Add DELETE endpoint |
| `backend/app/schemas/organization.py` | Add OrganizationDeleteResponse |
| `backend/tests/test_organizations.py` | Add delete tests |

### Frontend
| File | Changes |
|------|---------|
| `frontend/src/api/client.ts` | Add deleteOrganization method |
| `frontend/src/components/organizations/OrganizationDeleteModal.tsx` | NEW: Delete modal |
| `frontend/src/components/organizations/index.ts` | Export new modal |
| `frontend/src/pages/Organizations.tsx` | Add delete button and modal integration |
| `frontend/src/types/index.ts` | Add OrganizationDeleteResponse type |

---

## Estimated Effort

| Task | Estimate |
|------|----------|
| Backend endpoint + tests | 1 hour |
| Frontend modal component | 1 hour |
| Integration in Organizations page | 30 min |
| Testing | 30 min |
| **Total** | **3 hours** |

---

## Dependencies

- None (self-contained feature)

---

## Out of Scope

- Hard delete (permanently remove from database) - may be added later
- Bulk delete organizations
- Organization archiving feature
- Organization transfer (move shipments to another org before delete)
