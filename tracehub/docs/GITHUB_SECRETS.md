# GitHub Repository Secrets Configuration

This document lists all the secrets required for the CI/CD workflows to function.

## Required Secrets

### Production Environment

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `PRODUCTION_SSH_KEY` | Private SSH key for deploying to production VPS | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `PRODUCTION_HOST` | Production server IP or hostname | `147.93.94.145` |
| `PRODUCTION_USER` | SSH user for production server | `root` |
| `PRODUCTION_DB_PASSWORD` | PostgreSQL database password | `your-secure-password` |
| `PRODUCTION_JWT_SECRET` | JWT signing secret for authentication | `your-jwt-secret-key` |
| `DEMO_PASSWORD` | Demo user password | `your-demo-password` |

### Staging Environment

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `STAGING_SSH_KEY` | Private SSH key for deploying to staging VPS | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `STAGING_HOST` | Staging server IP or hostname | `staging.vibotaj.com` |
| `STAGING_USER` | SSH user for staging server | `root` |
| `STAGING_DB_PASSWORD` | PostgreSQL database password | `staging-password` |
| `STAGING_JWT_SECRET` | JWT signing secret | `staging-jwt-secret` |

### External API Keys (Optional)

| Secret Name | Description | When Needed |
|-------------|-------------|-------------|
| `VIZION_API_KEY` | Vizion container tracking API key | Sprint 6 (Live Tracking) |
| `ANTHROPIC_API_KEY` | Claude AI API key | Sprint 7 (AI Workflows) |
| `SENDGRID_API_KEY` | SendGrid email API key | Sprint 6 (Email Notifications) |

## Setting Secrets in GitHub

1. Go to repository Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Add each secret with its name and value

## Creating SSH Keys

Generate a new SSH key pair for deployments:

```bash
# Generate key pair
ssh-keygen -t ed25519 -C "github-actions-deploy" -f deploy_key -N ""

# Copy public key to server
ssh-copy-id -i deploy_key.pub root@your-server-ip

# Add private key as PRODUCTION_SSH_KEY secret
cat deploy_key
```

## Environment-Specific Variables

The following environment variables are set in the workflow files:

| Variable | Production | Staging |
|----------|------------|---------|
| `ENVIRONMENT` | production | staging |
| `CORS_ORIGINS` | https://tracehub.vibotaj.com | https://staging.tracehub.vibotaj.com |
| `BACKEND_PORT` | 8000 | 8000 |
| `FRONTEND_PORT` | 3000 | 3000 |
| `DB_PORT` | 5432 | 5432 |

## Security Notes

- Never commit secrets to the repository
- Rotate secrets periodically
- Use different secrets for staging and production
- Limit access to secrets to repository administrators only
