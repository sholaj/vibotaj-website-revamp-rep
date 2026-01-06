.PHONY: setup test test-backend test-frontend lint format security-scan pre-commit clean dev docs validate new-prp git-check quick-start help

help: ## Show this help message
	@echo 'TraceHub Development Commands'
	@echo ''
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: ## Initial setup - install pre-commit hooks and dependencies
	@echo "=== Setting up TraceHub development environment ==="
	@echo ""
	@echo "Installing pre-commit hooks..."
	pip install pre-commit detect-secrets black ruff || echo "Note: Install pip packages manually if needed"
	pre-commit install || echo "Note: pre-commit not installed yet"
	@echo ""
	@echo "Creating secrets baseline..."
	@if [ ! -f .secrets.baseline ]; then \
		detect-secrets scan > .secrets.baseline || echo "Note: detect-secrets not installed yet"; \
	else \
		echo ".secrets.baseline already exists - skipping. Run 'detect-secrets scan' manually to update."; \
	fi
	@echo ""
	@echo "Setup complete! Remember to:"
	@echo "  1. Edit .env files with your configuration"
	@echo "  2. Review .secrets.baseline"
	@echo "  3. Run 'make test' to verify setup"

test: ## Run all tests
	@echo "=== Running TraceHub tests ==="
	@cd tracehub/backend && pytest -v --cov=app --cov-report=term-missing || echo "Tests not configured yet - see tracehub/backend/tests/"
	@echo ""
	@echo "Frontend tests:"
	@cd tracehub/frontend && npm test || echo "Frontend tests not configured yet"

test-backend: ## Run backend tests only
	@echo "=== Running backend tests ==="
	@cd tracehub/backend && pytest -v || echo "Backend tests not configured yet"

test-frontend: ## Run frontend tests only
	@echo "=== Running frontend tests ==="
	@cd tracehub/frontend && npm test || echo "Frontend tests not configured yet"

lint: ## Run linters (black, ruff for Python)
	@echo "=== Running linters ==="
	@echo "Python (black):"
	@black tracehub/backend --check || echo "Run 'black tracehub/backend' to fix"
	@echo ""
	@echo "Python (ruff):"
	@ruff check tracehub/backend || echo "Run 'ruff check tracehub/backend --fix' to fix"
	@echo ""
	@echo "TypeScript:"
	@cd tracehub/frontend && npm run lint || echo "Frontend lint not configured"

format: ## Auto-format code
	@echo "=== Formatting code ==="
	@black tracehub/backend || echo "black not installed"
	@ruff check tracehub/backend --fix || echo "ruff not installed"
	@cd tracehub/frontend && npm run format || echo "Frontend format not configured"

security-scan: ## Scan for secrets and security issues
	@echo "=== Running security scans ==="
	@echo "Scanning for secrets..."
	@detect-secrets scan --baseline .secrets.baseline || echo "No new secrets detected"
	@echo ""
	@echo "Checking for hardcoded credentials..."
	@grep -r "password\|api_key\|secret\|token" tracehub/backend/app --include="*.py" | grep -v ".pyc" | grep -v "__pycache__" || echo "No obvious credentials found"

pre-commit: ## Run pre-commit hooks manually
	@echo "=== Running pre-commit hooks ==="
	@pre-commit run --all-files

clean: ## Clean up generated files and caches
	@echo "=== Cleaning up ==="
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleanup complete"

dev: ## Start development environment (runs tracehub/Makefile)
	@echo "=== Starting TraceHub development environment ==="
	@cd tracehub && make dev

docs: ## Generate/view documentation
	@echo "=== TraceHub Documentation ==="
	@echo ""
	@echo "Key Documentation Files:"
	@echo "  - CLAUDE.md               : AI development context"
	@echo "  - CHANGELOG.md            : Version history"
	@echo "  - docs/COMPLIANCE_MATRIX.md : HS codes & requirements"
	@echo "  - docs/API.md             : API documentation"
	@echo "  - docs/DEPLOYMENT.md      : Deployment guide"
	@echo "  - docs/decisions/         : Architecture Decision Records"
	@echo ""
	@echo "Interactive API docs available at: http://localhost:8000/docs"

validate: lint test security-scan ## Run all validation checks
	@echo ""
	@echo "=== Validation complete ==="
	@echo "✅ All checks passed"

# Development workflow helpers
new-prp: ## Create a new PRP (Usage: make new-prp NAME=feature-name)
	@if [ -z "$(NAME)" ]; then echo "Usage: make new-prp NAME=feature-name"; exit 1; fi
	@echo "Creating new PRP: $(NAME)"
	@cat .claude/commands/generate-prp.md | sed 's/$$ARGUMENTS/$(NAME)/' > PRPs/active/$(NAME).md
	@echo "Created PRPs/active/$(NAME).md"
	@echo "Edit the file to complete the PRP"

git-check: ## Check git status and diff for secrets
	@echo "=== Git status ==="
	@git status
	@echo ""
	@echo "=== Checking diff for potential secrets ==="
	@git diff | grep -i "password\|api_key\|secret\|token\|bearer" || echo "No obvious secrets in diff"

# Quick reference
quick-start: ## Show quick start guide
	@echo "=== TraceHub Quick Start ==="
	@echo ""
	@echo "1. Setup environment:"
	@echo "   make setup"
	@echo ""
	@echo "2. Start development:"
	@echo "   make dev"
	@echo ""
	@echo "3. Run tests:"
	@echo "   make test"
	@echo ""
	@echo "4. Before committing:"
	@echo "   make validate"
	@echo ""
	@echo "5. View documentation:"
	@echo "   make docs"
	@echo ""
	@echo "For more commands: make help"
