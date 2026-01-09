#!/bin/bash
# Setup branch protection rules for main branch
# Repository: sholaj/vibotaj-website-revamp-rep

set -euo pipefail

REPO="sholaj/vibotaj-website-revamp-rep"
BRANCH="main"

echo "Setting up branch protection for ${BRANCH} on ${REPO}..."

# Branch protection rules configuration
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "/repos/${REPO}/branches/${BRANCH}/protection" \
  -f required_status_checks='null' \
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
  -f required_conversation_resolution=false \
  -f lock_branch=false \
  -f allow_fork_syncing=false

echo "✅ Branch protection rules applied successfully!"
echo ""
echo "Protection rules for '${BRANCH}' branch:"
echo "  ✓ Require pull request reviews (1 approving review)"
echo "  ✓ Dismiss stale reviews on new commits"
echo "  ✓ Prevent force pushes"
echo "  ✓ Prevent branch deletion"
echo ""
echo "You can view the settings at:"
echo "https://github.com/${REPO}/settings/branches"
