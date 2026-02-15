# PRD-007: OpenAPI → Hey API Type Bridge

**Status:** Specified
**Complexity:** Medium
**Target:** Week 4
**Dependencies:** PRD-001 (Next.js frontend — generated client destination), PRD-004 (FastAPI on Railway — OpenAPI source)
**Branch:** `feature/prd-007-openapi-type-bridge`

---

## Problem

v1 has a manually-written 1,777-line Axios API client (`tracehub/frontend/src/api/client.ts`) with ~100 type imports, a custom `SimpleCache`, retry logic, and comprehensive endpoint coverage. This client drifts from backend schemas — when a Pydantic model changes, the TypeScript types must be manually updated. No build-time validation catches mismatches. The client also embeds business logic (token refresh, cache invalidation patterns) that couples it tightly to the Axios implementation.

## Acceptance Criteria

1. FastAPI generates clean OpenAPI 3.1 spec at `/openapi.json`
2. Pydantic v2 models produce accurate JSON Schema in the spec (no `Any` types, correct optionals)
3. Hey API generates TypeScript client with:
   - Typed request/response functions for every endpoint
   - Zod schemas for runtime validation at API boundaries
   - Proper handling of `UUID`, `datetime`, enum, and nullable types
4. Generated code output at `v2/frontend/src/lib/api/`
5. CI script auto-regenerates client on backend changes (pre-commit or GitHub Action)
6. Zero `any` types in generated output — strict TypeScript
7. Authentication header injection via Hey API plugin (PropelAuth token)
8. Mapping document: v1 client methods → v2 generated functions
9. Custom hooks layer on top of generated client for React Query integration

## Technical Approach

### 1. OpenAPI Spec Cleanup

FastAPI auto-generates OpenAPI, but it needs cleanup for clean codegen:

```python
# Ensure all Pydantic models have explicit titles and descriptions
class ShipmentResponse(BaseModel):
    """Shipment with full details."""
    model_config = ConfigDict(json_schema_extra={"title": "ShipmentResponse"})

# Ensure all routers have proper tags
@router.get("/shipments", tags=["shipments"], response_model=list[ShipmentResponse])

# Ensure all path parameters and query parameters have descriptions
@router.get("/shipments/{shipment_id}")
async def get_shipment(
    shipment_id: Annotated[UUID, Path(description="The shipment's UUID")],
):
```

Key checks:
- No duplicate operation IDs
- All response models specified (no raw dicts)
- Proper HTTP status codes on all endpoints
- File upload endpoints use correct `multipart/form-data` spec

### 2. Hey API Configuration

```typescript
// v2/frontend/openapi-ts.config.ts
import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  client: '@hey-api/client-fetch',
  input: 'http://localhost:8000/openapi.json',  // or path to spec file
  output: {
    path: 'src/lib/api/generated',
    format: 'prettier',
    lint: 'eslint',
  },
  plugins: [
    '@hey-api/typescript',           // Type generation
    '@hey-api/schemas',              // Zod runtime schemas
    {
      name: '@hey-api/sdk',          // SDK functions
      asClass: false,                // Functional style, not class
      operationId: true,             // Use operationId for function names
    },
  ],
});
```

### 3. Generated Output Structure

```
v2/frontend/src/lib/api/
  generated/
    index.ts                 # Re-exports
    types.gen.ts             # TypeScript interfaces from Pydantic models
    schemas.gen.ts           # Zod schemas for runtime validation
    sdk.gen.ts               # Typed API functions
  client.ts                  # Hey API client instance with auth + base URL
  hooks/
    use-shipments.ts         # React Query wrapper: useShipments(), useShipment()
    use-documents.ts         # React Query wrapper: useDocuments(), useDocument()
    use-organizations.ts     # React Query wrapper: useOrganizations()
    use-auth.ts              # React Query wrapper: useCurrentUser()
    index.ts                 # Re-exports
```

### 4. Client Instance with Auth

```typescript
// v2/frontend/src/lib/api/client.ts
import { createClient } from '@hey-api/client-fetch';

export const apiClient = createClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL,
});

// Auth interceptor — injects PropelAuth token
apiClient.interceptors.request.use((request) => {
  const token = getAccessToken();  // From PropelAuth (PRD-003)
  if (token) {
    request.headers.set('Authorization', `Bearer ${token}`);
  }
  return request;
});
```

### 5. React Query Integration Layer

```typescript
// v2/frontend/src/lib/api/hooks/use-shipments.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getShipments, getShipment, createShipment } from '../generated';

export function useShipments(params?: GetShipmentsParams) {
  return useQuery({
    queryKey: ['shipments', params],
    queryFn: () => getShipments({ query: params }),
  });
}

export function useCreateShipment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createShipment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shipments'] });
    },
  });
}
```

### 6. CI/CD Auto-Regeneration

```yaml
# .github/workflows/generate-api-client.yml
name: Generate API Client
on:
  push:
    paths:
      - 'tracehub/backend/app/schemas/**'
      - 'tracehub/backend/app/routers/**'
    branches: [main]

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start FastAPI
        run: |
          cd tracehub/backend
          pip install -r requirements.txt
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 5
      - name: Generate client
        run: |
          cd v2/frontend
          npm install
          npx @hey-api/openapi-ts
      - name: Check for changes
        run: |
          git diff --exit-code v2/frontend/src/lib/api/generated/ || {
            git add v2/frontend/src/lib/api/generated/
            git commit -m "chore(api): regenerate TypeScript client from OpenAPI spec"
            git push
          }
```

### 7. v1 → v2 Method Mapping

Document mapping for every v1 client method to its v2 generated equivalent:

| v1 Method | v2 Generated Function | Notes |
|-----------|----------------------|-------|
| `api.login(email, password)` | `postApiAuthLogin({ body })` | Auth moves to PropelAuth |
| `api.getShipments(params)` | `getApiShipments({ query })` | Direct mapping |
| `api.getShipment(id)` | `getApiShipmentsShipmentId({ path })` | Direct mapping |
| `api.uploadDocument(shipmentId, file)` | `postApiDocumentsUpload({ body })` | Multipart form |
| ... | ... | Full mapping in separate doc |

## Files to Create/Modify

```
v2/frontend/
  openapi-ts.config.ts            # NEW: Hey API configuration
  package.json                     # MODIFY: add @hey-api/*, @tanstack/react-query, zod
  src/lib/api/
    generated/                     # NEW: Auto-generated (gitignored except types)
      index.ts
      types.gen.ts
      schemas.gen.ts
      sdk.gen.ts
    client.ts                      # NEW: Client instance with auth interceptor
    hooks/
      use-shipments.ts             # NEW: React Query hooks
      use-documents.ts
      use-organizations.ts
      use-auth.ts
      index.ts
tracehub/backend/app/
  routers/*.py                     # AUDIT: ensure operation_id, tags, response_model on all endpoints
  schemas/*.py                     # AUDIT: ensure no Any types, proper Optional handling
.github/workflows/
  generate-api-client.yml          # NEW: CI pipeline for auto-regeneration
docs/
  api-client-mapping.md            # NEW: v1 → v2 method mapping reference
```

## v1 Source of Truth

| v1 File | What to Reference |
|---------|------------------|
| `tracehub/frontend/src/api/client.ts` (1,777 lines) | All endpoint methods, types, caching patterns, retry logic |
| `tracehub/backend/app/routers/*.py` (13 routers) | All API endpoints — source for OpenAPI spec |
| `tracehub/backend/app/schemas/*.py` | All Pydantic models — source for TypeScript types |
| `tracehub/backend/app/main.py` | Router mounts, tags, OpenAPI metadata |

## Testing Strategy

- OpenAPI spec validates against OpenAPI 3.1 schema (use `openapi-spec-validator`)
- Generated TypeScript compiles with zero errors (`npx tsc --noEmit`)
- Zero `any` types in generated output (`grep -r "any" generated/` returns nothing)
- Generated Zod schemas validate sample API responses correctly
- React Query hooks return correctly typed data
- CI pipeline: spec change → regeneration → commit (end-to-end)
- Mapping doc covers 100% of v1 client methods

## Migration Notes

- v1 Axios client at `tracehub/frontend/src/api/client.ts` is untouched — v2 uses generated client
- v1 retry logic (3 retries, exponential backoff) moves to Hey API client interceptor or React Query config
- v1 `SimpleCache` (1-minute TTL) is replaced by React Query's built-in cache (staleTime + gcTime)
- v1 token refresh (localStorage `tracehub_token`) is replaced by PropelAuth session management
- Hey API uses `fetch` (not Axios) — smaller bundle, better tree-shaking
- Generated code should be committed to git (not gitignored) for CI reproducibility and review visibility
