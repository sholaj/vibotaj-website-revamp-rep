Generate a PRP (Product Requirements Prompt) for: $ARGUMENTS

## Steps:

1. **Read and understand the feature request**
   - Clarify requirements and scope
   - Identify stakeholders and users

2. **Check compliance requirements** (if applicable)
   - Review `docs/COMPLIANCE_MATRIX.md` for HS code requirements
   - Check if feature affects horn/hoof products (HS 0506/0507)
   - Verify no EUDR fields are added to non-EUDR products

3. **Review existing decisions**
   - Check `docs/decisions/` for architectural constraints
   - Ensure consistency with existing patterns

4. **Create PRP document**
   - Create file in `PRPs/active/<feature-name>.md`
   - Include these sections:
     - **Overview**: Brief description and goals
     - **Requirements**: Functional and non-functional requirements
     - **Technical Approach**: Implementation strategy
     - **Files to Modify**: List of files that will change
     - **Test Requirements**: Test cases to add
     - **Compliance Check**: EUDR verification (if product-related)
     - **Dependencies**: External dependencies or prerequisites
     - **Acceptance Criteria**: Definition of done

5. **CRITICAL CHECKS**
   - If feature affects horn/hoof (HS 0506/0507): NO EUDR fields ever
   - If feature affects cocoa (HS 1801): EUDR fields required
   - All changes must maintain backward compatibility
   - Security implications documented

## Template:

```markdown
# PRP: [Feature Name]

**Status:** Draft  
**Priority:** [P0/P1/P2]  
**Sprint:** [Sprint Number]

## Overview

[Brief description and business value]

## Requirements

### Functional
- [ ] Requirement 1
- [ ] Requirement 2

### Non-Functional
- [ ] Performance requirements
- [ ] Security requirements

## Technical Approach

[High-level implementation strategy]

## Files to Modify

- `file/path/one.py` - [description of changes]
- `file/path/two.tsx` - [description of changes]

## Test Requirements

- [ ] Unit tests for [component]
- [ ] Integration tests for [flow]
- [ ] E2E tests for [user journey]

## Compliance Check

**Product HS Codes Affected:** [list]  
**EUDR Applicable:** [Yes/No]  
**Required Documents:** [list from COMPLIANCE_MATRIX.md]

## Dependencies

- [Dependency 1]
- [Dependency 2]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All tests pass
- [ ] Documentation updated

## Security Considerations

[Any security implications]

## Rollout Plan

[Deployment strategy]
```

---

**Output:** PRP file created in `PRPs/active/<feature-name>.md`
