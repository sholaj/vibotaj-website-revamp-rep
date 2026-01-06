# GitHub Secrets Configuration

This document explains how to configure GitHub Secrets for CI/CD workflows using the GitHub CLI.

## Quick Setup

### Step 1: Install GitHub CLI

```bash
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

### Step 2: Authenticate

```bash
gh auth login
```

### Step 3: Set Secrets via Environment Variables

```bash
# Copy example file
cp .env.production.example .env.production

# Edit with your values (DO NOT commit this file!)
nano .env.production

# Load environment and run setup script
source .env.production
./scripts/setup-github-secrets.sh
```

## Required Secrets

### Test Database Credentials (Optional - Defaults Provided)

These secrets are used for running tests in GitHub Actions. If not set, safe defaults will be used.

| Secret Name | Description | Default Value | Required |
|------------|-------------|---------------|----------|
| `TEST_DB_USER` | PostgreSQL test database user | `tracehub_test` | No |
| `TEST_DB_PASSWORD` | PostgreSQL test database password | `test_password` | No |
| `TEST_DB_NAME` | PostgreSQL test database name | `tracehub_test` | No |
| `TEST_JWT_SECRET` | JWT secret for test environment | `test-secret-key-for-ci` | No |

### Production Secrets (Required for Deployment)

These secrets MUST be configured for production deployments:

| Secret Name | Description | Required |
|------------|-------------|----------|
| `PROD_DB_URL` | Production database connection string | Yes |
| `PROD_JWT_SECRET` | Production JWT secret (min 32 characters) | Yes |
| `DOCKERHUB_USERNAME` | Docker Hub username for image push | Yes |
| `DOCKERHUB_TOKEN` | Docker Hub access token | Yes |
| `CODECOV_TOKEN` | Codecov upload token for coverage reports | No |

## How to Set Secrets

### Automated Setup (Recommended)

Use the provided script with environment variables:

```bash
# Set environment variables
export PROD_DB_URL='postgresql://user:pass@host:5432/db'
export PROD_JWT_SECRET=$(openssl rand -hex 32)
export DOCKERHUB_USERNAME='your-username'
export DOCKERHUB_TOKEN='your-token'

# Run setup script
./scripts/setup-github-secrets.sh
```

### Manual Setup via GitHub CLI

Set individual secrets:

```bash
# Test secrets (optional)
echo "tracehub_test" | gh secret set TEST_DB_USER
echo "test_password" | gh secret set TEST_DB_PASSWORD
openssl rand -hex 32 | gh secret set TEST_JWT_SECRET

# Production secrets (required)
gh secret set PROD_DB_URL -b "postgresql://user:pass@host:5432/db"
gh secret set PROD_JWT_SECRET -b "$(openssl rand -hex 32)"
gh secret set DOCKERHUB_USERNAME -b "your-username"
gh secret set DOCKERHUB_TOKEN -b "your-token"

# Verify
gh secret list
```

## Security Best Practices

### ✅ DO:
- Use GitHub Secrets for all sensitive data
- Rotate secrets regularly (every 90 days)
- Use different secrets for test/staging/production
- Generate strong random secrets (min 32 characters)
- Limit secret access to necessary workflows only
- Use environment-specific secrets in GitHub Environments

### ❌ DON'T:
- Never commit secrets to git (even in test files)
- Never log secrets in workflow outputs
- Never use the same secret across environments
- Never share production secrets via Slack/email
- Never store secrets in code or config files

## Secret Rotation

When rotating secrets:

1. Generate new secret value
2. Update GitHub Secret
3. Update production environment variables
4. Verify applications still work
5. Deactivate old secret after 24-48 hours

## Emergency Secret Revocation

If a secret is compromised:

1. **Immediately** delete the secret from GitHub
2. Generate a new secret value
3. Update all environments
4. Review access logs for unauthorized usage
5. Rotate all related secrets as precaution

## Validation

Test that secrets are properly configured:

```bash
# This should NOT show actual secret values
gh secret list

# Run a test workflow to verify secrets work
gh workflow run backend-ci.yml
```

## Local Development

For local development, use environment variables or `.env` files (never committed):

```bash
# Create .env file (already in .gitignore)
cat > .env << EOF
DATABASE_URL=postgresql://localhost:5433/tracehub_dev
JWT_SECRET=$(openssl rand -hex 32)
EOF

# Load environment
source .env
```

---

**Last Updated**: January 6, 2026
**Next Review**: April 6, 2026
