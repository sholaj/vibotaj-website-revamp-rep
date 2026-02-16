---
mode: "agent"
description: "Fix a bug — diagnose, test, fix, commit"
---

Fix the described issue. Act autonomously — do NOT ask for confirmation.

## Steps

1. **Understand:** Read the issue description. If a GitHub issue number is provided, read it with `gh issue view`.
2. **Reproduce:** Write a failing test that demonstrates the bug.
3. **Diagnose:** Read relevant source code. Check for:
   - Multi-tenancy violations (missing org_id filter)
   - Compliance logic errors (check `docs/COMPLIANCE_MATRIX.md`)
   - Missing error handling
   - Type mismatches
4. **Fix:** Write the minimum code change to fix the issue.
5. **Verify:** Run the failing test — it should now pass.
6. **Full suite:** Run `make validate` — all tests must pass.
7. **Commit:** On a feature branch: `git commit -m "fix(module): description"`
8. **Report:** What was wrong, what you changed, what tests you added.
