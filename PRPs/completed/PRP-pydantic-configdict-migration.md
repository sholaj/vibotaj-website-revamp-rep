# PRP: Pydantic v2 ConfigDict Migration

**Status:** ✅ Completed (2026-01-17)
**Priority:** Medium (Tech Debt Reduction)
**Estimated Effort:** 1-2 hours
**Risk Level:** Low

---

## Problem Statement

The codebase is running Pydantic v2.12.5 but still uses the deprecated `class Config:` pattern from Pydantic v1. This generates deprecation warnings during test runs:

```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated,
use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0.
```

When Pydantic v3 is released, these patterns will break the application.

---

## Solution

Migrate all `class Config:` usages to `model_config = ConfigDict(...)` pattern.

### Before (Deprecated)
```python
class MyModel(BaseModel):
    name: str

    class Config:
        from_attributes = True
```

### After (Pydantic v2)
```python
from pydantic import ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
```

---

## Scope

### Files to Update (21 occurrences)

| File | Count | Complexity |
|------|-------|------------|
| `app/config.py` | 1 | Low |
| `app/schemas/shipment.py` | 6 | Low |
| `app/schemas/invitation.py` | 2 | Low |
| `app/schemas/eudr.py` | 1 | Low |
| `app/schemas/document.py` | 1 | Low |
| `app/schemas/bol.py` | 1 | Medium (has json_schema_extra) |
| `app/schemas/organization.py` | 4 | Low |
| `app/schemas/user.py` | 3 | Low |
| `app/routers/notifications.py` | 1 | Low |
| `app/routers/audit.py` | 1 | Low |

### Out of Scope
- `@validator` to `@field_validator` migration (separate PRP)
- `.dict()` to `.model_dump()` migration (separate PRP)
- Strict mode enablement (separate PRP)

---

## Implementation Plan

### Phase 1: Schema Files (15 occurrences)

1. **Add ConfigDict import** to each schema file:
   ```python
   from pydantic import BaseModel, ConfigDict
   ```

2. **Convert each class** following this pattern:
   ```python
   # Before
   class Config:
       from_attributes = True

   # After
   model_config = ConfigDict(from_attributes=True)
   ```

3. **Handle json_schema_extra** in `bol.py`:
   ```python
   model_config = ConfigDict(
       from_attributes=True,
       json_schema_extra={...}
   )
   ```

### Phase 2: Router Files (2 occurrences)

Update inline Pydantic models in:
- `routers/notifications.py`
- `routers/audit.py`

### Phase 3: Config File (1 occurrence)

Update `app/config.py` Settings class (uses pydantic_settings).

---

## Validation

### Test Command
```bash
cd tracehub/backend
python -m pytest -v 2>&1 | grep -c "PydanticDeprecatedSince20"
# Should return 0 after migration
```

### Success Criteria
1. All tests pass
2. Zero Pydantic deprecation warnings
3. API endpoints return same responses
4. No runtime errors

---

## Rollback Plan

If issues arise:
1. Revert commit with `git revert`
2. No database changes required
3. No frontend changes required

---

## References

- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [ConfigDict Documentation](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict)

---

**Document Version:** 1.0
**Created:** 2026-01-17
**Author:** Claude Opus 4.5
