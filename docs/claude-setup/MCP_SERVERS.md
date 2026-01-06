# MCP Servers Configuration

> Multi-Capability Protocol (MCP) servers provide Claude with up-to-date documentation and specialized capabilities

## Overview

Claude's training data has a knowledge cutoff date, which means it may not have the latest documentation for frameworks, libraries, and tools. MCP servers solve this problem by fetching current documentation in real-time.

## What are MCP Servers?

MCP servers are specialized services that extend Claude's capabilities by:

- **Fetching up-to-date documentation** - Get current API docs, changelogs, and guides
- **Providing specialized tools** - Database queries, browser automation, code analysis
- **Accessing external systems** - APIs, file systems, development tools
- **Real-time data retrieval** - Latest package versions, dependency information

## Benefits

| Benefit | Description |
|---------|-------------|
| **Current Information** | Always access the latest documentation and API references |
| **Reduced Hallucination** | Facts come from authoritative sources, not outdated training data |
| **Specialized Capabilities** | Tools for specific domains (databases, browsers, code analysis) |
| **Faster Development** | No need to manually provide documentation context |

## Common MCP Servers for TraceHub

### 1. Context 7 - Documentation Retrieval

**Purpose**: Automatically fetches up-to-date documentation from official sources

**Use Cases**:
- FastAPI latest API documentation
- React 18 current best practices
- PostgreSQL 15+ features
- TypeScript 5.x updates

**Example Prompt**:
```
"Show me the latest FastAPI documentation for async database connections"
```

Context 7 will automatically fetch current FastAPI docs instead of relying on Claude's training data.

### 2. Database MCP Server

**Purpose**: Query PostgreSQL databases directly

**Use Cases**:
- Inspect schema without exporting SQL
- Run queries to understand data
- Debug data issues
- Validate migrations

**Example**:
```
"Show me all tables in the tracehub database"
"What's the schema for the shipments table?"
```

### 3. Browser MCP Server

**Purpose**: Automate browser interactions for testing and debugging

**Use Cases**:
- Test WordPress integration
- Debug UI issues
- Automate form submissions
- Validate tracking dashboard

**Example**:
```
"Navigate to the tracking dashboard and verify the container status displays correctly"
```

### 4. File System MCP Server

**Purpose**: Read, write, and analyze files in the repository

**Use Cases**:
- Search across codebase
- Analyze dependencies
- Generate reports
- Batch file operations

**Example**:
```
"Find all TypeScript files that import the DocumentState enum"
```

## Setup Instructions

### Prerequisites

- Claude Desktop app or Claude Pro subscription
- Node.js 18+ (for most MCP servers)
- Python 3.9+ (for Python-based MCP servers)

### Installation Steps

#### 1. Install Context 7 (Documentation MCP Server)

```bash
# Using npm
npm install -g @context7/mcp-server

# Or using Python
pip install context7-mcp
```

#### 2. Configure Claude to Use MCP Server

Create or edit `~/.config/claude/config.json`:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "your-api-key-here"
      }
    },
    "database": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_URL": "postgresql://user:pass@localhost:5432/tracehub"
      }
    }
  }
}
```

#### 3. Restart Claude

Close and reopen Claude Desktop to load the MCP servers.

#### 4. Verify Installation

Test the MCP server with a simple prompt:

```
"Use Context 7 to show me the latest FastAPI documentation structure"
```

## TraceHub-Specific MCP Configuration

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
    },
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_PATHS": [
          "/home/runner/work/vibotaj-website-revamp-rep/vibotaj-website-revamp-rep"
        ]
      }
    }
  }
}
```

### Production Environment

For production, limit MCP server access:

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
    "tracehub-db-readonly": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_URL": "postgresql://readonly_user:${DB_PASSWORD}@localhost:5432/tracehub",
        "READ_ONLY": "true"
      }
    }
  }
}
```

## Best Practices

### 1. Use MCP Servers for Current Information

❌ **Don't**:
```
"What are the FastAPI decorators for async routes?"
```
(Claude will use potentially outdated training data)

✅ **Do**:
```
"Use Context 7 to fetch the latest FastAPI documentation for async route decorators"
```

### 2. Specify What to Fetch

Be explicit about what documentation you need:

```
"Fetch the latest PostgreSQL 15 documentation for JSONB indexing strategies"
"Get React 18 concurrent features documentation"
"Show TypeScript 5.x utility types reference"
```

### 3. Combine with Repository Context

```
"Use Context 7 to get FastAPI middleware docs, then review our auth middleware 
in tracehub/backend/middleware/auth.py for consistency with best practices"
```

### 4. Verify Documentation Sources

Always check that fetched documentation is from official sources:
- fastapi.tiangolo.com for FastAPI
- react.dev for React
- postgresql.org for PostgreSQL
- typescriptlang.org for TypeScript

## Security Considerations

### Environment Variables

**Never commit MCP configuration with credentials!**

Use environment variables for sensitive data:

```json
{
  "mcpServers": {
    "database": {
      "env": {
        "POSTGRES_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### Read-Only Access

For database MCP servers, use read-only credentials:

```sql
-- Create read-only user
CREATE USER claude_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE tracehub TO claude_readonly;
GRANT USAGE ON SCHEMA public TO claude_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO claude_readonly;
```

### Restricted File Access

Limit file system MCP server to specific directories:

```json
{
  "filesystem": {
    "env": {
      "ALLOWED_PATHS": [
        "/path/to/tracehub/docs",
        "/path/to/tracehub/src"
      ],
      "DENIED_PATHS": [
        "/path/to/tracehub/.env",
        "/path/to/tracehub/.secrets"
      ]
    }
  }
}
```

## Troubleshooting

### MCP Server Not Loading

**Problem**: Claude doesn't recognize MCP commands

**Solution**:
1. Check config file location: `~/.config/claude/config.json`
2. Verify JSON syntax (use a JSON validator)
3. Restart Claude Desktop completely
4. Check Claude logs: `~/.config/claude/logs/`

### Context 7 Not Fetching Documentation

**Problem**: Context 7 returns outdated or no results

**Solution**:
1. Verify API key is valid
2. Check internet connection
3. Specify exact documentation source URL if needed
4. Try alternative documentation sources

### Database Connection Issues

**Problem**: Cannot connect to PostgreSQL

**Solution**:
1. Verify PostgreSQL is running: `pg_isready`
2. Check connection string format
3. Verify user permissions
4. Test connection with `psql` first

## Integration with TraceHub Workflow

### Development Workflow

```mermaid
graph LR
    A[Start Task] --> B[Check Documentation Needs]
    B --> C{Up-to-date?}
    C -->|No| D[Use Context 7]
    C -->|Yes| E[Proceed]
    D --> E
    E --> F[Implement Feature]
    F --> G[Test]
    G --> H[Review]
```

### Example Development Session

```bash
# 1. Start with current documentation
Claude: "Use Context 7 to fetch latest FastAPI dependency injection patterns"

# 2. Check existing code
Claude: "Show me how we currently handle dependencies in tracehub/backend/api/routes/"

# 3. Implement with best practices
Claude: "Update the shipments route to use the latest FastAPI dependency injection pattern"

# 4. Verify against documentation
Claude: "Compare our implementation with the official FastAPI docs to ensure compliance"
```

## Resources

- [MCP Specification](https://github.com/anthropics/mcp)
- [Context 7 Documentation](https://context7.ai)
- [Model Context Protocol Servers](https://github.com/modelcontextprotocol/servers)
- [FastAPI Official Docs](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Next Steps

1. Install Context 7 MCP server for documentation retrieval
2. Configure database MCP server for TraceHub development
3. Read [SUB_AGENTS.md](./SUB_AGENTS.md) for parallel workflow optimization
4. Review [CLAUDE.md](../../CLAUDE.md) for project-specific Claude usage

---

**Last Updated**: January 6, 2026  
**Maintained by**: TraceHub Development Team
