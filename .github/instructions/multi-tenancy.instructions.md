---
applyTo: "**/routers/**,**/services/**,**/models/**,**/schemas/**"
---

# Multi-Tenancy Rules

All data in TraceHub is scoped to an organization. Defense-in-depth: application-level filtering + Supabase RLS.

## Application-Level (Mandatory)

Every database query MUST include `organization_id` filtering. No exceptions.

### SQLAlchemy Pattern (v1 backend)

```python
# CORRECT — always filter by org
shipments = db.query(Shipment).filter(
    Shipment.organization_id == current_user.organization_id
).all()

# WRONG — returns data across tenants
shipments = db.query(Shipment).all()
```

### Supabase Pattern (v2)

```python
# CORRECT — RLS handles filtering, but application code still scopes
response = supabase.table("shipments").select("*").eq(
    "organization_id", user.org_id
).execute()
```

## Supabase RLS (v2 Defense-in-Depth)

Every table with tenant data must have RLS policies:

```sql
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tenant_isolation" ON shipments
  USING (organization_id = auth.jwt() ->> 'org_id');
```

## Tables That MUST Be Tenant-Scoped

- `shipments` — organization_id (FK)
- `documents` — via shipment.organization_id
- `containers` — via shipment.organization_id
- `compliance_records` — via shipment.organization_id
- `members` / `invitations` — organization_id (FK)

## Tables That Are Global

- `organizations` — top-level entity
- `users` — may belong to multiple orgs (via members)
- `roles` / `permissions` — system-wide definitions

## Router Pattern

```python
from app.routers.auth import get_current_active_user
from app.schemas.user import CurrentUser

@router.get("/{id}")
async def get_resource(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    resource = db.query(Model).filter(
        Model.id == id,
        Model.organization_id == current_user.organization_id
    ).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Not found")
    return resource
```

## Anti-Patterns

- NEVER query without org filter, even in admin endpoints
- NEVER pass organization_id from the frontend — derive from auth token
- NEVER allow cross-tenant joins without explicit admin authorization
- NEVER expose internal org IDs in URLs — use org slugs in v2
