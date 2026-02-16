---
applyTo: "**/tests/**,**/e2e/**,**/*.test.ts,**/*.test.tsx,**/conftest.py"
---

# Testing Rules

## TDD Flow

Write failing test → implement → refactor. Every public function needs tests.

## Backend (pytest + pytest-asyncio)

### Structure

```
tracehub/backend/tests/
  conftest.py          — fixtures (db session, test client, auth helpers)
  test_shipments.py    — shipment CRUD tests
  test_documents.py    — document lifecycle tests
  test_compliance.py   — compliance rule tests
  test_auth.py         — authentication tests
```

### Rules

- Tests grouped in classes by feature: `class TestShipmentCreation:`
- Descriptive names: `test_create_shipment_with_valid_data_returns_201`
- Use fixtures for common setup (db, auth, test data)
- Mock external services (JSONCargo, Anthropic, PropelAuth)
- Test both success and error paths
- Test multi-tenancy: verify org A cannot access org B's data
- Test role-based access: verify buyer cannot approve documents

### Patterns

```python
class TestShipmentCreation:
    """Tests for shipment creation endpoint."""

    def test_create_with_valid_data(self, client, admin_token):
        response = client.post("/api/shipments", json={...}, headers=auth_header(admin_token))
        assert response.status_code == 201

    def test_create_without_auth_returns_401(self, client):
        response = client.post("/api/shipments", json={...})
        assert response.status_code == 401

    def test_create_as_viewer_returns_403(self, client, viewer_token):
        response = client.post("/api/shipments", json={...}, headers=auth_header(viewer_token))
        assert response.status_code == 403
```

## Frontend (Vitest + Testing Library + Playwright)

### Unit Tests (Vitest)

- Test components in isolation
- Mock API calls
- Test user interactions (click, type, submit)
- No `any` types in test code

### E2E Tests (Playwright)

- Test critical user flows (login, create shipment, upload document)
- Use page objects for reusable selectors
- Test against real API (staging environment)

## Compliance Tests

Every compliance rule in `docs/COMPLIANCE_MATRIX.md` must have a test:
- Horn/hoof (0506/0507) → EUDR fields NOT required
- Cocoa (1801) → EUDR fields required
- BoL parsing → compliance rules BOL-001 through BOL-011
- Document lifecycle → state transitions validated

## Commands

```bash
make test              # Backend pytest + frontend vitest
make validate          # lint + test + security-scan
```
