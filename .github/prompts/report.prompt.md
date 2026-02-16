---
mode: "ask"
description: "Generate a progress report for TraceHub"
---

Generate a progress report for TraceHub. This is a read-only task — do NOT modify any files.

## Steps

1. **Read project state** from these sources:
   - `docs/PLAN.md` — extract phase, completed work, decisions, key metrics
   - Recent git log (last 20 commits)
   - Run `make test` — current test health (count of passing tests)

2. **Generate the report** in exactly this format (plain text, ready to copy/paste):

```
**TraceHub — Progress Report ({today's date})**
**Phase {N} — {focus area from PLAN.md}**

**What's built:**
{Bullet list from PLAN.md completed PRDs — group related items, keep concise}

**Recent work:**
{From git log, group commits by theme. 3-5 bullet points max}

**Test health:** {X} backend + {Y} frontend tests passing

**Key decisions:**
{2-3 recent decisions from PLAN.md decisions log}

**Next steps:**
{3-4 bullets — derived from PLAN.md upcoming PRDs}
```

3. **Output the report as text** — directly readable, ready to share.

## Important

- Do NOT create or modify any files
- Do NOT commit anything
- Just read, synthesize, and output the formatted report
