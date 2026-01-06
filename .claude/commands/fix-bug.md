Fix bug: $ARGUMENTS

## TDD Approach (REQUIRED)

1. **Write failing test FIRST**
   - Reproduce the bug in a test
   - Verify the test fails with the bug
   - This confirms you understand the issue

2. **Implement minimal fix**
   - Make the smallest change that fixes the bug
   - Avoid refactoring unrelated code
   - Keep changes surgical and precise

3. **Verify fix**
   - Run the test - it should now pass
   - Run full test suite to catch regressions
   - Run: `make test && make lint`

4. **Update documentation**
   - Update CHANGELOG.md in "Fixed" section
   - Add comments if the fix is non-obvious
   - Update relevant documentation if needed

## Steps:

### 1. Understand the Bug
- [ ] Reproduce the bug locally
- [ ] Identify root cause
- [ ] Check if it's related to EUDR/compliance logic
- [ ] Determine scope of impact

### 2. Write Failing Test
```python
# Example: test_bug_fix.py
def test_horn_hoof_should_not_require_eudr():
    """Bug: Horn/hoof products incorrectly require EUDR fields."""
    product = create_product(hs_code="0506.10")
    
    # This should pass but currently fails
    assert product.eudr_required is False
    assert "geolocation" not in product.required_fields
```

Run test to verify it fails:
```bash
cd tracehub/backend
pytest tests/test_bug_fix.py -v
```

### 3. Implement Fix
- Make minimal code change to fix the issue
- Example: Update compliance logic to check HS code

### 4. Verify Fix
```bash
# Run the specific test
pytest tests/test_bug_fix.py -v

# Run full test suite
make test

# Run linter
make lint
```

### 5. Update CHANGELOG.md
```markdown
### Fixed
- Bug where horn/hoof products incorrectly required EUDR fields
```

## NEVER Skip:
- ❌ Do NOT skip writing the failing test
- ❌ Do NOT refactor unrelated code
- ❌ Do NOT make changes without tests
- ❌ Do NOT skip CHANGELOG.md update

## Security Check:
- [ ] Does fix introduce security vulnerabilities?
- [ ] Are error messages safe (no data leakage)?
- [ ] Is input validation still working?

---

**Output:** Bug fixed with test coverage and documentation updated
