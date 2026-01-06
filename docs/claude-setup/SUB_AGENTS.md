# Sub-Agents for Parallel Workflows

> Isolated Claude instances that run tasks in parallel with the main session

## Overview

Sub-agents are independent Claude instances that work alongside your main Claude session to handle specific tasks in parallel. This offloads work cleanly and improves productivity by allowing multiple tasks to progress simultaneously.

## What are Sub-Agents?

Sub-agents are:

- **Isolated Claude instances** - Each has its own context window and memory
- **Task-specific workers** - Defined by tasks, not human-like roles
- **Parallel processors** - Work simultaneously with main session
- **Independent executors** - Have their own set of tools and capabilities

## Key Concepts

### Sub-Agents vs. Main Session

| Aspect | Main Session | Sub-Agent |
|--------|-------------|-----------|
| **Context** | Full project context | Task-specific context |
| **Scope** | Broad, strategic | Narrow, focused |
| **Duration** | Long-lived | Task-duration |
| **Coordination** | Orchestrates sub-agents | Reports back to main |

### When to Use Sub-Agents

✅ **Good Use Cases**:
- Generate documentation while developing features
- Run tests in parallel with code reviews
- Refactor code while implementing new features
- Generate API specifications while building endpoints
- Create migration scripts while updating models

❌ **Poor Use Cases**:
- Simple, sequential tasks
- Tasks requiring main session context
- Quick one-off commands
- Tasks with complex dependencies

## Sub-Agent Architecture

```
┌─────────────────────────────────────────────────┐
│           Main Claude Session                   │
│  (Strategic oversight & coordination)           │
└────────┬─────────────┬──────────────┬───────────┘
         │             │              │
    ┌────▼───┐    ┌───▼────┐    ┌───▼────┐
    │ Agent  │    │ Agent  │    │ Agent  │
    │   1    │    │   2    │    │   3    │
    └────┬───┘    └───┬────┘    └───┬────┘
         │            │              │
    ┌────▼───┐   ┌───▼────┐    ┌───▼────┐
    │Feature │   │  Test  │    │  Docs  │
    │  Dev   │   │  Run   │    │  Gen   │
    └────────┘   └────────┘    └────────┘
```

## Defining Sub-Agents

### Task-Based Definition (✅ Correct)

Define sub-agents by **what they do**, not **who they are**:

```
Good Examples:
- "Generate API documentation for the shipments module"
- "Run integration tests for the tracking system"
- "Refactor database queries to use async/await"
- "Create TypeScript interfaces from Python models"
- "Generate CHANGELOG entries from git commits"
```

### Role-Based Definition (❌ Incorrect)

Avoid defining sub-agents as human roles:

```
Bad Examples:
- "Act as a senior backend engineer" (too vague)
- "Be a DevOps expert" (not task-specific)
- "Work as a technical writer" (too broad)
```

## TraceHub Sub-Agent Patterns

### Pattern 1: Documentation Generation

**Scenario**: Implementing EUDR compliance feature

**Main Session**:
```
I'm implementing EUDR compliance checks for shipments.
While I work on the backend code, spawn a sub-agent to:

Task: "Generate API documentation for EUDR compliance endpoints"
Context: "Based on the shipments module in tracehub/backend/api/routes/shipments.py"
Output: "docs/api/eudr-compliance.md"
```

**Sub-Agent Task**:
- Reads existing shipments API code
- Extracts endpoint definitions
- Generates OpenAPI-style documentation
- Writes to docs/api/eudr-compliance.md

**Result**: Documentation ready when code is complete

### Pattern 2: Test Generation

**Scenario**: Adding new document validation logic

**Main Session**:
```
I'm adding document validation for Bill of Lading.
Spawn a sub-agent to:

Task: "Generate pytest tests for Bill of Lading validation"
Context: "Based on validation rules in tracehub/backend/models/document.py"
Output: "tracehub/backend/tests/test_bol_validation.py"
Requirements:
- Test happy path
- Test missing required fields
- Test invalid BL numbers
- Test EUDR compliance scenarios
```

**Sub-Agent Task**:
- Analyzes document validation logic
- Creates comprehensive test cases
- Follows existing test patterns
- Ensures compliance testing

**Result**: Tests ready to run immediately

### Pattern 3: Migration Generation

**Scenario**: Adding new fields to database schema

**Main Session**:
```
I'm adding EUDR compliance fields to the Product model.
Spawn a sub-agent to:

Task: "Generate Alembic migration for EUDR fields on Product table"
Context: "New fields: farm_plot_id (str), geolocation (JSON), production_date (date)"
Output: "tracehub/backend/alembic/versions/xxx_add_eudr_fields.py"
```

**Sub-Agent Task**:
- Creates Alembic migration file
- Adds upgrade() and downgrade() methods
- Includes proper type definitions
- Adds NOT NULL constraints where appropriate

**Result**: Migration ready to apply

### Pattern 4: Code Refactoring

**Scenario**: Updating API routes to async

**Main Session**:
```
Spawn a sub-agent to:

Task: "Refactor shipments API routes from sync to async"
Context: "tracehub/backend/api/routes/shipments.py"
Requirements:
- Convert all route functions to async def
- Update database calls to use await
- Keep same endpoint signatures
- Maintain backward compatibility
```

**Sub-Agent Task**:
- Analyzes current sync implementation
- Converts to async/await pattern
- Updates database session handling
- Preserves functionality

**Result**: Refactored code ready for testing

### Pattern 5: Configuration Generation

**Scenario**: Setting up new environment

**Main Session**:
```
While I set up the production deployment, spawn a sub-agent to:

Task: "Generate production-ready configuration files"
Context: "Based on development config in tracehub/backend/config/"
Output: 
  - "config/production.env.template"
  - "config/nginx.conf"
  - "config/supervisor.conf"
```

**Sub-Agent Task**:
- Creates production config templates
- Removes development-only settings
- Adds production security settings
- Documents required environment variables

**Result**: Configuration files ready for deployment

## Best Practices

### 1. Provide Clear Context

Give sub-agents exactly what they need:

```
✅ Good:
"Generate tests for the Document class in tracehub/backend/models/document.py
Include tests for state transitions: Draft -> Uploaded -> Validated
Follow existing test patterns in tracehub/backend/tests/test_models.py"

❌ Bad:
"Write some tests for documents"
```

### 2. Define Success Criteria

Be explicit about what "done" means:

```
✅ Good:
"Generate API documentation with:
- All endpoints documented
- Request/response examples
- Error codes listed
- Authentication requirements
Output format: OpenAPI 3.0 YAML"

❌ Bad:
"Document the API"
```

### 3. Specify Output Location

Tell sub-agents where to put results:

```
✅ Good:
"Output: docs/api/shipments.md"

❌ Bad:
"Save the documentation somewhere"
```

### 4. Include Relevant Constraints

Mention important constraints upfront:

```
✅ Good:
"Refactor to async but maintain Python 3.11 compatibility
Keep existing function signatures for backward compatibility
No breaking changes to public API"

❌ Bad:
"Make it async"
```

### 5. Reference Examples

Point to existing patterns to follow:

```
✅ Good:
"Follow the same test structure as tracehub/backend/tests/test_shipments.py
Use the same pytest fixtures and assertion style"

❌ Bad:
"Write tests however you think is best"
```

## Common Sub-Agent Tasks for TraceHub

### Documentation Tasks

```
1. "Generate API reference for [module]"
2. "Create user guide for [feature]"
3. "Generate CHANGELOG entries from git commits since last release"
4. "Create migration guide for [breaking change]"
5. "Generate OpenAPI spec from FastAPI routes"
```

### Testing Tasks

```
1. "Generate pytest tests for [module]"
2. "Create integration tests for [API endpoint]"
3. "Generate test fixtures for [model]"
4. "Create E2E test scenarios for [user flow]"
5. "Generate performance test suite for [feature]"
```

### Code Generation Tasks

```
1. "Generate TypeScript interfaces from Python Pydantic models"
2. "Create database migration for [schema change]"
3. "Generate API client from OpenAPI spec"
4. "Create React components from design specifications"
5. "Generate SQL queries from ORM models"
```

### Refactoring Tasks

```
1. "Convert [module] from sync to async"
2. "Update [module] to use new [pattern]"
3. "Extract common logic into utility functions"
4. "Split large file into smaller modules"
5. "Update imports after module reorganization"
```

### Analysis Tasks

```
1. "Analyze dependencies and generate upgrade plan"
2. "Review security vulnerabilities in [module]"
3. "Generate complexity report for [module]"
4. "Find unused code in [directory]"
5. "Analyze test coverage gaps"
```

## Coordination Patterns

### Sequential Handoff

Main session completes work, sub-agent takes over:

```
Main: Implement feature
  ↓
Sub-Agent 1: Generate tests
  ↓
Sub-Agent 2: Generate documentation
  ↓
Main: Review and integrate
```

### Parallel Execution

Multiple sub-agents work simultaneously:

```
Main: Define requirements
  ↓
  ├→ Sub-Agent 1: Implement backend
  ├→ Sub-Agent 2: Generate tests
  └→ Sub-Agent 3: Create documentation
  ↓
Main: Integrate all outputs
```

### Iterative Refinement

Sub-agent outputs feed back to main session:

```
Main: Define task
  ↓
Sub-Agent: Initial implementation
  ↓
Main: Review and provide feedback
  ↓
Sub-Agent: Refine based on feedback
  ↓
Main: Final review and merge
```

## Example: Full Feature Development

**Goal**: Add container tracking integration

**Main Session Orchestration**:

```
Step 1: I'll design the API and data model

Step 2: Spawn Sub-Agent 1:
  Task: "Implement ShipsGo API client"
  Context: "API spec in docs/integrations/shipsgo-api.yaml"
  Output: "tracehub/backend/integrations/shipsgo_client.py"

Step 3: Spawn Sub-Agent 2 (parallel):
  Task: "Generate database migration for container_events table"
  Context: "Schema defined in docs/architecture/data-model.md"
  Output: "tracehub/backend/alembic/versions/xxx_container_events.py"

Step 4: Spawn Sub-Agent 3 (parallel):
  Task: "Generate pytest tests for ShipsGo client"
  Context: "Based on API client spec"
  Output: "tracehub/backend/tests/test_shipsgo_client.py"

Step 5: I'll integrate all pieces and run tests

Step 6: Spawn Sub-Agent 4:
  Task: "Generate API documentation for tracking endpoints"
  Context: "Implementation in tracehub/backend/api/routes/tracking.py"
  Output: "docs/api/container-tracking.md"

Step 7: Final review and commit
```

**Timeline**:
- Without sub-agents: ~4 hours sequential work
- With sub-agents: ~2 hours (parallel execution)

## Security Considerations

### Context Isolation

Each sub-agent has limited context:

```python
# Sub-agents should NOT have access to:
- Production credentials
- API keys
- Customer data
- Private repository information

# Sub-agents SHOULD only access:
- Public code repositories
- Documentation
- Test data
- Development configurations
```

### Output Validation

Always review sub-agent outputs:

```
Checklist:
- [ ] Code follows project standards
- [ ] No hardcoded secrets
- [ ] Tests are meaningful
- [ ] Documentation is accurate
- [ ] No security vulnerabilities introduced
```

## Limitations

### What Sub-Agents Cannot Do

1. **Cross-session coordination** - Sub-agents don't communicate with each other
2. **Context persistence** - Each sub-agent session is isolated
3. **Strategic decisions** - Main session handles architecture choices
4. **Complex debugging** - Requires full context from main session

### When to Keep Work in Main Session

- Strategic planning
- Architecture decisions
- Complex debugging
- Tasks requiring full project context
- High-level code reviews

## Monitoring Sub-Agent Progress

### Status Checks

Periodically check on sub-agent tasks:

```
"Sub-Agent 1, provide status update:
- Current progress
- Any blockers
- Estimated completion time"
```

### Error Handling

If a sub-agent encounters issues:

```
1. Review error messages
2. Provide additional context
3. Refine task definition
4. Re-spawn if necessary
```

## Resources

- [Claude Documentation on Sub-Agents](https://docs.anthropic.com/claude/docs/sub-agents)
- [MCP Servers Setup](./MCP_SERVERS.md)
- [TraceHub Development Workflow](../../CLAUDE.md)
- [API Documentation Standards](../API.md)

## Next Steps

1. Review [MCP_SERVERS.md](./MCP_SERVERS.md) for capability extensions
2. Practice with simple sub-agent tasks
3. Integrate into TraceHub development workflow
4. Share learnings with team

---

**Last Updated**: January 6, 2026  
**Maintained by**: TraceHub Development Team
