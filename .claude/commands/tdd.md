---
description: TDD cycle — execute without asking
---

Execute a TDD cycle on the module specified. Do NOT ask for confirmation at any step.

1. Read the relevant PRD from docs/prds/ if one exists.
2. Create feature branch from main: `git checkout -b feature/prd-XXX-short-description`
3. Write failing tests in the appropriate tests/ directory.
4. Run: make test (or pytest directly for backend-only changes)
5. Confirm tests FAIL (if they pass, the test is wrong — fix it).
6. Write minimum implementation to make tests pass.
7. Run: make test
8. Confirm tests PASS.
9. Run: make lint (ruff for backend, eslint for frontend)
10. Fix any issues.
11. Run full validation: make validate
12. Git commit on feature branch: git add <files> && git commit -m "feat(module): description"
13. Push feature branch: git push -u origin feature/prd-XXX-short-description
14. Report: what tests were written, what code was implemented, what's next.
