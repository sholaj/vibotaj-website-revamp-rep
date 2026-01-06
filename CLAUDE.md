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

## Current Focus

**Sprint 8: EUDR Correction & Multi-Tenancy** - COMPLETED
- [x] Remove EUDR fields from horn/hoof products
- [x] Implement organization model
- [x] Onboard HAGES as pilot customer

---

## Browser UI Testing

**Puppeteer MCP Server** is installed for automated browser testing.

### Available Tools
After Claude Code restart, these puppeteer tools are available:
- `puppeteer_launch` - Launch browser instance
- `puppeteer_navigate` - Navigate to URL
- `puppeteer_screenshot` - Capture screenshots
- `puppeteer_click` - Click elements
- `puppeteer_type` - Type text into inputs
- `puppeteer_get_text` - Extract text from elements
- `puppeteer_evaluate` - Execute JavaScript
- `puppeteer_wait_for_selector` - Wait for elements

### Example: Test Login Flow
```
1. Launch browser: puppeteer_launch
2. Navigate: puppeteer_navigate to https://tracehub.vibotaj.com
3. Type email: puppeteer_type in email input
4. Type password: puppeteer_type in password input
5. Click login: puppeteer_click on login button
6. Screenshot: puppeteer_screenshot to verify
```

### Management
```bash
npx puppeteer-mcp-claude status    # Check installation
npx puppeteer-mcp-claude uninstall # Remove if needed
```

---

## Test Accounts

### HAGES Organization (Buyer)
| User | Email | Password |
|------|-------|----------|
| Helge Bischoff (owner) | helge.bischoff@hages.de | Hages2026Helge! |
| Mats Morten Jarsetz (admin) | mats.jarsetz@hages.de | Hages2026Mats! |
| Eike Pannen (admin) | eike.pannen@hages.de | Hages2026Eike! |

### VIBOTAJ Organization (Exporter)
| User | Email | Notes |
|------|-------|-------|
| Admin | admin@vibotaj.com | System admin |
| Shola | shola@vibotaj.com | CEO/CTO |
