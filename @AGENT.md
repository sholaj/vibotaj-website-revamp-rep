# TraceHub Agent Build Instructions

## Project Structure
```
tracehub/
├── backend/         # FastAPI (Python 3.11)
├── frontend/        # React 18 (TypeScript)
├── docs/            # Architecture & sprint documentation
└── scripts/         # Deployment & backup scripts
```

## Backend Setup (FastAPI)
```bash
cd tracehub/backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Frontend Setup (React)
```bash
cd tracehub/frontend
npm install
```

## Running Tests

### Backend Tests
```bash
cd tracehub/backend
pytest                              # Run all tests
pytest tests/test_shipments.py      # Run specific test file
pytest -v --tb=short                # Verbose with short tracebacks
make test                           # Via Makefile (if available)
```

### Frontend Tests
```bash
cd tracehub/frontend
npm test                            # Run unit tests with Vitest
npm run test:coverage               # Run with coverage
npx playwright test                 # Run E2E tests
```

## Linting & Formatting

### Backend
```bash
cd tracehub/backend
black .                             # Format Python code
ruff check .                        # Lint Python code
ruff check . --fix                  # Auto-fix lint issues
```

### Frontend
```bash
cd tracehub/frontend
npm run lint                        # ESLint
npx prettier --check .              # Check formatting
npx prettier --write .              # Fix formatting
```

## Development Servers
```bash
# Backend (runs on port 8000)
cd tracehub/backend
uvicorn app.main:app --reload

# Frontend (runs on port 5173)
cd tracehub/frontend
npm run dev
```

## Docker Development
```bash
# Full stack with docker-compose
cd tracehub
docker-compose up -d

# Rebuild after changes
docker-compose up -d --build
```

## Database Migrations
```bash
cd tracehub/backend
alembic upgrade head                # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration
```

## Key Learnings
- Multi-tenancy: All queries must filter by `organization_id`
- EUDR compliance: Horn/hoof products (HS 0506/0507) are NOT covered
- Use `CurrentUser` from `schemas.auth`, not legacy `User` model
- Check `docs/COMPLIANCE_MATRIX.md` before compliance work
- GitOps: feature branch -> develop (staging) -> main (production)

## Feature Development Quality Standards

**CRITICAL**: All new features MUST meet the following mandatory requirements before being considered complete.

### Testing Requirements
- **Backend Coverage**: Use pytest with coverage for FastAPI endpoints
- **Frontend Coverage**: Use Vitest for React components
- **E2E Tests**: Playwright for critical user workflows
- **Test Pass Rate**: 100% - all tests must pass

### Git Workflow (GitOps)
```bash
# Create feature branch
git checkout main && git pull
git checkout -b feature/my-feature

# After implementation
git add .
git commit -m "feat(scope): description"

# Push to develop for staging
git checkout develop && git merge feature/my-feature
git push origin develop  # Triggers staging deployment

# After staging verification, merge to main
git checkout main && git merge develop
git push origin main  # Triggers production deployment
```

### Documentation Requirements
- Update relevant docs when implementation changes
- Keep `CHANGELOG.md` updated
- Update `@fix_plan.md` with task status

### Feature Completion Checklist
- [ ] All tests pass
- [ ] Code formatted (Black + Prettier)
- [ ] Type checking passes
- [ ] All changes committed with conventional commit messages
- [ ] @fix_plan.md task marked as complete
- [ ] Multi-tenancy properly implemented (organization_id filtering)
- [ ] No security vulnerabilities introduced
