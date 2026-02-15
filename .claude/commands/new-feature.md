---
description: Plan a new feature via PRD then execute it
---

This is the ONE command where you interview me before acting.

1. Ask me what I want to build (use AskUserQuestion tool).
   Focus on: inputs, outputs, edge cases, acceptance criteria.
   Ask 2-3 focused questions max, not 10.

2. Write the PRD to docs/prds/NNN-feature-name.md.
   Number sequentially from existing PRDs. Include:
   - Problem statement
   - Acceptance criteria (testable)
   - API changes (if any)
   - Database changes (if any)
   - Frontend changes (if any)
   - Compliance impact (check docs/COMPLIANCE_MATRIX.md)

3. Show me the PRD summary (3-5 bullets, not the full doc).
   Ask: "Approve to start building?"

4. On approval: create feature branch `feature/prd-NNN-short-description` from main.
   Then immediately start the /tdd cycle on that branch.
   Do NOT ask again. Execute the full test -> implement -> commit cycle.

5. When complete: push feature branch, create PR to main, update docs/PLAN.md.
