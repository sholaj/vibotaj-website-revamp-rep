# PRD-021: Third-Party Integrations (Customs + Banking APIs)

## Problem Statement

TraceHub manages export shipments from Nigeria to the EU, but customs declarations and trade finance operations happen outside the system — manually via NCS portals, phone calls to freight forwarders, and bank visits for LC verification. This creates data silos, missed deadlines, and no audit trail. Automating customs pre-clearance checks, duty calculations, and banking operations (LC verification, payment status, forex rates) directly within TraceHub eliminates manual steps and provides a single source of truth for trade operations.

## Solution

Build a provider-agnostic integration framework using the Protocol pattern (same as `EmailBackend`, `LLMBackend`, `StorageBackend`). Two integration domains:

1. **Customs:** Pre-clearance checks, duty calculations, export declaration submission (NCS, SON)
2. **Banking:** Letter of Credit verification, payment status tracking, forex rate lookups

Since NCS/SON and Nigerian bank APIs have limited public documentation, the v1 implementation builds the full abstraction layer with **mock backends** for development and testing. Real provider implementations will be added when API access is obtained. The infrastructure (credential storage, webhook receivers, logging, frontend dashboard) is production-ready from day one.

## Architecture

```
CustomsBackend (Protocol)
├── MockCustomsBackend      ← dev/test (simulates NCS responses)
├── NCSCustomsBackend       ← future (Nigeria Customs Service)
└── SONCustomsBackend       ← future (Standards Organisation of Nigeria)

BankingBackend (Protocol)
├── MockBankingBackend      ← dev/test (simulates bank responses)
├── GTBankBackend           ← future (Guaranty Trust Bank)
└── UBABackend              ← future (United Bank for Africa)

IntegrationService
├── Credential storage (encrypted, org-scoped)
├── API call logging (audit trail)
├── Webhook receivers (customs + banking callbacks)
└── Retry + circuit breaker pattern
```

## Acceptance Criteria

### Backend — Customs Protocol
- [ ] `CustomsBackend` Protocol with `check_pre_clearance()`, `calculate_duty()`, `submit_declaration()`, `get_declaration_status()`, `is_available()`, `get_provider_name()`, `get_status()`
- [ ] `MockCustomsBackend` with configurable responses and realistic delays
- [ ] `get_customs_backend()` factory (singleton, reads `customs_provider` from Settings)
- [ ] Pre-clearance check accepts HS code + origin country, returns clearance status + required docs
- [ ] Duty calculation accepts HS code + CIF value + quantity, returns duty breakdown (import duty, VAT, surcharges)
- [ ] Declaration submission accepts shipment data, returns declaration reference + status

### Backend — Banking Protocol
- [ ] `BankingBackend` Protocol with `verify_lc()`, `get_payment_status()`, `get_forex_rate()`, `is_available()`, `get_provider_name()`, `get_status()`
- [ ] `MockBankingBackend` with configurable responses
- [ ] `get_banking_backend()` factory (singleton, reads `banking_provider` from Settings)
- [ ] LC verification accepts LC number + issuing bank, returns validity + terms
- [ ] Payment status accepts payment reference, returns status + amount + date
- [ ] Forex rate accepts currency pair, returns buy/sell rates + timestamp

### Backend — Integration Infrastructure
- [ ] `integration_credentials` table (org-scoped, encrypted API keys)
- [ ] `integration_logs` table (API call audit trail with request/response)
- [ ] Webhook endpoints: `POST /webhooks/customs`, `POST /webhooks/banking`
- [ ] HMAC signature verification on webhook endpoints (reuse existing pattern)
- [ ] API endpoints for integration management (CRUD, test connection, status)
- [ ] All endpoints filter by `organization_id` (multi-tenancy)
- [ ] Config: `customs_provider`, `banking_provider`, `customs_enabled`, `banking_enabled`

### Frontend
- [ ] Integrations dashboard at `/settings/integrations`
- [ ] Connection status cards (customs + banking) with connected/disconnected indicators
- [ ] Test connection button per integration
- [ ] Recent sync activity log (last 10 API calls with status)
- [ ] React Query hooks: `useIntegrations()`, `useTestConnection()`, `useIntegrationLogs()`

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/integrations | List org integration configs + status |
| PUT | /api/integrations/{type} | Update integration config (admin only) |
| POST | /api/integrations/{type}/test | Test connection (returns success/error) |
| GET | /api/integrations/{type}/logs | Recent API call logs |
| POST | /api/integrations/customs/pre-clearance | Run pre-clearance check |
| POST | /api/integrations/customs/duty-calc | Calculate duties |
| POST | /api/integrations/customs/declare | Submit export declaration |
| GET | /api/integrations/customs/declarations/{ref} | Get declaration status |
| POST | /api/integrations/banking/verify-lc | Verify Letter of Credit |
| GET | /api/integrations/banking/payment/{ref} | Get payment status |
| GET | /api/integrations/banking/forex/{pair} | Get forex rate (e.g., NGN-EUR) |
| POST | /webhooks/customs | Receive customs status updates |
| POST | /webhooks/banking | Receive banking payment updates |

## Database Changes

### New table: `integration_credentials`
```sql
CREATE TABLE integration_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_type VARCHAR(50) NOT NULL,  -- 'customs', 'banking'
    provider VARCHAR(50) NOT NULL,          -- 'ncs', 'son', 'gtbank', 'uba', 'mock'
    config JSON NOT NULL DEFAULT '{}',      -- provider-specific config (base_url, etc.)
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_tested_at TIMESTAMPTZ,
    last_test_success BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(organization_id, integration_type)
);
```

### New table: `integration_logs`
```sql
CREATE TABLE integration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_type VARCHAR(50) NOT NULL,  -- 'customs', 'banking'
    provider VARCHAR(50) NOT NULL,
    method VARCHAR(100) NOT NULL,           -- 'check_pre_clearance', 'verify_lc', etc.
    request_summary VARCHAR(500),           -- human-readable summary
    status VARCHAR(20) NOT NULL,            -- 'success', 'error', 'timeout'
    response_time_ms INTEGER,
    error_message TEXT,
    shipment_id UUID,                       -- optional link to shipment
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_integration_logs_org_type ON integration_logs(organization_id, integration_type);
CREATE INDEX idx_integration_logs_created ON integration_logs(created_at DESC);
```

## Config Changes (`config.py`)

```python
# Customs Integration (PRD-021)
customs_provider: str = "mock"  # "ncs", "son", "mock"
customs_enabled: bool = False   # Master switch
customs_api_key: SecretStr = SecretStr("")
customs_api_url: str = ""

# Banking Integration (PRD-021)
banking_provider: str = "mock"  # "gtbank", "uba", "mock"
banking_enabled: bool = False   # Master switch
banking_api_key: SecretStr = SecretStr("")
banking_api_url: str = ""
```

## Frontend Changes

### New page: `/settings/integrations`
- Two cards: Customs + Banking
- Each card shows: provider name, connection status (green/red dot), last tested time
- "Configure" button opens credential form
- "Test Connection" button sends test request

### New files
- `v2/frontend/src/app/settings/integrations/page.tsx`
- `v2/frontend/src/lib/api/integration-types.ts`
- `v2/frontend/src/lib/api/integrations.ts`
- `v2/frontend/src/components/settings/integration-card.tsx`
- `v2/frontend/src/components/settings/integration-log-table.tsx`

## Compliance Impact

None. Customs and banking integrations are operational tools that assist with existing compliance workflows. No EUDR impact. Horn/hoof (0506/0507) products are NOT affected — they don't require EUDR fields regardless of customs integration status. Checked against `docs/COMPLIANCE_MATRIX.md`.

## Dependencies

- PRD-004 (FastAPI on Railway) — backend hosting
- PRD-009 (Design system) — Shadcn components
- PRD-020 (Email notifications) — notify on customs/banking status changes

## Non-Goals (v1)

- Real NCS/SON API implementation (blocked on API access documentation)
- Real bank API implementation (requires bank partnership agreement)
- Automatic customs filing (manual trigger only for v1)
- Multi-currency payment initiation
- Integration marketplace / third-party plugin system
- OAuth2 flows for bank connections
