---
description: Review recent changes against standards
---

Review the current branch's changes. Execute all checks, then report.

1. Run: git branch --show-current (confirm NOT on main; warn if so)
2. Run: git diff main --stat
3. Run: make lint (ruff + eslint)
4. Run: make test (pytest + vitest)
5. Run: make security-scan (detect-secrets + credential grep)

Check against:
- Type hints on all public functions? (Python)
- No `any` types? (TypeScript)
- Pydantic models for all API request/response bodies?
- Tests for new public functions?
- Multi-tenancy: all queries filter by organization_id?
- No hardcoded secrets or magic numbers?
- Compliance: any EUDR-related changes verified against COMPLIANCE_MATRIX.md?
- Docstrings on public functions?

Report: PASS or list issues with file:line references. Fix any auto-fixable issues immediately.
