#!/bin/bash
# Remove branch protection rules from main branch
# Repository: sholaj/vibotaj-website-revamp-rep
# Use with caution!

set -euo pipefail

REPO="sholaj/vibotaj-website-revamp-rep"
BRANCH="main"

echo "⚠️  WARNING: This will remove ALL branch protection rules from ${BRANCH}!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Removing branch protection from ${BRANCH} on ${REPO}..."

gh api \
  --method DELETE \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "/repos/${REPO}/branches/${BRANCH}/protection"

echo "✅ Branch protection rules removed."
