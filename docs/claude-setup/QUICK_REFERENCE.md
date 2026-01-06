# MCP & Sub-Agents Quick Reference

> One-page cheat sheet for Claude advanced features

## MCP Servers (Up-to-Date Documentation)

### When to Use

Use MCP servers when you need **current** documentation that may have changed since Claude's training cutoff.

### Quick Commands

```
✅ "Use Context 7 to fetch latest FastAPI dependency injection docs"
✅ "Get current React 18 concurrent features documentation"
✅ "Show PostgreSQL 15 JSONB indexing best practices"
```

### Common Scenarios

| Scenario | Command |
|----------|---------|
| Latest API patterns | "Use Context 7 to get latest [framework] patterns for [feature]" |
| New language features | "Fetch [language] [version] documentation for [feature]" |
| Updated best practices | "Get current best practices for [technology] [use case]" |
| Database queries | "Query tracehub database to show [what you need]" |

---

## Sub-Agents (Parallel Tasks)

### When to Use

Use sub-agents when you can split work into **independent parallel tasks**.

### Task Template

```
Spawn a sub-agent to:

Task: "[Specific action to perform]"
Context: "[Relevant files/information]"
Output: "[Exact file path or deliverable]"
Requirements:
- [Requirement 1]
- [Requirement 2]
```

### Common Use Cases

#### 1. Documentation Generation

```
Task: "Generate API documentation for shipments module"
Context: "Based on tracehub/backend/api/routes/shipments.py"
Output: "docs/api/shipments.md"
Requirements:
- Include all endpoints
- Add request/response examples
- Document error codes
```

#### 2. Test Generation

```
Task: "Generate pytest tests for Document validation"
Context: "Based on tracehub/backend/models/document.py"
Output: "tracehub/backend/tests/test_document_validation.py"
Requirements:
- Test all validation rules
- Include edge cases
- Follow existing test patterns in test_shipments.py
```

#### 3. Database Migrations

```
Task: "Generate Alembic migration for EUDR compliance fields"
Context: "Add fields: farm_plot_id (str), geolocation (JSON), production_date (date) to products table"
Output: "tracehub/backend/alembic/versions/xxx_add_eudr_fields.py"
Requirements:
- Include upgrade() and downgrade()
- Add appropriate constraints
```

#### 4. Code Refactoring

```
Task: "Refactor tracking API routes from sync to async"
Context: "tracehub/backend/api/routes/tracking.py"
Output: "Same file, updated"
Requirements:
- Convert all functions to async def
- Update database calls to use await
- Maintain backward compatibility
```

#### 5. Type Definitions

```
Task: "Generate TypeScript interfaces from Pydantic models"
Context: "Based on tracehub/backend/models/"
Output: "tracehub/frontend/src/types/api.ts"
Requirements:
- Match Python model structure
- Include optional fields correctly
- Add JSDoc comments
```

---

## Best Practices Checklist

### MCP Servers

- [ ] Be specific about what documentation to fetch
- [ ] Mention the technology version (e.g., "React 18", "Python 3.11")
- [ ] Reference official sources when possible
- [ ] Verify fetched information is current

### Sub-Agents

- [ ] Define task clearly and specifically
- [ ] Provide relevant file paths
- [ ] Specify output location explicitly
- [ ] Include examples/patterns to follow
- [ ] List all requirements upfront
- [ ] Review output before integrating

---

## Quick Decision Tree

```
Need current docs?
    Yes → Use MCP Server (Context 7)
    No  → Continue

Can task run independently?
    Yes → Use Sub-Agent
    No  → Do in main session

Multiple independent tasks?
    Yes → Spawn multiple sub-agents (parallel)
    No  → Sequential or main session
```

---

## Example: Feature Development Flow

```
# Main Session: Plan feature
"I'm adding container tracking integration"

# Sub-Agent 1: Implementation
Task: "Implement ShipsGo API client"
Context: "API spec in docs/integrations/shipsgo-api.yaml"
Output: "tracehub/backend/integrations/shipsgo_client.py"

# Sub-Agent 2: Tests (Parallel)
Task: "Generate pytest tests for ShipsGo client"
Context: "Based on API client implementation"
Output: "tracehub/backend/tests/test_shipsgo_client.py"

# Sub-Agent 3: Documentation (Parallel)
Task: "Generate API documentation for tracking endpoints"
Context: "Implementation in tracehub/backend/api/routes/tracking.py"
Output: "docs/api/container-tracking.md"

# Main Session: Integrate and verify
"Review all sub-agent outputs and run tests"
```

---

## Common Pitfalls

### ❌ Don't

```
# MCP - Too vague
"What's new in FastAPI?"

# Sub-Agent - No context
"Write some tests"

# Sub-Agent - Human role
"Act as a senior developer"
```

### ✅ Do

```
# MCP - Specific
"Use Context 7 to fetch FastAPI 0.109 dependency injection documentation"

# Sub-Agent - Specific task with context
"Generate pytest tests for Document class in tracehub/backend/models/document.py, following patterns in test_shipments.py"

# Sub-Agent - Task-based
"Refactor shipments API routes from sync to async in tracehub/backend/api/routes/shipments.py"
```

---

## Resources

- **Full Guides**: [docs/claude-setup/README.md](./README.md)
- **MCP Details**: [docs/claude-setup/MCP_SERVERS.md](./MCP_SERVERS.md)
- **Sub-Agents Details**: [docs/claude-setup/SUB_AGENTS.md](./SUB_AGENTS.md)
- **Project Context**: [CLAUDE.md](../../CLAUDE.md)

---

**Last Updated**: January 6, 2026
