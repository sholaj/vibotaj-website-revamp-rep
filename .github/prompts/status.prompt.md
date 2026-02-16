---
mode: "ask"
description: "Quick project status — read-only"
---

Read these sources and report immediately. Do not ask what I want to know.

## Sources

1. `docs/PLAN.md`
2. Recent git log (last 15 commits)
3. `make test 2>&1 | tail -20`
4. `git branch --show-current`

## Report Format

- **Current phase:** (from PLAN.md)
- **Done recently:** (from git log)
- **Test status:** X backend + Y frontend passing
- **Current branch:** (from git branch)
- **Next up:** (from PLAN.md upcoming PRDs)

## Important

- Do NOT modify any files
- Do NOT commit anything
- Just read and report
