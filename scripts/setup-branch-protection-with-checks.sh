#!/bin/bash
# Setup branch protection rules for main branch WITH status checks
# Repository: sholaj/vibotaj-website-revamp-rep
# Use this version if you have CI/CD workflows that need to pass

set -euo pipefail

REPO="sholaj/vibotaj-website-revamp-rep"
BRANCH="main"

echo "Setting up branch protection with status checks for ${BRANCH} on ${REPO}..."

# Branch protection rules configuration with status checks
# Adjust the "contexts" array to match your GitHub Actions workflow job names
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "/repos/${REPO}/branches/${BRANCH}/protection" \
  -f required_status_checks='{
    "strict": true,
    "contexts": ["test", "lint", "build", "deploy-staging"]
  }' \
  -f enforce_admins=false \
  -f required_pull_request_reviews='{
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": false
  }' \
  -f restrictions='null' \
  -f required_linear_history=false \
  -f allow_force_pushes=false \
  -f allow_deletions=false \
  -f block_creations=false \
  -f required_conversation_resolution=true \
  -f lock_branch=false \
  -f allow_fork_syncing=false

echo "✅ Branch protection rules with status checks applied successfully!"
echo ""
echo "Protection rules for '${BRANCH}' branch:"
echo "  ✓ Require pull request reviews (1 approving review)"
echo "  ✓ Require status checks to pass before merging"
echo "  ✓ Require branches to be up to date before merging"
echo "  ✓ Dismiss stale reviews on new commits"
echo "  ✓ Require conversation resolution before merging"
echo "  ✓ Prevent force pushes"
echo "  ✓ Prevent branch deletion"
echo ""
echo "Status checks required:"
echo "  - test"
echo "  - lint"
echo "  - build"
echo "  - deploy-staging"
echo ""
echo "⚠️  NOTE: Update the 'contexts' array in this script to match your actual"
echo "    GitHub Actions workflow job names."
echo ""
echo "You can view the settings at:"
echo "https://github.com/${REPO}/settings/branches"
