# TraceHub - Project Context

> Single source of truth for AI-assisted development

## Project

**TraceHub** - Container tracking & compliance platform for VIBOTAJ Global Nigeria Ltd  
**EU TRACES:** RC1479592 | **Production:** https://tracehub.vibotaj.com  
**Stack:** FastAPI (Python 3.11) + React 18 (TypeScript) + PostgreSQL

## Team

- **CEO/CTO:** Shola | **COO:** Bolaji Jibodu (bolaji@vibotaj.com)
- **Buyers:** HAGES, Witatrade, Beckman GBH, De Lochting (Belgium)

---

## 🚨 CRITICAL BUSINESS RULES

### EUDR Compliance - READ FIRST

**Horn & Hoof (HS 0506/0507) = NOT covered by EUDR**

NEVER add to horn/hoof products:
- ❌ Geolocation coordinates
- ❌ Deforestation statements
- ❌ EUDR risk scores

REQUIRED documents for horn/hoof:
- ✅ EU TRACES (RC1479592)
- ✅ Veterinary Health Cert
- ✅ Certificate of Origin
- ✅ Bill of Lading
- ✅ Commercial Invoice
- ✅ Packing List

**Check `docs/COMPLIANCE_MATRIX.md` before any compliance work.**

---

## Code Standards

### Python
- Formatter: Black (line-length=88)
- Linter: ruff
- Type hints: Required for public functions
- Docstrings: Google style

### TypeScript
- Formatter: Prettier
- Linter: ESLint (strict)
- No `any` types

### Commits
```
feat(scope): description
fix(scope): description
docs: description
test: description
refactor: description
```

---

## Workflow

1. **Before coding:** Check `docs/COMPLIANCE_MATRIX.md` and `docs/decisions/`
2. **Complex features:** Create PRP in `PRPs/active/`
3. **Write tests first** (TDD)
4. **Run before commit:** `make test && make lint`
5. **Update:** CHANGELOG.md

---

## Security - CRITICAL

- **NEVER** commit secrets - use `.env` only
- **ALWAYS** run pre-commit hooks
- **CHECK** diffs for API keys before push

---

## Key Paths

| Path | Purpose |
|------|---------|
| `docs/COMPLIANCE_MATRIX.md` | HS codes & required documents |
| `docs/decisions/` | Architecture decisions |
| `tracehub/` | Main application code |
| `PRPs/active/` | Current implementation blueprints |

---

## Advanced Features & Workflow

### MCP Servers - Up-to-Date Documentation

Claude's training data may be outdated. Use MCP (Multi-Capability Protocol) servers to fetch current documentation reliably:

- **Context 7**: Automatically brings up-to-date docs when prompted
- **Database MCP**: Query databases directly for debugging
- **Browser MCP**: Automate browser testing and debugging
- **File System MCP**: Search and analyze codebase efficiently

📖 **Full Guide**: [docs/claude-setup/MCP_SERVERS.md](docs/claude-setup/MCP_SERVERS.md)

### Sub-Agents - Parallel Workflows

Sub-agents are isolated Claude instances that run tasks in parallel with the main session:

- Each sub-agent has its own context window and tools
- Offloads work cleanly (documentation, testing, refactoring)
- Define by specific tasks, not human-like roles
- Improves productivity through parallel execution

📖 **Full Guide**: [docs/claude-setup/SUB_AGENTS.md](docs/claude-setup/SUB_AGENTS.md)

---

## Current Focus

**Sprint 8: EUDR Correction & Multi-Tenancy**
- [ ] Remove EUDR fields from horn/hoof products
- [ ] Implement organization model
- [ ] Onboard HAGES as pilot customer
