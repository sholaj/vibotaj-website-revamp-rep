# PRP: Pydantic v2 Validator Migration

**Status:** ✅ Completed (2026-01-17)
**Priority:** Medium (Tech Debt Reduction)
**Estimated Effort:** 30 minutes
**Risk Level:** Low
**Depends On:** PRP-pydantic-configdict-migration (optional, can be done independently)

---

## Problem Statement

The codebase uses the deprecated `@validator` decorator from Pydantic v1. While Pydantic v2 supports it for backwards compatibility, it will be removed in v3.

Current usage in `app/schemas/shipment.py`:
```python
@validator('event_type', pre=True)
def convert_event_type(cls, v):
    ...

@validator('document_type', 'status', pre=True)
def convert_enums(cls, v):
    ...
```

---

## Solution

Migrate `@validator` to `@field_validator` with updated syntax.

### Key Differences

| Pydantic v1 (`@validator`) | Pydantic v2 (`@field_validator`) |
|----------------------------|----------------------------------|
| `@validator('field')` | `@field_validator('field')` |
| `def method(cls, v)` | `def method(cls, v)` |
| `pre=True` | `mode='before'` |
| `always=True` | `mode='wrap'` or explicit check |
| `each_item=True` | Handled differently |

### Before (Deprecated)
```python
from pydantic import validator

class EventInfo(BaseModel):
    event_type: str

    @validator('event_type', pre=True)
    def convert_event_type(cls, v):
        # conversion logic
        return result
```

### After (Pydantic v2)
```python
from pydantic import field_validator

class EventInfo(BaseModel):
    event_type: str

    @field_validator('event_type', mode='before')
    @classmethod
    def convert_event_type(cls, v):
        # conversion logic
        return result
```

---

## Scope

### Files to Update

| File | Validators | Notes |
|------|------------|-------|
| `app/schemas/shipment.py` | 2 | `convert_event_type`, `convert_enums` |

### Already Using v2 Pattern
These files already use `@field_validator` correctly:
- `app/schemas/bol.py`
- `app/schemas/invitation.py`
- `app/schemas/organization.py`
- `app/schemas/user.py`

---

## Implementation Plan

### Step 1: Update Import
```python
# Before
from pydantic import BaseModel, validator, field_validator

# After
from pydantic import BaseModel, field_validator
```

### Step 2: Update EventInfo Validator (line ~167)

```python
# Before
@validator('event_type', pre=True)
def convert_event_type(cls, v):
    """Convert backend UPPERCASE enum to frontend lowercase event type."""
    status_to_type_map = {...}
    if hasattr(v, 'value'):
        v = v.value
    v = str(v) if v is not None else "OTHER"
    return status_to_type_map.get(v, "unknown")

# After
@field_validator('event_type', mode='before')
@classmethod
def convert_event_type(cls, v):
    """Convert backend UPPERCASE enum to frontend lowercase event type."""
    status_to_type_map = {...}
    if hasattr(v, 'value'):
        v = v.value
    v = str(v) if v is not None else "OTHER"
    return status_to_type_map.get(v, "unknown")
```

### Step 3: Update DocumentInfo Validator (line ~203)

```python
# Before
@validator('document_type', 'status', pre=True)
def convert_enums(cls, v):
    if hasattr(v, 'value'):
        return v.value
    return v

# After
@field_validator('document_type', 'status', mode='before')
@classmethod
def convert_enums(cls, v):
    if hasattr(v, 'value'):
        return v.value
    return v
```

---

## Validation

### Test Command
```bash
cd tracehub/backend
python -m pytest tests/test_bol_schema.py -v
python -m pytest -k "shipment" -v
```

### Manual Verification
```bash
# Start backend and test API response
curl -s https://tracehub.vibotaj.com/api/shipments/{id} | jq '.events[0]'
# Should return event_type in lowercase format
```

### Success Criteria
1. All tests pass
2. Events API returns correct `event_type` values
3. No validator-related deprecation warnings

---

## Rollback Plan

If issues arise:
1. Revert commit with `git revert`
2. No database changes required
3. No frontend changes required

---

## References

- [Pydantic v2 Validators Guide](https://docs.pydantic.dev/latest/concepts/validators/)
- [Migration: validator to field_validator](https://docs.pydantic.dev/latest/migration/#validator-and-root_validator-are-deprecated)

---

**Document Version:** 1.0
**Created:** 2026-01-17
**Author:** Claude Opus 4.5
