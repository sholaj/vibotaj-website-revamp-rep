# Claude Setup for TraceHub

> Configuration and guides for optimizing Claude AI for TraceHub development

## Quick Start

This directory contains documentation and configuration examples for advanced Claude features:

### 📚 Documentation

| Guide | Description |
|-------|-------------|
| [MCP_SERVERS.md](./MCP_SERVERS.md) | MCP servers for up-to-date documentation and specialized tools |
| [SUB_AGENTS.md](./SUB_AGENTS.md) | Parallel workflows with isolated Claude instances |

### ⚙️ Configuration Examples

| File | Description |
|------|-------------|
| [claude-config.example.json](./claude-config.example.json) | Example Claude Desktop MCP configuration |

## Overview

Claude can be significantly enhanced through two key features:

### 1. MCP Servers

Multi-Capability Protocol (MCP) servers extend Claude's capabilities by:
- Fetching current documentation (Context 7)
- Querying databases directly
- Automating browser interactions
- Analyzing file systems

**Why?** Claude's training data has a cutoff date. MCP servers fetch real-time information from authoritative sources.

### 2. Sub-Agents

Sub-agents are isolated Claude instances that run tasks in parallel:
- Generate documentation while developing features
- Run tests while writing code
- Refactor code independently
- Create migrations while updating models

**Why?** Parallel execution dramatically improves productivity and reduces development time.

## Setup Process

### 1. Install Claude Desktop

Download from: https://claude.ai/download

### 2. Configure MCP Servers

```bash
# Create config directory (if not exists)
mkdir -p ~/.config/claude

# Copy example configuration
cp claude-config.example.json ~/.config/claude/config.json

# Edit with your credentials
nano ~/.config/claude/config.json
```

### 3. Install MCP Server Dependencies

```bash
# Context 7 (Documentation)
npm install -g @context7/mcp-server

# PostgreSQL MCP Server
npm install -g @modelcontextprotocol/server-postgres

# File System MCP Server
npm install -g @modelcontextprotocol/server-filesystem
```

### 4. Restart Claude Desktop

Close and reopen Claude to load MCP servers.

### 5. Verify Setup

Test in Claude:
```
"Use Context 7 to fetch the latest FastAPI documentation for dependency injection"
```

## TraceHub-Specific Configuration

### Development Environment

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
      }
    },
    "tracehub-db": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_URL": "postgresql://tracehub:${DB_PASSWORD}@localhost:5432/tracehub"
      }
    }
  }
}
```

### Environment Variables

Create `~/.config/claude/.env`:

```bash
CONTEXT7_API_KEY=your_context7_api_key
DB_PASSWORD=your_database_password
```

**Security**: Never commit credentials to git!

## Common Use Cases

### Fetching Up-to-Date Documentation

```
"Use Context 7 to get the latest FastAPI async patterns documentation"
"Fetch current React 18 concurrent features documentation"
"Show PostgreSQL 15 JSONB indexing best practices"
```

### Parallel Development with Sub-Agents

```
Main Session: "I'm implementing EUDR compliance checks"

Spawn Sub-Agent 1: "Generate API documentation for EUDR endpoints"
Spawn Sub-Agent 2: "Create pytest tests for EUDR validation"
Spawn Sub-Agent 3: "Generate database migration for EUDR fields"

Result: All outputs ready simultaneously
```

### Database Debugging

```
"Query the tracehub database to show all shipments with status 'in_transit'"
"Show me the schema for the documents table"
"Find products missing EUDR compliance fields"
```

## Best Practices

### 1. Always Use MCP for Current Info

❌ **Don't**: "What are the FastAPI async patterns?"  
✅ **Do**: "Use Context 7 to fetch latest FastAPI async patterns"

### 2. Define Sub-Agents by Task

❌ **Don't**: "Act as a senior developer"  
✅ **Do**: "Generate tests for the shipments module"

### 3. Provide Context to Sub-Agents

❌ **Don't**: "Write some tests"  
✅ **Do**: "Generate pytest tests for tracehub/backend/models/shipment.py following patterns in test_documents.py"

### 4. Review Sub-Agent Output

Always verify:
- Code quality and standards
- Security considerations
- No hardcoded secrets
- Tests are meaningful

## Troubleshooting

### MCP Server Not Working

1. Check config location: `~/.config/claude/config.json`
2. Verify JSON syntax
3. Restart Claude Desktop
4. Check logs: `~/.config/claude/logs/`

### Database Connection Failed

1. Verify PostgreSQL is running: `pg_isready`
2. Check connection string
3. Test with `psql` first

### Sub-Agent Not Responding

1. Provide more specific task definition
2. Include relevant file paths
3. Reference example patterns to follow

## Resources

### Official Documentation
- [Anthropic MCP Specification](https://github.com/anthropics/mcp)
- [Claude Desktop Documentation](https://claude.ai/docs)

### TraceHub Guides
- [MCP Servers Full Guide](./MCP_SERVERS.md)
- [Sub-Agents Full Guide](./SUB_AGENTS.md)
- [Project Context](../../CLAUDE.md)

### External Resources
- [Context 7 Documentation](https://context7.ai)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)

## Support

For TraceHub-specific questions:
- Check [CLAUDE.md](../../CLAUDE.md) for project context
- Review [docs/decisions/](../decisions/) for architectural decisions
- Contact: Shola (CEO/CTO) or Bolaji Jibodu (COO)

---

**Last Updated**: January 6, 2026  
**Maintained by**: TraceHub Development Team
