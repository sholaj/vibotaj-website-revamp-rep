#!/bin/bash
# Setup GitHub Secrets for TraceHub CI/CD
# Usage: ./setup-github-secrets.sh

set -e

echo "🔐 TraceHub GitHub Secrets Setup"
echo "=================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is installed and authenticated"
echo ""

# Function to set secret from environment or generate
set_secret() {
    local secret_name=$1
    local env_var=$2
    local default_value=$3
    
    if [ -n "${!env_var}" ]; then
        echo "Setting $secret_name from environment variable $env_var..."
        echo "${!env_var}" | gh secret set "$secret_name"
    elif [ -n "$default_value" ]; then
        echo "Setting $secret_name with default value..."
        echo "$default_value" | gh secret set "$secret_name"
    else
        echo "⚠️  Skipping $secret_name (no value provided)"
    fi
}

# Test Database Secrets (optional - defaults in workflows)
echo "📦 Test Database Secrets (optional):"
echo "-----------------------------------"
set_secret "TEST_DB_USER" "TEST_DB_USER" "tracehub_test"
set_secret "TEST_DB_PASSWORD" "TEST_DB_PASSWORD" "test_password"
set_secret "TEST_DB_NAME" "TEST_DB_NAME" "tracehub_test"

# Generate secure JWT secret if not provided
if [ -z "$TEST_JWT_SECRET" ]; then
    echo "Generating secure TEST_JWT_SECRET..."
    TEST_JWT_SECRET=$(openssl rand -hex 32)
fi
set_secret "TEST_JWT_SECRET" "TEST_JWT_SECRET" "$TEST_JWT_SECRET"

echo ""
echo "🚀 Production Secrets (set via environment):"
echo "--------------------------------------------"

# Production secrets - must be set via environment variables
if [ -n "$PROD_DB_URL" ]; then
    echo "Setting PROD_DB_URL..."
    echo "$PROD_DB_URL" | gh secret set "PROD_DB_URL"
else
    echo "⚠️  PROD_DB_URL not set - required for production deployments"
fi

if [ -n "$PROD_JWT_SECRET" ]; then
    echo "Setting PROD_JWT_SECRET..."
    echo "$PROD_JWT_SECRET" | gh secret set "PROD_JWT_SECRET"
else
    echo "⚠️  PROD_JWT_SECRET not set - required for production"
    echo "   Generate with: openssl rand -hex 32"
fi

# Docker Hub secrets
if [ -n "$DOCKERHUB_USERNAME" ]; then
    echo "Setting DOCKERHUB_USERNAME..."
    echo "$DOCKERHUB_USERNAME" | gh secret set "DOCKERHUB_USERNAME"
else
    echo "⚠️  DOCKERHUB_USERNAME not set"
fi

if [ -n "$DOCKERHUB_TOKEN" ]; then
    echo "Setting DOCKERHUB_TOKEN..."
    echo "$DOCKERHUB_TOKEN" | gh secret set "DOCKERHUB_TOKEN"
else
    echo "⚠️  DOCKERHUB_TOKEN not set"
fi

# Codecov token (optional)
if [ -n "$CODECOV_TOKEN" ]; then
    echo "Setting CODECOV_TOKEN..."
    echo "$CODECOV_TOKEN" | gh secret set "CODECOV_TOKEN"
fi

echo ""
echo "✅ Secrets setup complete!"
echo ""
echo "📋 Current secrets:"
gh secret list

echo ""
echo "💡 Usage examples:"
echo "   # Set production secrets before running:"
echo "   export PROD_DB_URL='postgresql://user:pass@host:5432/db'"
echo "   export PROD_JWT_SECRET=\$(openssl rand -hex 32)"
echo "   export DOCKERHUB_USERNAME='your-username'"
echo "   export DOCKERHUB_TOKEN='your-token'"
echo "   ./setup-github-secrets.sh"
echo ""
echo "   # Or set from .env file:"
echo "   source .env.production"
echo "   ./setup-github-secrets.sh"
