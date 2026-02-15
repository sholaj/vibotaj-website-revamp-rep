# Security Rules

## Authentication (v2: PropelAuth)

- PropelAuth manages users, organizations, roles, and SAML/SCIM
- Backend validates tokens via PropelAuth FastAPI SDK
- Frontend uses PropelAuth React components
- 6 roles: `admin`, `compliance_officer`, `logistics`, `buyer`, `supplier`, `viewer`
- Role checks happen at the route level via FastAPI `Depends()`

### PropelAuth Pattern
```python
from propelauth_fastapi import init_auth, User

auth = init_auth(auth_url, api_key)

@router.get("/shipments")
async def list_shipments(user: User = Depends(auth.require_user)):
    org_id = user.org_id  # Always derive from token
    ...
```

## Secrets Management

- All secrets use `pydantic.SecretStr` in Settings
- Never `os.getenv()` — always `pydantic-settings`
- Never log SecretStr values
- Never commit `.env` files
- Never hardcode secrets in code or tests
- API keys stored as SHA-256 hashes, never plaintext

## CORS

- Configurable origins via Settings
- Never `["*"]` in production
- Allow methods: GET, POST, PUT, DELETE, OPTIONS
- Allow headers: Authorization, Content-Type

## Error Responses

All API errors use structured format:
```json
{"code": "ASSET_NOT_FOUND", "message": "Shipment not found", "detail": null}
```

Never return stack traces to clients. Log them server-side.

## File Upload Security

- Extension whitelist: `.pdf`, `.docx`, `.xlsx`, `.jpg`, `.png` only
- MIME type validation must match extension
- Max upload size via Settings (default: 50MB)
- Sanitize filenames — strip path traversal (`..`, `/`, `\`)
- Store in Supabase Storage (v2) — never serve directly

## Anti-Patterns

- Never skip auth with `# TODO: add auth later`
- Never store plaintext API keys or passwords
- Never trust frontend-supplied organization_id
- Never return data across tenants
- Never expose internal IDs (UUIDs) where slugs would suffice
