Review code: $ARGUMENTS

## Code Review Checklist

### 1. Code Quality
- [ ] Follows existing patterns and conventions
- [ ] Code is readable and well-structured
- [ ] No unnecessary complexity
- [ ] DRY (Don't Repeat Yourself) principle followed
- [ ] Proper error handling

### 2. Type Safety
**Python:**
- [ ] Type hints present for public functions
- [ ] Docstrings follow Google style
- [ ] No `# type: ignore` without justification

**TypeScript:**
- [ ] No `any` types (use `unknown` if needed)
- [ ] Proper interface/type definitions
- [ ] Strict mode enabled

### 3. Testing
- [ ] Tests added for new features
- [ ] Tests updated for changes
- [ ] Edge cases covered
- [ ] TDD approach used for bug fixes
- [ ] Test coverage maintained or improved

### 4. Security - CRITICAL
- [ ] NO hardcoded secrets (API keys, passwords, tokens)
- [ ] NO credentials in code or comments
- [ ] Proper input validation and sanitization
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Error messages don't leak sensitive data
- [ ] Authentication/authorization properly implemented

### 5. Compliance (Product Features)
- [ ] **CRITICAL:** EUDR NOT added to horn/hoof (HS 0506/0507)
- [ ] Geolocation only for EUDR-applicable products
- [ ] Compliance matrix consulted (`docs/COMPLIANCE_MATRIX.md`)
- [ ] Document requirements match HS code

### 6. Documentation
- [ ] CHANGELOG.md updated
- [ ] README updated if public API changed
- [ ] Comments added for complex logic
- [ ] API documentation updated if endpoints changed
- [ ] Architecture decisions documented (ADR) if significant

### 7. Performance
- [ ] No N+1 query problems
- [ ] Appropriate database indexes used
- [ ] No unnecessary API calls
- [ ] Pagination used for large datasets
- [ ] Efficient algorithms used

### 8. Database
- [ ] Migrations created for schema changes
- [ ] Migrations are reversible
- [ ] No data loss in migrations
- [ ] Foreign key constraints properly defined

### 9. Git Hygiene
- [ ] Commit messages follow convention (feat/fix/docs/etc.)
- [ ] No merge conflicts
- [ ] No debug code or console.logs left in
- [ ] No commented-out code blocks
- [ ] `.gitignore` properly configured

### 10. Dependencies
- [ ] No unnecessary dependencies added
- [ ] Dependencies are from trusted sources
- [ ] Version pinning appropriate
- [ ] License compatibility checked

## Review Process:

1. **Quick Scan**
   ```bash
   git diff main...HEAD --name-only
   git diff main...HEAD
   ```

2. **Check for Secrets**
   ```bash
   git diff main...HEAD | grep -i "api_key\|password\|secret\|token"
   ```

3. **Run Tests**
   ```bash
   make test && make lint
   ```

4. **Check EUDR Logic** (if compliance-related)
   - Verify horn/hoof products don't have EUDR fields
   - Check `docs/COMPLIANCE_MATRIX.md` was consulted

5. **Verify Documentation**
   - Check CHANGELOG.md updated
   - Check relevant docs updated

## Output Format:

### ✅ APPROVED
All checks passed. Ready to merge.

**OR**

### ⚠️ CHANGES REQUESTED

**Critical Issues:**
1. [Issue 1 - with specific file/line]
2. [Issue 2 - with specific file/line]

**Suggestions:**
1. [Suggestion 1]
2. [Suggestion 2]

**Nice to Have:**
1. [Optional improvement 1]
2. [Optional improvement 2]

---

**Reviewer:** [Your Name]  
**Date:** [Date]  
**Branch:** [Branch Name]
