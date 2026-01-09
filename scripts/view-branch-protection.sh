#!/bin/bash
# View current branch protection rules for main branch
# Repository: sholaj/vibotaj-website-revamp-rep

set -euo pipefail

REPO="sholaj/vibotaj-website-revamp-rep"
BRANCH="main"

echo "Fetching branch protection rules for ${BRANCH} on ${REPO}..."
echo ""

gh api \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "/repos/${REPO}/branches/${BRANCH}/protection" \
  --jq '
    "Branch: " + .url,
    "",
    "Required Pull Request Reviews:",
    "  Approving reviews required: " + (.required_pull_request_reviews.required_approving_review_count | tostring),
    "  Dismiss stale reviews: " + (.required_pull_request_reviews.dismiss_stale_reviews | tostring),
    "  Require code owner reviews: " + (.required_pull_request_reviews.require_code_owner_reviews | tostring),
    "",
    "Required Status Checks:",
    if .required_status_checks then
      "  Strict: " + (.required_status_checks.strict | tostring),
      "  Contexts: " + (.required_status_checks.contexts | join(", "))
    else
      "  None configured"
    end,
    "",
    "Force Push Protection:",
    "  Allow force pushes: " + (.allow_force_pushes.enabled | tostring),
    "  Allow deletions: " + (.allow_deletions.enabled | tostring),
    "",
    "Other Settings:",
    "  Enforce admins: " + (.enforce_admins.enabled | tostring),
    "  Required linear history: " + (.required_linear_history.enabled | tostring),
    "  Require conversation resolution: " + (.required_conversation_resolution.enabled | tostring)
  '
