# Branch Protection Setup Scripts

Scripts to manage GitHub branch protection rules for the `main` branch using the GitHub CLI (`gh`).

## Prerequisites

1. **Install GitHub CLI** (if not already installed):
   ```bash
   brew install gh
   ```

2. **Authenticate with GitHub**:
   ```bash
   gh auth login
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x scripts/setup-branch-protection.sh
   chmod +x scripts/setup-branch-protection-with-checks.sh
   chmod +x scripts/view-branch-protection.sh
   chmod +x scripts/remove-branch-protection.sh
   ```

## Available Scripts

### 1. Basic Branch Protection (Recommended to Start)

**File:** `setup-branch-protection.sh`

Applies the following rules to the `main` branch:
- Require pull request reviews (1 approving review required)
- Dismiss stale reviews when new commits are pushed
- Prevent force pushes
- Prevent branch deletion

**Usage:**
```bash
./scripts/setup-branch-protection.sh
```

### 2. Branch Protection with Status Checks

**File:** `setup-branch-protection-with-checks.sh`

Includes all basic protections PLUS:
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Require conversation resolution before merging

**Before using:** Edit the script to match your actual GitHub Actions workflow job names:
```bash
# Edit line with "contexts" array to match your workflow jobs
"contexts": ["test", "lint", "build", "deploy-staging"]
```

**Usage:**
```bash
./scripts/setup-branch-protection-with-checks.sh
```

### 3. View Current Protection Rules

**File:** `view-branch-protection.sh`

Displays the current branch protection configuration.

**Usage:**
```bash
./scripts/view-branch-protection.sh
```

### 4. Remove Branch Protection

**File:** `remove-branch-protection.sh`

Removes all branch protection rules (use with caution).

**Usage:**
```bash
./scripts/remove-branch-protection.sh
```

## Recommended Workflow

### Step 1: Apply Basic Protection
Start with basic protection to ensure PRs are required:
```bash
./scripts/setup-branch-protection.sh
```

### Step 2: Verify Configuration
Check that the rules were applied correctly:
```bash
./scripts/view-branch-protection.sh
```

Or view in browser:
```
https://github.com/sholaj/vibotaj-website-revamp-rep/settings/branches
```

### Step 3: Add Status Checks (Optional)
If you have CI/CD workflows, upgrade to include status checks:

1. Check your GitHub Actions workflow job names:
   ```bash
   gh api repos/sholaj/vibotaj-website-revamp-rep/actions/workflows | jq '.workflows[].name'
   ```

2. Edit `setup-branch-protection-with-checks.sh` to include your job names

3. Apply the updated rules:
   ```bash
   ./scripts/setup-branch-protection-with-checks.sh
   ```

## What These Rules Prevent

### Without Protection (Current State)
- Anyone can push directly to `main`
- No code review required
- Force pushes allowed
- Branch can be deleted

### With Protection (After Setup)
- All changes must go through pull requests
- At least 1 approving review required
- Force pushes blocked
- Branch deletion blocked
- Optional: CI/CD checks must pass

## Troubleshooting

### Permission Denied
If you get a permission error:
```bash
# Re-authenticate with admin scope
gh auth refresh -s admin:org
```

### Status Check Not Found
If status checks fail to apply, the check names must match your GitHub Actions workflow job names exactly. Check your workflow files in `.github/workflows/`.

### View Raw Protection JSON
```bash
gh api repos/sholaj/vibotaj-website-revamp-rep/branches/main/protection
```

## Integration with GitOps Workflow

These protections enforce the GitOps workflow defined in `/Users/shola/Documents/vibotaj-website-revamp-rep/CLAUDE.md`:

```
feature branch → develop → staging → main → production
```

With branch protection:
1. Changes to `main` require PR from `develop`
2. PR requires review and approval
3. CI/CD checks must pass (if configured)
4. No accidental force pushes or deletions

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub CLI API Documentation](https://cli.github.com/manual/gh_api)
- [Branch Protection API Reference](https://docs.github.com/en/rest/branches/branch-protection)
