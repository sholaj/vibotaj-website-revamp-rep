# TraceHub Makefile
# Convenient commands for development and deployment

.PHONY: help dev build up down logs clean test backup restore

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Development Commands
dev: ## Start development environment
	docker-compose up -d
	@echo "TraceHub is running:"
	@echo "  Frontend: http://localhost:80"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

dev-logs: ## Follow development logs
	docker-compose logs -f

dev-down: ## Stop development environment
	docker-compose down

dev-rebuild: ## Rebuild and restart development environment
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Production Commands
prod-build: ## Build production images
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Start production environment
	docker-compose -f docker-compose.prod.yml up -d
	@echo "TraceHub production is running"

prod-down: ## Stop production environment
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Follow production logs
	docker-compose -f docker-compose.prod.yml logs -f

prod-restart: ## Restart production services
	docker-compose -f docker-compose.prod.yml restart

# Database Commands
db-migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

db-rollback: ## Rollback last database migration
	docker-compose exec backend alembic downgrade -1

db-shell: ## Open PostgreSQL shell
	docker-compose exec db psql -U tracehub -d tracehub

db-backup: ## Create database backup
	@mkdir -p ./backups
	docker-compose exec db pg_dump -U tracehub tracehub > ./backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in ./backups/"

db-restore: ## Restore database from backup (Usage: make db-restore FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then echo "Usage: make db-restore FILE=backup.sql"; exit 1; fi
	docker-compose exec -T db psql -U tracehub tracehub < $(FILE)
	@echo "Database restored from $(FILE)"

# Testing Commands
test: ## Run tests
	docker-compose exec backend pytest

test-frontend: ## Run frontend tests
	cd frontend && npm test

test-coverage: ## Run tests with coverage
	docker-compose exec backend pytest --cov=app --cov-report=html

# Utility Commands
logs: ## Show all logs
	docker-compose logs

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-db: ## Show database logs
	docker-compose logs -f db

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

clean: ## Remove all containers, volumes, and images
	docker-compose down -v
	docker-compose -f docker-compose.prod.yml down -v
	@echo "Cleaned up containers and volumes"

clean-all: clean ## Remove everything including images
	docker-compose down -v --rmi all
	docker-compose -f docker-compose.prod.yml down -v --rmi all
	@echo "Cleaned up everything"

ps: ## Show running containers
	docker-compose ps

health: ## Check health of all services
	@echo "Database:"
	@docker-compose exec db pg_isready -U tracehub || echo "  Not healthy"
	@echo "Backend:"
	@curl -sf http://localhost:8000/health > /dev/null && echo "  Healthy" || echo "  Not healthy"
	@echo "Frontend:"
	@curl -sf http://localhost:80/health > /dev/null && echo "  Healthy" || echo "  Not healthy"

# Setup Commands
setup: ## Initial setup - create .env files and install dependencies
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file - please edit it"; fi
	@if [ ! -f frontend/.env ]; then cp frontend/.env.example frontend/.env; echo "Created frontend/.env file"; fi
	@echo "Setup complete - please edit .env files with your configuration"

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

install-backend: ## Install backend dependencies
	cd backend && pip install -r requirements.txt

# Deployment Commands
deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	docker-compose -f docker-compose.prod.yml build
	docker-compose -f docker-compose.prod.yml up -d
	docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
	@echo "Staging deployment complete"

deploy-production: ## Deploy to production environment
	@echo "WARNING: This will deploy to production!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.prod.yml build; \
		docker-compose -f docker-compose.prod.yml up -d; \
		docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head; \
		echo "Production deployment complete"; \
	fi
