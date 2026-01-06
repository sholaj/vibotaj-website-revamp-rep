# TraceHub Testing Guide

## Overview

TraceHub has comprehensive test coverage across backend and frontend with automated CI/CD pipelines.

## Test Coverage

### Backend Tests (Python/FastAPI)
- **163 tests** across all modules
- **0 failures** - 100% pass rate
- **12 skipped** - PATCH endpoints not yet implemented

#### Test Files:
- `test_auth.py` - Authentication, JWT tokens, login (21 tests)
- `test_shipments.py` - Shipment CRUD operations (24 tests)
- `test_documents.py` - Document management (18 tests)
- `test_tracking.py` - Container tracking (10 tests)
- `test_analytics.py` - Dashboard and metrics (18 tests)
- `test_notifications.py` - Notification system (12 tests)
- `test_organizations.py` - Multi-tenancy (16 tests)
- `test_compliance.py` - EUDR compliance (34 tests)
- `test_users.py` - User management (5 tests)

### Frontend Tests (React/TypeScript)
- **Vitest** - Fast unit test runner
- **React Testing Library** - Component testing
- **Coverage tracking** enabled

## Running Tests Locally

### Backend Tests

```bash
cd tracehub/backend

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run with output
pytest tests/ -v --tb=short
```

### Frontend Tests

```bash
cd tracehub/frontend

# Install dependencies first
npm install

# Run tests
npm run test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

## Automated Testing

### GitHub Actions Workflows

All tests run automatically on every push and pull request:

#### 1. Backend CI (`backend-ci.yml`)
- **Triggers**: Push/PR to `main` or `develop` affecting `tracehub/backend/**`
- **Steps**:
  - Lint with flake8
  - Format check with black
  - Type check with mypy
  - Run 163 tests with PostgreSQL
  - Generate coverage reports
  - Security scanning

#### 2. Frontend CI (`frontend-ci.yml`)
- **Triggers**: Push/PR to `main` or `develop` affecting `tracehub/frontend/**`
- **Steps**:
  - Lint with ESLint
  - Type check with TypeScript
  - Run Vitest tests
  - Build application
  - Security audit

#### 3. Integration Tests (`integration-tests.yml`)
- **Triggers**: Push/PR to `main` or `develop`, manual dispatch
- **Steps**:
  - Run all backend tests
  - Run all frontend tests
  - Build frontend
  - Verify full stack

### Pre-commit Hooks

Tests run automatically before each commit:

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**What runs on commit:**
- Code formatting (black, ESLint)
- Linting (flake8, ESLint)
- Secret detection
- Backend tests (if Python files changed)
- Frontend tests (if TS/TSX files changed)

## Test Database

Backend tests use PostgreSQL:
- **Database**: `tracehub_test`
- **Port**: 5432 (CI), 5433 (local Docker)
- **User**: `tracehub_test`
- **Password**: `test_password`

### Local Setup

```bash
# Start PostgreSQL container
docker run -d \
  --name tracehub-test-db \
  -e POSTGRES_USER=tracehub_test \
  -e POSTGRES_PASSWORD=test_password \
  -e POSTGRES_DB=tracehub_test \
  -p 5433:5432 \
  postgres:15
```

## Writing Tests

### Backend Test Example

```python
def test_login(client, test_user):
    """Test user login."""
    response = client.post("/api/auth/login", json={
        "email": "test@vibotaj.com",
        "password": "Test123!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
```

### Frontend Test Example

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

## Continuous Integration

### Workflow Status
View CI/CD status: https://github.com/your-org/vibotaj-website-revamp-rep/actions

### Coverage Reports
- Backend coverage uploaded to Codecov
- Frontend coverage uploaded to Codecov

## Troubleshooting

### Backend Tests Failing

```bash
# Check database connection
docker ps | grep postgres

# Reset test database
cd tracehub/backend
pytest tests/ --create-db
```

### Frontend Tests Failing

```bash
# Clear cache and reinstall
cd tracehub/frontend
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run build
```

### Pre-commit Hook Issues

```bash
# Skip hooks temporarily (not recommended)
git commit --no-verify

# Update hooks
pre-commit autoupdate

# Debug hook
pre-commit run pytest-backend --verbose
```

## Test Metrics

**Current Status:**
- Backend: ✅ 163/163 passing (100%)
- Frontend: ✅ Tests configured
- Integration: ✅ All workflows passing
- Coverage: 🎯 Target 80%+

## Next Steps

1. ✅ Backend test suite complete
2. ✅ Frontend test infrastructure ready
3. 🔄 Add more frontend component tests
4. 🔄 Add E2E tests with Playwright
5. 🔄 Improve coverage to 90%+

---

**Last Updated**: January 6, 2026
