# BoL Parsing & Compliance Engine - Implementation Plan

**PRP:** `PRPs/active/PRP-bol-parsing-compliance-engine.md`
**Sprint:** 12
**TDD Approach:** Write tests first (RED), then implement (GREEN), then refactor

---

## Overview

This plan implements a system to parse Bill of Lading documents into canonical JSON format and run a deterministic compliance rules engine against the parsed data.

### Key Components
1. **Canonical BoL Schema** - Pydantic models for standardized BoL data
2. **BoL Parser Service** - Extract structured data from BoL text/PDF
3. **Rules Engine** - Evaluate compliance rules against BoL data
4. **Compliance Decisions** - APPROVE / HOLD / REJECT with explanations

---

## Phase 1: Canonical BoL Schema (Backend)

### TEST-001: Write Schema Tests First
- [ ] Create `tracehub/backend/tests/test_bol_schema.py` with:
  - [ ] `test_bol_schema_validates_required_fields()` - shipper, consignee, vessel required
  - [ ] `test_bol_schema_validates_container_format()` - ISO 6346 validation
  - [ ] `test_bol_schema_handles_optional_fields()` - port_of_loading optional
  - [ ] `test_bol_schema_serializes_to_json()` - Can serialize/deserialize
  - [ ] `test_bol_schema_from_dict()` - Create from dictionary
- [ ] Run tests - expect FAIL (schema doesn't exist)

### IMPL-001: Create Canonical BoL Schema
- [ ] Create `tracehub/backend/app/schemas/bol.py`:
  ```python
  class BolParty(BaseModel):
      name: str
      address: Optional[str]
      country: Optional[str]

  class BolContainer(BaseModel):
      number: str  # ISO 6346 format
      seal_number: Optional[str]
      type: Optional[str]  # 20GP, 40HC, etc.
      weight_kg: Optional[float]

  class BolCargo(BaseModel):
      description: str
      hs_code: Optional[str]
      quantity: Optional[float]
      unit: Optional[str]
      gross_weight_kg: Optional[float]
      net_weight_kg: Optional[float]

  class CanonicalBoL(BaseModel):
      bol_number: str
      shipper: BolParty
      consignee: BolParty
      notify_party: Optional[BolParty]
      vessel_name: Optional[str]
      voyage_number: Optional[str]
      port_of_loading: Optional[str]
      port_of_discharge: Optional[str]
      place_of_delivery: Optional[str]
      date_of_issue: Optional[date]
      shipped_on_board_date: Optional[date]
      containers: List[BolContainer]
      cargo: List[BolCargo]
      freight_terms: Optional[str]  # PREPAID, COLLECT
      raw_text: Optional[str]
      confidence_score: float = 0.0
  ```
- [ ] Run tests - should PASS

---

## Phase 2: BoL Parser Service (Backend)

### TEST-002: Write Parser Tests First
- [ ] Create `tracehub/backend/tests/test_bol_parser.py` with:
  - [ ] `test_parse_bol_extracts_shipper()` - Extract shipper name and address
  - [ ] `test_parse_bol_extracts_consignee()` - Extract consignee details
  - [ ] `test_parse_bol_extracts_container()` - Extract container number
  - [ ] `test_parse_bol_extracts_vessel()` - Extract vessel name and voyage
  - [ ] `test_parse_bol_extracts_ports()` - Extract loading/discharge ports
  - [ ] `test_parse_bol_extracts_cargo()` - Extract cargo description
  - [ ] `test_parse_bol_returns_confidence()` - Returns confidence score
  - [ ] `test_parse_bol_handles_missing_fields()` - Graceful degradation
- [ ] Run tests - expect FAIL (parser doesn't exist)

### IMPL-002: Create BoL Parser Service
- [ ] Create `tracehub/backend/app/services/bol_parser.py`:
  ```python
  class BolParser:
      """Parse Bill of Lading documents into canonical format."""

      # Regex patterns for common BoL fields
      PATTERNS = {
          'bol_number': [
              r'B/L\s*(?:No\.?|Number)?\s*:?\s*([A-Z0-9-]+)',
              r'Bill\s+of\s+Lading\s*:?\s*([A-Z0-9-]+)',
          ],
          'container': [
              r'Container\s*(?:No\.?)?\s*:?\s*([A-Z]{4}\d{7})',
              r'Equipment\s*(?:No\.?)?\s*:?\s*([A-Z]{4}\d{7})',
          ],
          'vessel': [
              r'Vessel\s*(?:Name)?\s*:?\s*([A-Z][A-Za-z\s]+)',
              r'M/V\s+([A-Z][A-Za-z\s]+)',
          ],
          # ... more patterns
      }

      def parse(self, text: str) -> CanonicalBoL:
          """Parse BoL text into canonical schema."""
          pass

      def _extract_field(self, text: str, patterns: List[str]) -> Optional[str]:
          """Try multiple patterns to extract a field."""
          pass

      def _extract_party(self, text: str, label: str) -> BolParty:
          """Extract party (shipper/consignee) details."""
          pass

      def _calculate_confidence(self, bol: CanonicalBoL) -> float:
          """Calculate confidence score based on extracted fields."""
          pass
  ```
- [ ] Run tests - should PASS

---

## Phase 3: Rules Engine Core (Backend)

### TEST-003: Write Rules Engine Tests First
- [ ] Create `tracehub/backend/tests/test_rules_engine.py` with:
  - [ ] `test_rule_not_null_passes()` - NOT_NULL with value present
  - [ ] `test_rule_not_null_fails()` - NOT_NULL with value missing
  - [ ] `test_rule_in_list_passes()` - IN_LIST with matching value
  - [ ] `test_rule_in_list_fails()` - IN_LIST with non-matching value
  - [ ] `test_rule_equals_passes()` - EQUALS with matching value
  - [ ] `test_rule_range_passes()` - RANGE within bounds
  - [ ] `test_rule_regex_passes()` - REGEX pattern matches
  - [ ] `test_rule_date_order_passes()` - DATE_ORDER chronological
  - [ ] `test_evaluate_all_rules()` - Run all rules and aggregate
- [ ] Run tests - expect FAIL (engine doesn't exist)

### IMPL-003: Create Rules Engine
- [ ] Create `tracehub/backend/app/services/bol_rules/engine.py`:
  ```python
  class ConditionType(str, Enum):
      NOT_NULL = "NOT_NULL"
      IN_LIST = "IN_LIST"
      EQUALS = "EQUALS"
      RANGE = "RANGE"
      DATE_ORDER = "DATE_ORDER"
      REGEX = "REGEX"

  class RuleResult(BaseModel):
      rule_id: str
      rule_name: str
      passed: bool
      message: str
      severity: str  # ERROR, WARNING, INFO

  class RulesEngine:
      """Deterministic rules engine for BoL compliance."""

      def __init__(self, rules: List[ComplianceRule]):
          self.rules = rules

      def evaluate(self, bol: CanonicalBoL) -> List[RuleResult]:
          """Evaluate all rules against BoL data."""
          pass

      def _evaluate_rule(self, rule: ComplianceRule, bol: CanonicalBoL) -> RuleResult:
          """Evaluate a single rule."""
          pass

      def _get_field_value(self, bol: CanonicalBoL, field_path: str) -> Any:
          """Get nested field value using dot notation."""
          pass
  ```
- [ ] Create `tracehub/backend/app/services/bol_rules/__init__.py`
- [ ] Run tests - should PASS

---

## Phase 4: Compliance Rules Definition (Backend)

### TEST-004: Write Compliance Rules Tests First
- [ ] Create `tracehub/backend/tests/test_compliance_rules.py` with:
  - [ ] `test_shipper_name_required()` - Shipper must have name
  - [ ] `test_consignee_name_required()` - Consignee must have name
  - [ ] `test_container_iso6346_format()` - Container matches ISO 6346
  - [ ] `test_bol_number_required()` - BoL number is mandatory
  - [ ] `test_port_of_loading_required()` - Port of loading required
  - [ ] `test_cargo_description_required()` - Cargo description required
  - [ ] `test_shipped_date_before_discharge()` - Date order check
  - [ ] `test_compliance_decision_approve()` - All pass = APPROVE
  - [ ] `test_compliance_decision_hold()` - Warning = HOLD
  - [ ] `test_compliance_decision_reject()` - Error = REJECT
- [ ] Run tests - expect FAIL (rules not defined)

### IMPL-004: Define Compliance Rules
- [ ] Create `tracehub/backend/app/services/bol_rules/compliance_rules.py`:
  ```python
  # Standard BoL compliance rules
  STANDARD_BOL_RULES = [
      ComplianceRule(
          id="BOL-001",
          name="Shipper Name Required",
          field="shipper.name",
          condition=ConditionType.NOT_NULL,
          severity="ERROR",
          message="Shipper name is required"
      ),
      ComplianceRule(
          id="BOL-002",
          name="Consignee Name Required",
          field="consignee.name",
          condition=ConditionType.NOT_NULL,
          severity="ERROR",
          message="Consignee name is required"
      ),
      ComplianceRule(
          id="BOL-003",
          name="Container ISO 6346 Format",
          field="containers[0].number",
          condition=ConditionType.REGEX,
          value=r"^[A-Z]{4}\d{7}$",
          severity="WARNING",
          message="Container number should match ISO 6346 format"
      ),
      # ... more rules
  ]

  def get_compliance_decision(results: List[RuleResult]) -> str:
      """Determine overall compliance decision."""
      errors = [r for r in results if not r.passed and r.severity == "ERROR"]
      warnings = [r for r in results if not r.passed and r.severity == "WARNING"]

      if errors:
          return "REJECT"
      elif warnings:
          return "HOLD"
      return "APPROVE"
  ```
- [ ] Run tests - should PASS

---

## Phase 5: Database & API Integration (Backend)

### TEST-005: Write Integration Tests First
- [ ] Create `tracehub/backend/tests/test_bol_compliance_api.py` with:
  - [ ] `test_upload_bol_parses_document()` - Parse on upload
  - [ ] `test_parsed_data_stored_in_document()` - JSONB stored
  - [ ] `test_compliance_check_endpoint()` - POST /api/documents/{id}/compliance
  - [ ] `test_compliance_results_stored()` - Results in compliance_results table
  - [ ] `test_get_compliance_status()` - GET /api/documents/{id}/compliance
- [ ] Run tests - expect FAIL (not integrated)

### IMPL-005: Database Migration & API Endpoints
- [ ] Create migration `tracehub/backend/alembic/versions/20260116_add_bol_compliance_fields.py`:
  ```python
  def upgrade():
      # Add parsed BoL data to documents
      op.add_column('documents', sa.Column('bol_parsed_data', JSONB, nullable=True))

      # Create compliance_results table
      op.create_table(
          'compliance_results',
          sa.Column('id', UUID, primary_key=True),
          sa.Column('document_id', UUID, sa.ForeignKey('documents.id')),
          sa.Column('rule_id', sa.String(20)),
          sa.Column('rule_name', sa.String(100)),
          sa.Column('passed', sa.Boolean),
          sa.Column('message', sa.Text),
          sa.Column('severity', sa.String(20)),
          sa.Column('checked_at', sa.DateTime),
          sa.Column('organization_id', UUID, sa.ForeignKey('organizations.id'))
      )
  ```
- [ ] Update `tracehub/backend/app/models/document.py`:
  - [ ] Add `bol_parsed_data = Column(JSONB, nullable=True)`
- [ ] Create `tracehub/backend/app/models/compliance_result.py`
- [ ] In `tracehub/backend/app/routers/documents.py`:
  - [ ] Add POST `/api/documents/{id}/compliance` - Run compliance check
  - [ ] Add GET `/api/documents/{id}/compliance` - Get compliance status
- [ ] Run migration and tests - should PASS

---

## Phase 6: Frontend Integration

### TEST-006: Write Frontend Tests First
- [ ] Create `tracehub/frontend/src/components/__tests__/BolCompliancePanel.test.tsx`:
  - [ ] `test_renders_compliance_status()` - Shows APPROVE/HOLD/REJECT
  - [ ] `test_shows_rule_results()` - Lists individual rule results
  - [ ] `test_shows_parsed_fields()` - Displays extracted BoL data
  - [ ] `test_run_compliance_button()` - Triggers compliance check
- [ ] Run tests - expect FAIL (component doesn't exist)

### IMPL-006: Create Frontend Components
- [ ] Create `tracehub/frontend/src/components/BolCompliancePanel.tsx`:
  - [ ] Display compliance decision badge (APPROVE=green, HOLD=yellow, REJECT=red)
  - [ ] List rule results with pass/fail icons
  - [ ] Show parsed BoL fields in collapsible section
  - [ ] "Run Compliance Check" button
- [ ] Update `tracehub/frontend/src/types/index.ts`:
  - [ ] Add `BolParsedData`, `ComplianceResult`, `ComplianceDecision` types
- [ ] Update `tracehub/frontend/src/api/client.ts`:
  - [ ] Add `runComplianceCheck(documentId)` method
  - [ ] Add `getComplianceStatus(documentId)` method
- [ ] Integrate into `DocumentDetailModal.tsx` or document view
- [ ] Run tests - should PASS

---

## Phase 7: End-to-End Testing & Documentation

### TEST-007: E2E Tests
- [ ] Create `tracehub/backend/tests/test_bol_compliance_e2e.py`:
  - [ ] `test_full_workflow_approve()` - Upload valid BoL → APPROVE
  - [ ] `test_full_workflow_hold()` - BoL with warnings → HOLD
  - [ ] `test_full_workflow_reject()` - Invalid BoL → REJECT
- [ ] Manual testing with real BoL documents

### DOC-007: Documentation
- [ ] Update `docs/COMPLIANCE_MATRIX.md` with BoL rules
- [ ] Add API documentation for new endpoints
- [ ] Update CHANGELOG.md

---

## Test Commands

```bash
# Backend tests
cd tracehub/backend
pytest tests/test_bol_schema.py -v
pytest tests/test_bol_parser.py -v
pytest tests/test_rules_engine.py -v
pytest tests/test_compliance_rules.py -v
pytest tests/test_bol_compliance_api.py -v
pytest tests/test_bol_compliance_e2e.py -v
pytest -v  # All tests

# Frontend tests
cd tracehub/frontend
npm test -- BolCompliancePanel
npm test  # All tests
```

---

## Architecture Integration Points

### Existing Services to Extend
| Service | Location | Integration |
|---------|----------|-------------|
| `shipment_data_extractor.py` | `app/services/` | Use existing regex patterns |
| `document_classifier.py` | `app/services/` | Trigger parser for BILL_OF_LADING |
| `compliance.py` | `app/services/` | Integrate rules engine |

### New Files to Create
| File | Purpose |
|------|---------|
| `app/schemas/bol.py` | Canonical BoL Pydantic models |
| `app/services/bol_parser.py` | BoL text parsing service |
| `app/services/bol_rules/engine.py` | Rules engine core |
| `app/services/bol_rules/compliance_rules.py` | Rule definitions |
| `app/models/compliance_result.py` | Database model |

---

## Success Criteria

1. **Parser Accuracy**: >85% field extraction rate on test BoL documents
2. **Rules Coverage**: All standard BoL compliance requirements implemented
3. **Performance**: Compliance check completes in <2 seconds
4. **Test Coverage**: >90% for new code
5. **Zero Regression**: All existing tests pass

---

## Notes

- **TDD Approach**: Each phase starts with TEST- (write failing tests), then IMPL- (make tests pass)
- **Deterministic Rules**: No AI/ML for compliance decisions - pure rule evaluation
- **Graceful Degradation**: Parser should work with partial data, returning lower confidence
- **Multi-tenancy**: All compliance results scoped by organization_id
- **Audit Trail**: Compliance checks logged with timestamp and user
