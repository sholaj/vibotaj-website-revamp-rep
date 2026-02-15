---
description: Project status — just report, don't ask
---

Read these and report immediately. Do not ask what I want to know.

1. docs/PLAN.md
2. git log --oneline -15
3. make test 2>&1 | tail -20
4. git branch --show-current

Report format:
- Current phase: (from PLAN.md)
- Done recently: (from git log)
- Test status: X backend + Y frontend passing
- Current branch: (from git branch)
- Next up: (from PLAN.md upcoming PRDs)
