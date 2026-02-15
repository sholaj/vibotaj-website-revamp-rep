---
description: Deploy checklist — verify before deploying
---

Run deployment verification. Do NOT actually deploy — just confirm readiness.

## Pre-Deploy Checklist

1. **Branch check:** `git branch --show-current` — must be `main`
2. **Clean working tree:** `git status` — no uncommitted changes
3. **Tests pass:** `make validate` — lint + test + security-scan all green
4. **No secrets exposed:** `make security-scan` — clean
5. **PLAN.md up to date:** Check that completed PRDs are marked done
6. **Database migrations:** Check for pending Alembic migrations
7. **Environment variables:** Verify all required env vars are documented in `.env.example`

## Report

Output a deployment readiness report:
```
**Deploy Readiness — {date}**
- Branch: main ✓/✗
- Clean tree: ✓/✗
- Tests: {X} passing ✓/✗
- Security scan: clean ✓/✗
- Pending migrations: {list or "none"}
- Missing env vars: {list or "none"}

**Verdict:** READY / NOT READY (with blockers)
```

## Important
- Do NOT push to production
- Do NOT run deployment commands
- Only verify and report readiness
