---
mode: "agent"
description: "Plan a new feature via PRD then execute it"
---

This is the ONE prompt where you interview me before acting.

## Steps

1. **Gather requirements.** Ask what I want to build. Focus on: inputs, outputs, edge cases, acceptance criteria. Ask 2-3 focused questions max, not 10.

2. **Write the PRD** to `docs/prds/NNN-feature-name.md`. Number sequentially from existing PRDs. Include:
   - Problem statement
   - Acceptance criteria (testable)
   - API changes (if any)
   - Database changes (if any)
   - Frontend changes (if any)
   - Compliance impact (check `docs/COMPLIANCE_MATRIX.md`)

3. **Show me the PRD summary** (3-5 bullets, not the full doc). Ask: "Approve to start building?"

4. **On approval:** Create feature branch `feature/prd-NNN-short-description` from main. Then immediately start the TDD cycle on that branch. Do NOT ask again — execute the full test → implement → commit cycle.

5. **When complete:** Push feature branch, create PR to main, update `docs/PLAN.md`.

## Context

- Read `docs/PLAN.md` for current sprint and existing PRD numbers
- Read `docs/COMPLIANCE_MATRIX.md` if the feature touches compliance
- Check `AGENTS.md` for critical business rules (EUDR horn/hoof exception, multi-tenancy)
- Use conventional commits: `feat(scope):`, `fix(scope):`, `test(scope):`
