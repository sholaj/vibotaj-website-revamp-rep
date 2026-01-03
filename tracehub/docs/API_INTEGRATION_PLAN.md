# TraceHub API Integration Plan

**Document Version:** 1.0
**Date:** 2026-01-03
**Author:** API Architecture Team
**Status:** Draft - Ready for Review

---

## Executive Summary

This document outlines the API architecture and implementation plan for the remaining integration features in TraceHub. Based on analysis of the existing codebase, we have identified four major feature areas requiring completion, with detailed endpoint specifications, data models, complexity estimates, and sprint allocation recommendations.

---

## Current State Assessment

### Existing Infrastructure

| Component | Status | Location |
|-----------|--------|----------|
| Container Tracking Router | Partial | `/app/routers/tracking.py` |
| Webhook Handler | Complete | `/app/routers/webhooks.py` |
| JSONCargo Client | Complete | `/app/services/jsoncargo.py` |
| Vizion Client | Partial | `/app/services/vizion.py` |
| Audit Pack Generation | Complete | `/app/services/audit_pack.py` |
| EUDR Compliance Service | Complete | `/app/services/eudr.py` |
| Notification Service | Complete | `/app/services/notifications.py` |

### Gaps Identified

1. **Vizion API Integration** - Subscribe/unsubscribe not fully implemented
2. **AI-Augmented Workflows** - No LLM integration exists
3. **Email Notifications** - SMTP service not implemented
4. **Enhanced Audit Pack** - Missing digital signatures and timestamps

---

## Feature 1: Complete Container Tracking Integration

### 1.1 Vizion API Full Integration

**Priority:** High
**Complexity:** Medium (M)
**Estimated Story Points:** 13

#### New Endpoints

```
POST   /api/tracking/subscribe/{shipment_id}
DELETE /api/tracking/unsubscribe/{shipment_id}
GET    /api/tracking/subscriptions
POST   /api/tracking/poll/{shipment_id}
GET    /api/tracking/carriers
```

#### Endpoint Specifications

**POST /api/tracking/subscribe/{shipment_id}**

Subscribe a shipment's container to Vizion tracking.

```json
// Request
{
  "carrier_code": "MAEU",           // Optional: SCAC code
  "webhook_url_override": "string", // Optional: Custom webhook URL
  "notification_preferences": {
    "on_departure": true,
    "on_arrival": true,
    "on_delay": true,
    "eta_threshold_hours": 24
  }
}

// Response 201
{
  "subscription_id": "sub_abc123",
  "shipment_id": "uuid",
  "container_number": "MRSU3452572",
  "status": "active",
  "carrier": {
    "code": "MAEU",
    "name": "Maersk"
  },
  "subscribed_at": "2026-01-03T10:00:00Z",
  "webhook_configured": true
}

// Response 409
{
  "error": "already_subscribed",
  "message": "Container is already subscribed for tracking",
  "existing_subscription_id": "sub_xyz789"
}
```

**DELETE /api/tracking/unsubscribe/{shipment_id}**

Unsubscribe a container from tracking updates.

```json
// Response 200
{
  "message": "Unsubscribed successfully",
  "subscription_id": "sub_abc123",
  "container_number": "MRSU3452572",
  "unsubscribed_at": "2026-01-03T15:00:00Z",
  "final_status": "in_transit"
}
```

**GET /api/tracking/subscriptions**

List all active tracking subscriptions.

```json
// Response 200
{
  "total": 15,
  "active": 12,
  "paused": 3,
  "subscriptions": [
    {
      "subscription_id": "sub_abc123",
      "shipment_id": "uuid",
      "shipment_reference": "VIBO-2026-001",
      "container_number": "MRSU3452572",
      "carrier": "MAERSK",
      "status": "active",
      "last_event": {
        "type": "departed",
        "timestamp": "2026-01-02T08:00:00Z",
        "location": "Lagos, Nigeria"
      },
      "eta": "2026-01-15T12:00:00Z"
    }
  ]
}
```

**POST /api/tracking/poll/{shipment_id}**

Manually trigger a tracking data refresh (for non-webhook scenarios).

```json
// Response 200
{
  "shipment_id": "uuid",
  "container_number": "MRSU3452572",
  "polling_result": "updated",
  "events_added": 2,
  "new_events": [
    {
      "type": "transshipment",
      "timestamp": "2026-01-03T06:00:00Z",
      "location": "Algeciras, Spain"
    }
  ],
  "current_status": "in_transit",
  "eta": "2026-01-15T12:00:00Z"
}
```

**GET /api/tracking/carriers**

List supported carriers and their capabilities.

```json
// Response 200
{
  "carriers": [
    {
      "code": "MAEU",
      "name": "Maersk",
      "container_prefixes": ["MRSU", "MSKU", "MAEU"],
      "tracking_supported": true,
      "webhook_supported": true,
      "bol_lookup": true
    }
  ]
}
```

#### Data Models Required

```python
# New model: TrackingSubscription
class TrackingSubscription(Base):
    __tablename__ = "tracking_subscriptions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID, ForeignKey("shipments.id"), nullable=False)
    external_subscription_id = Column(String(100))  # Vizion's subscription ID
    provider = Column(String(50), default="vizion")  # vizion | jsoncargo
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    carrier_code = Column(String(10))
    webhook_url = Column(String(500))
    notification_preferences = Column(JSONB, default={})
    last_poll_at = Column(DateTime)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    CANCELLED = "cancelled"
```

#### Vizion Service Enhancements

```python
# Enhanced vizion.py
class VizionClient:
    async def subscribe_container(self, container_number: str, ...) -> Dict
    async def unsubscribe_container(self, subscription_id: str) -> Dict
    async def get_subscription_status(self, subscription_id: str) -> Dict
    async def list_subscriptions(self) -> List[Dict]
    async def configure_webhook(self, webhook_url: str) -> Dict
```

### 1.2 Webhook Handler Enhancements

**Priority:** High
**Complexity:** Small (S)
**Estimated Story Points:** 5

#### Enhanced Webhook Processing

The existing webhook handler at `/api/webhooks/vizion` and `/api/webhooks/carrier` is functional. Enhancements needed:

1. **Signature Verification** - Currently optional, make configurable per provider
2. **Retry Logic** - Add dead-letter queue for failed webhook processing
3. **Rate Limiting** - Protect against webhook flooding

#### New Endpoints

```
GET  /api/webhooks/logs
POST /api/webhooks/replay/{event_id}
GET  /api/webhooks/health
```

**GET /api/webhooks/logs**

View webhook processing history.

```json
// Query Parameters
?status=processed|failed|pending
&provider=vizion|carrier|jsoncargo
&from=2026-01-01T00:00:00Z
&to=2026-01-03T23:59:59Z
&limit=50
&offset=0

// Response 200
{
  "total": 150,
  "logs": [
    {
      "id": "wh_log_123",
      "provider": "vizion",
      "container_number": "MRSU3452572",
      "event_type": "VESSEL_DEPARTED",
      "status": "processed",
      "received_at": "2026-01-02T08:15:32Z",
      "processed_at": "2026-01-02T08:15:33Z",
      "processing_time_ms": 145,
      "shipment_updated": true
    }
  ]
}
```

#### Data Model

```python
class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False)
    container_number = Column(String(20))
    event_type = Column(String(50))
    status = Column(Enum(WebhookStatus))
    payload = Column(JSONB)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    processing_time_ms = Column(Integer)
```

---

## Feature 2: Audit Pack Generation Enhancements

### 2.1 Enhanced Audit Pack with Digital Signatures

**Priority:** Medium
**Complexity:** Medium (M)
**Estimated Story Points:** 8

The existing audit pack service (`/app/services/audit_pack.py`) generates ZIP bundles with PDF summaries. Enhancements needed:

#### New Endpoints

```
GET    /api/shipments/{shipment_id}/audit-pack/preview
POST   /api/shipments/{shipment_id}/audit-pack/generate
GET    /api/shipments/{shipment_id}/audit-pack/verify
GET    /api/audit-packs
```

**POST /api/shipments/{shipment_id}/audit-pack/generate**

Generate a signed, timestamped audit pack.

```json
// Request
{
  "include_sections": {
    "shipment_summary": true,
    "documents": true,
    "tracking_history": true,
    "eudr_compliance": true,
    "origin_data": true
  },
  "format": "zip",           // zip | pdf_bundle
  "sign": true,              // Digital signature
  "timestamp_authority": "rfc3161",  // RFC 3161 timestamp
  "watermark": "AUDIT COPY"
}

// Response 202
{
  "job_id": "audit_job_123",
  "status": "processing",
  "estimated_completion_seconds": 30,
  "poll_url": "/api/audit-packs/audit_job_123/status"
}

// Completed Response (polling result)
{
  "job_id": "audit_job_123",
  "status": "completed",
  "download_url": "/api/audit-packs/audit_job_123/download",
  "expires_at": "2026-01-04T10:00:00Z",
  "audit_pack": {
    "id": "ap_abc123",
    "shipment_reference": "VIBO-2026-001",
    "generated_at": "2026-01-03T10:30:00Z",
    "file_size_bytes": 15234567,
    "document_count": 8,
    "signature": {
      "algorithm": "SHA256withRSA",
      "signed_by": "TraceHub Compliance System",
      "signed_at": "2026-01-03T10:30:00Z",
      "certificate_serial": "abc123..."
    },
    "timestamp": {
      "authority": "DigiCert TSA",
      "timestamp": "2026-01-03T10:30:01Z",
      "token": "base64_encoded_token"
    },
    "checksum": {
      "algorithm": "SHA-256",
      "value": "abc123def456..."
    }
  }
}
```

**GET /api/shipments/{shipment_id}/audit-pack/verify**

Verify an existing audit pack's integrity.

```json
// Request Query Parameter
?checksum=abc123def456...

// Response 200
{
  "valid": true,
  "verification_details": {
    "checksum_valid": true,
    "signature_valid": true,
    "timestamp_valid": true,
    "certificate_not_expired": true,
    "document_count_matches": true
  },
  "verified_at": "2026-01-03T11:00:00Z"
}
```

**GET /api/audit-packs**

List generated audit packs.

```json
// Response 200
{
  "total": 25,
  "audit_packs": [
    {
      "id": "ap_abc123",
      "shipment_id": "uuid",
      "shipment_reference": "VIBO-2026-001",
      "generated_at": "2026-01-03T10:30:00Z",
      "generated_by": "demo@vibotaj.com",
      "file_size_bytes": 15234567,
      "document_count": 8,
      "is_signed": true,
      "download_count": 3,
      "last_downloaded_at": "2026-01-03T14:00:00Z"
    }
  ]
}
```

#### Data Model

```python
class AuditPack(Base):
    __tablename__ = "audit_packs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID, ForeignKey("shipments.id"), nullable=False)
    file_path = Column(String(500))
    file_size_bytes = Column(Integer)
    checksum_sha256 = Column(String(64))
    document_count = Column(Integer)

    # Signing metadata
    is_signed = Column(Boolean, default=False)
    signature_algorithm = Column(String(50))
    signature_value = Column(Text)
    signer_certificate = Column(Text)

    # Timestamping
    timestamp_authority = Column(String(100))
    timestamp_token = Column(Text)

    # Audit
    generated_by = Column(String(100))
    generated_at = Column(DateTime, default=datetime.utcnow)
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime)
```

---

## Feature 3: AI-Augmented Workflows

### 3.1 Document Completeness & Discrepancy Detection

**Priority:** High
**Complexity:** Large (L)
**Estimated Story Points:** 21

This is a new capability requiring LLM integration for intelligent document analysis.

#### New Endpoints

```
POST   /api/ai/analyze/shipment/{shipment_id}
POST   /api/ai/analyze/document/{document_id}
POST   /api/ai/check/completeness/{shipment_id}
POST   /api/ai/check/discrepancies/{shipment_id}
POST   /api/ai/generate/summary/{shipment_id}
GET    /api/ai/analyses
GET    /api/ai/usage
```

**POST /api/ai/analyze/shipment/{shipment_id}**

Comprehensive AI analysis of a shipment's documents and data.

```json
// Request
{
  "analysis_types": [
    "document_completeness",
    "data_consistency",
    "compliance_check",
    "risk_assessment"
  ],
  "include_recommendations": true,
  "language": "en"
}

// Response 200
{
  "analysis_id": "ai_analysis_123",
  "shipment_id": "uuid",
  "shipment_reference": "VIBO-2026-001",
  "analyzed_at": "2026-01-03T10:00:00Z",
  "model_used": "claude-3-haiku",
  "analysis_results": {
    "document_completeness": {
      "score": 85,
      "status": "mostly_complete",
      "present_documents": [
        "bill_of_lading",
        "commercial_invoice",
        "packing_list",
        "certificate_of_origin"
      ],
      "missing_documents": [
        {
          "type": "phytosanitary_certificate",
          "required_for": "agro_export_to_eu",
          "criticality": "high",
          "recommendation": "Upload phytosanitary certificate issued by NAQS before shipment departure"
        }
      ],
      "optional_documents_missing": [
        "insurance_certificate"
      ]
    },
    "data_consistency": {
      "score": 92,
      "discrepancies_found": 2,
      "discrepancies": [
        {
          "id": "disc_001",
          "type": "quantity_mismatch",
          "severity": "warning",
          "description": "Net weight on packing list (25,000 kg) differs from commercial invoice (25,500 kg)",
          "documents_involved": ["packing_list", "commercial_invoice"],
          "recommendation": "Verify correct weight and update documents for consistency"
        },
        {
          "id": "disc_002",
          "type": "hs_code_mismatch",
          "severity": "error",
          "description": "HS code 050400 on invoice does not match 050590 on certificate of origin",
          "documents_involved": ["commercial_invoice", "certificate_of_origin"],
          "recommendation": "Critical: HS codes must match across all documents for customs clearance"
        }
      ]
    },
    "compliance_check": {
      "eudr_status": "incomplete",
      "issues": [
        {
          "regulation": "EUDR",
          "article": "Article 9",
          "issue": "Origin geolocation missing for 1 of 2 product batches",
          "criticality": "high"
        }
      ]
    },
    "risk_assessment": {
      "overall_risk": "medium",
      "risk_factors": [
        {
          "factor": "incomplete_documentation",
          "risk_level": "medium",
          "impact": "Potential customs delays"
        }
      ]
    }
  },
  "human_readable_summary": "Shipment VIBO-2026-001 is 85% document-complete with 2 data discrepancies requiring attention. Critical: HS code mismatch between invoice and certificate of origin must be resolved before shipment. Missing phytosanitary certificate is required for EU agro imports.",
  "recommendations": [
    {
      "priority": 1,
      "action": "Resolve HS code discrepancy between commercial invoice and certificate of origin",
      "deadline": "Before customs filing"
    },
    {
      "priority": 2,
      "action": "Upload phytosanitary certificate",
      "deadline": "Before shipment departure"
    },
    {
      "priority": 3,
      "action": "Reconcile weight discrepancy on packing list",
      "deadline": "Before B/L issuance"
    }
  ],
  "tokens_used": {
    "input": 4500,
    "output": 1200
  }
}
```

**POST /api/ai/check/completeness/{shipment_id}**

Quick document completeness check.

```json
// Request
{
  "destination_country": "DE",
  "product_hs_codes": ["050400"],
  "incoterms": "CIF"
}

// Response 200
{
  "shipment_id": "uuid",
  "is_complete": false,
  "completeness_score": 75,
  "required_documents": {
    "total": 8,
    "present": 6,
    "missing": 2,
    "invalid": 0
  },
  "missing": [
    {
      "document_type": "phytosanitary_certificate",
      "reason": "Required for agro products (HS 05) imported to Germany",
      "regulation": "EU Plant Health Regulation 2016/2031"
    },
    {
      "document_type": "eudr_due_diligence",
      "reason": "Required for commodities under EUDR since Dec 30, 2024",
      "regulation": "Regulation (EU) 2023/1115"
    }
  ],
  "checked_at": "2026-01-03T10:00:00Z"
}
```

**POST /api/ai/check/discrepancies/{shipment_id}**

Check for data discrepancies across documents.

```json
// Response 200
{
  "shipment_id": "uuid",
  "discrepancies_found": true,
  "total_discrepancies": 3,
  "discrepancies": [
    {
      "id": "disc_001",
      "type": "quantity_mismatch",
      "severity": "warning",
      "field": "net_weight_kg",
      "values": {
        "commercial_invoice": 25500,
        "packing_list": 25000,
        "bill_of_lading": 25500
      },
      "expected_consistency": true,
      "recommendation": "Verify correct weight. Packing list shows 500kg less than other documents."
    },
    {
      "id": "disc_002",
      "type": "date_inconsistency",
      "severity": "info",
      "field": "issue_date",
      "values": {
        "commercial_invoice": "2025-12-10",
        "certificate_of_origin": "2025-12-15"
      },
      "expected_consistency": false,
      "recommendation": "Issue dates vary - acceptable if within shipment timeline"
    }
  ],
  "fields_checked": [
    "shipper_name", "consignee_name", "product_description", "hs_code",
    "net_weight_kg", "gross_weight_kg", "quantity", "container_number",
    "vessel_name", "port_of_loading", "port_of_discharge"
  ],
  "checked_at": "2026-01-03T10:00:00Z"
}
```

**POST /api/ai/generate/summary/{shipment_id}**

Generate human-readable shipment summary for buyers.

```json
// Request
{
  "audience": "buyer",        // buyer | supplier | compliance
  "format": "paragraph",      // paragraph | bullet_points
  "include_sections": [
    "status",
    "documents",
    "compliance",
    "timeline"
  ],
  "language": "en"
}

// Response 200
{
  "shipment_id": "uuid",
  "shipment_reference": "VIBO-2026-001",
  "summary": "Shipment VIBO-2026-001 containing 25,000 kg of cattle hooves (HS 050400) is currently in transit from Lagos, Nigeria to Hamburg, Germany. The container MRSU3452572 departed on December 13, 2025 aboard vessel RHINE MAERSK and is expected to arrive on January 15, 2026. Documentation is 85% complete with 6 of 8 required documents uploaded and validated. Two items require attention: the phytosanitary certificate has not yet been uploaded, and there is a minor weight discrepancy between the packing list and commercial invoice. EUDR compliance status is pending verification of origin coordinates for batch #2. No customs holds or delays have been reported.",
  "key_facts": {
    "container": "MRSU3452572",
    "product": "Cattle Hooves, 25,000 kg",
    "origin": "Lagos, Nigeria",
    "destination": "Hamburg, Germany",
    "eta": "2026-01-15",
    "status": "In Transit",
    "documents_complete": "6/8",
    "compliance_flags": 2
  },
  "generated_at": "2026-01-03T10:00:00Z",
  "tokens_used": 850
}
```

#### Data Models

```python
class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID, ForeignKey("shipments.id"))
    document_id = Column(UUID, ForeignKey("documents.id"))
    analysis_type = Column(String(50), nullable=False)
    model_used = Column(String(100))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    result = Column(JSONB)
    cached = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    requested_by = Column(String(100))

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100))
    endpoint = Column(String(100))
    model = Column(String(100))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    cost_usd = Column(Numeric(10, 6))
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Service Architecture

```python
# services/ai_analyzer.py

class AIAnalyzerService:
    """AI-powered document analysis service."""

    def __init__(self, db: Session):
        self.db = db
        self.client = anthropic.Anthropic()  # or openai.OpenAI()
        self.cache_ttl = 3600  # Cache results for 1 hour

    async def analyze_shipment(
        self,
        shipment_id: UUID,
        analysis_types: List[str]
    ) -> AnalysisResult:
        """Comprehensive shipment analysis."""
        pass

    async def check_document_completeness(
        self,
        shipment_id: UUID,
        destination: str,
        hs_codes: List[str]
    ) -> CompletenessResult:
        """Check required documents based on trade route."""
        pass

    async def detect_discrepancies(
        self,
        shipment_id: UUID
    ) -> DiscrepancyResult:
        """Compare data across documents for consistency."""
        pass

    async def generate_summary(
        self,
        shipment_id: UUID,
        audience: str,
        language: str
    ) -> str:
        """Generate human-readable summary."""
        pass

    def _build_document_context(
        self,
        shipment: Shipment,
        documents: List[Document]
    ) -> str:
        """Build context string from shipment data for LLM."""
        pass
```

#### Configuration Requirements

```python
# config.py additions
class Settings(BaseSettings):
    # AI Configuration
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ai_model: str = "claude-3-haiku"
    ai_max_tokens: int = 4096
    ai_temperature: float = 0.3
    ai_cache_enabled: bool = True
    ai_rate_limit_requests_per_minute: int = 60
```

---

## Feature 4: Email Notification Service

### 4.1 SMTP Integration & Templates

**Priority:** Medium
**Complexity:** Medium (M)
**Estimated Story Points:** 8

#### New Endpoints

```
POST   /api/notifications/email/send
POST   /api/notifications/email/test
GET    /api/notifications/email/templates
PUT    /api/notifications/preferences
GET    /api/notifications/preferences
```

**POST /api/notifications/email/send**

Send an email notification (admin only).

```json
// Request
{
  "recipients": ["buyer@example.com"],
  "cc": ["compliance@vibotaj.com"],
  "template": "shipment_status_update",
  "template_data": {
    "shipment_reference": "VIBO-2026-001",
    "status": "in_transit",
    "eta": "2026-01-15T12:00:00Z"
  },
  "priority": "normal"
}

// Response 202
{
  "message_id": "email_msg_123",
  "status": "queued",
  "recipients": ["buyer@example.com"],
  "template": "shipment_status_update",
  "scheduled_at": "2026-01-03T10:00:00Z"
}
```

**PUT /api/notifications/preferences**

Update user notification preferences.

```json
// Request
{
  "email_enabled": true,
  "in_app_enabled": true,
  "email_address": "user@example.com",
  "preferences": {
    "shipment_departed": { "email": true, "in_app": true },
    "shipment_arrived": { "email": true, "in_app": true },
    "shipment_delivered": { "email": true, "in_app": true },
    "eta_changed": { "email": true, "in_app": true },
    "document_uploaded": { "email": false, "in_app": true },
    "document_validated": { "email": false, "in_app": true },
    "compliance_alert": { "email": true, "in_app": true },
    "expiry_warning": { "email": true, "in_app": true }
  },
  "digest_frequency": "daily",  // immediate | daily | weekly
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00",
    "timezone": "Europe/Berlin"
  }
}

// Response 200
{
  "message": "Preferences updated",
  "preferences": { ... }
}
```

**GET /api/notifications/email/templates**

List available email templates.

```json
// Response 200
{
  "templates": [
    {
      "id": "shipment_status_update",
      "name": "Shipment Status Update",
      "description": "Notification when shipment status changes",
      "variables": [
        "shipment_reference",
        "status",
        "container_number",
        "eta",
        "location"
      ],
      "preview_url": "/api/notifications/email/templates/shipment_status_update/preview"
    },
    {
      "id": "eta_changed",
      "name": "ETA Change Alert",
      "description": "Notification when estimated arrival changes",
      "variables": [
        "shipment_reference",
        "old_eta",
        "new_eta",
        "delay_hours"
      ]
    },
    {
      "id": "document_action_required",
      "name": "Document Action Required",
      "description": "Alert for missing or expiring documents",
      "variables": [
        "shipment_reference",
        "document_type",
        "action_required",
        "deadline"
      ]
    },
    {
      "id": "compliance_alert",
      "name": "Compliance Alert",
      "description": "EUDR or other compliance issues",
      "variables": [
        "shipment_reference",
        "alert_type",
        "description",
        "required_action"
      ]
    },
    {
      "id": "weekly_digest",
      "name": "Weekly Digest",
      "description": "Summary of all shipment activity",
      "variables": [
        "period_start",
        "period_end",
        "active_shipments",
        "events_summary"
      ]
    }
  ]
}
```

#### Data Models

```python
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    message_id = Column(String(100))  # SMTP message ID
    recipient = Column(String(255), nullable=False)
    cc = Column(JSONB, default=[])
    template = Column(String(100))
    subject = Column(String(500))
    status = Column(Enum(EmailStatus))  # queued, sent, delivered, bounced, failed
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    error_message = Column(Text)
    opened_at = Column(DateTime)  # If tracking pixel used
    clicked_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserNotificationPreferences(Base):
    __tablename__ = "user_notification_preferences"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    email_address = Column(String(255))
    preferences = Column(JSONB, default={})
    digest_frequency = Column(String(20), default="immediate")
    quiet_hours = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class EmailStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"
```

#### Service Architecture

```python
# services/email_service.py

class EmailService:
    """SMTP email service with template support."""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_address = settings.email_from_address
        self.templates_dir = Path(__file__).parent / "email_templates"

    async def send_email(
        self,
        to: List[str],
        template: str,
        template_data: Dict[str, Any],
        cc: List[str] = None,
        priority: str = "normal"
    ) -> EmailSendResult:
        """Send templated email."""
        pass

    async def send_notification_email(
        self,
        notification: Notification,
        user_prefs: UserNotificationPreferences
    ) -> Optional[EmailSendResult]:
        """Send email for in-app notification if user prefers."""
        pass

    def render_template(
        self,
        template: str,
        data: Dict[str, Any]
    ) -> Tuple[str, str]:
        """Render HTML and plain text versions."""
        pass

    async def send_digest(
        self,
        user_id: str,
        period: str  # daily | weekly
    ) -> EmailSendResult:
        """Send notification digest."""
        pass
```

#### Configuration Requirements

```python
# config.py additions
class Settings(BaseSettings):
    # Email Configuration
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from_address: str = "notifications@tracehub.vibotaj.com"
    email_from_name: str = "TraceHub Notifications"
    email_reply_to: str = "support@vibotaj.com"
```

---

## Dependencies Between Features

```
                    Feature Dependencies
                    ====================

[Feature 1: Tracking]
        |
        v
[Feature 2: Audit Pack] <---- Needs tracking events for complete audit trail
        |
        v
[Feature 3: AI Workflows] <-- Needs document/tracking data for analysis
        |
        v
[Feature 4: Email Service] <-- Triggered by all other features
```

### Dependency Matrix

| Feature | Depends On | Blocks |
|---------|------------|--------|
| 1. Tracking | None | 2, 3, 4 |
| 2. Audit Pack | 1 (partial) | 3 |
| 3. AI Workflows | 1, 2 | 4 |
| 4. Email Service | None (can run parallel) | None |

---

## Complexity Estimates Summary

| Feature | Size | Story Points | Dependencies |
|---------|------|--------------|--------------|
| 1.1 Vizion Full Integration | M | 13 | None |
| 1.2 Webhook Enhancements | S | 5 | 1.1 |
| 2.1 Enhanced Audit Pack | M | 8 | 1.1 partial |
| 3.1 AI Document Analysis | L | 21 | 2.1 |
| 4.1 Email Service | M | 8 | None |

**Total Estimated Story Points:** 55

---

## Recommended Sprint Allocation

### Sprint 3 (Current + 2 weeks): Foundation

**Goal:** Complete tracking infrastructure and email service foundation

| Task | Points | Assignee |
|------|--------|----------|
| 1.1 Vizion Subscribe/Unsubscribe | 8 | Backend |
| 1.2 Webhook Log & Replay | 5 | Backend |
| 4.1 Email Service Setup (SMTP, templates) | 5 | Backend |
| Database migrations | 2 | Backend |

**Sprint Total:** 20 points

**Deliverables:**
- Full Vizion API integration with subscribe/unsubscribe
- Webhook logging and replay capability
- Basic email sending with 3 templates

### Sprint 4 (Weeks 3-4): AI Integration

**Goal:** Implement AI-powered document analysis

| Task | Points | Assignee |
|------|--------|----------|
| 3.1a Document Completeness Check | 8 | Backend |
| 3.1b Discrepancy Detection | 8 | Backend |
| 3.1c Summary Generation | 5 | Backend |
| 1.1 Polling & Carriers endpoint | 5 | Backend |

**Sprint Total:** 26 points

**Deliverables:**
- AI document completeness checking
- Cross-document discrepancy detection
- Human-readable summary generation
- Tracking polling for non-webhook scenarios

### Sprint 5 (Weeks 5-6): Polish & Compliance

**Goal:** Enhanced audit pack and email preferences

| Task | Points | Assignee |
|------|--------|----------|
| 2.1 Digital Signatures | 5 | Backend |
| 2.1 RFC 3161 Timestamps | 3 | Backend |
| 4.1 Email Preferences | 3 | Backend |
| 4.1 Digest Emails | 3 | Backend |
| Integration Testing | 5 | QA |

**Sprint Total:** 19 points

**Deliverables:**
- Signed and timestamped audit packs
- User notification preferences
- Daily/weekly digest emails
- Full integration test suite

---

## External Service Integrations Required

### 1. Container Tracking APIs

| Provider | Purpose | Cost Model | Status |
|----------|---------|------------|--------|
| Vizion | Primary tracking + webhooks | Per container/month | API key configured |
| JSONCargo | Backup/secondary | Per request | API key configured |

### 2. AI/LLM Provider

| Provider | Model | Cost | Recommendation |
|----------|-------|------|----------------|
| Anthropic | claude-3-haiku | $0.25/1M tokens | **Recommended** - Best for document analysis |
| Anthropic | claude-3-sonnet | $3.00/1M tokens | For complex analysis |
| OpenAI | gpt-4o-mini | $0.15/1M tokens | Alternative |

### 3. Email Service

| Provider | Features | Cost | Recommendation |
|----------|----------|------|----------------|
| SendGrid | SMTP + Templates | Free tier: 100/day | **Recommended** |
| AWS SES | SMTP + Bulk | $0.10/1000 | Cost-effective at scale |
| Mailgun | SMTP + Webhooks | Free tier: 5000/mo | Good for POC |

### 4. Digital Signature / Timestamping

| Provider | Service | Cost | Recommendation |
|----------|---------|------|----------------|
| DigiCert | TSA (RFC 3161) | Included with cert | **Recommended** |
| FreeTSA | TSA | Free | POC only |
| GlobalSign | Document signing | Per signature | If legal signing needed |

---

## API Security Considerations

### Authentication

All new endpoints follow existing JWT authentication pattern:
- `Depends(get_current_user)` for read operations
- `Depends(get_current_active_user)` for write operations

### Rate Limiting

Existing middleware configuration extended:

```python
endpoint_limits = {
    "/api/ai/": (10, 60),           # 10 AI requests per minute
    "/api/notifications/email/": (20, 60),  # 20 email requests per minute
    "/api/tracking/subscribe": (5, 60),     # 5 subscriptions per minute
}
```

### Webhook Security

- HMAC signature verification (existing)
- IP allowlist for Vizion webhooks
- Rate limiting on webhook endpoints

### Data Privacy

- AI prompts should not include PII unless necessary
- Email logs should mask recipient addresses in GET requests
- Audit pack downloads should be logged

---

## Error Response Standards

All new endpoints follow existing error format:

```json
{
  "detail": {
    "error_code": "TRACKING_SUBSCRIPTION_FAILED",
    "message": "Failed to subscribe container for tracking",
    "errors": [
      {
        "field": "carrier_code",
        "message": "Carrier SCAC code not supported",
        "value": "INVALID"
      }
    ],
    "request_id": "req_abc123",
    "timestamp": "2026-01-03T10:00:00Z"
  }
}
```

### Error Codes by Feature

| Feature | Error Code | HTTP Status | Description |
|---------|------------|-------------|-------------|
| Tracking | SUBSCRIPTION_EXISTS | 409 | Already subscribed |
| Tracking | CARRIER_NOT_SUPPORTED | 400 | Unknown carrier |
| Tracking | VIZION_API_ERROR | 502 | Upstream API failure |
| AI | ANALYSIS_TIMEOUT | 504 | LLM response timeout |
| AI | QUOTA_EXCEEDED | 429 | AI usage limit reached |
| Email | SMTP_ERROR | 502 | Email delivery failed |
| Audit | SIGNING_FAILED | 500 | Digital signature error |

---

## Testing Requirements

### Unit Tests

- Service layer tests for all new services
- Mock external APIs (Vizion, Anthropic, SMTP)

### Integration Tests

- End-to-end tracking subscription flow
- AI analysis with real document data
- Email delivery verification

### Performance Tests

- AI endpoint response times < 30 seconds
- Audit pack generation < 60 seconds
- Webhook processing < 500ms

---

## Monitoring & Observability

### New Metrics

```python
# Tracking
tracking_subscriptions_active = Gauge("tracking_subscriptions_active")
tracking_events_received = Counter("tracking_events_received")
webhook_processing_time = Histogram("webhook_processing_seconds")

# AI
ai_requests_total = Counter("ai_requests_total", ["endpoint", "model"])
ai_tokens_used = Counter("ai_tokens_used", ["model"])
ai_latency = Histogram("ai_latency_seconds", ["endpoint"])

# Email
emails_sent_total = Counter("emails_sent_total", ["template", "status"])
email_delivery_rate = Gauge("email_delivery_rate")
```

### Alerts

- Vizion API errors > 5 in 5 minutes
- AI latency > 30 seconds
- Email bounce rate > 10%
- Webhook backlog > 100 messages

---

## Next Steps

1. **Review & Approve** - Architecture review with team
2. **Sprint Planning** - Break down into tasks
3. **Database Migrations** - Create migration scripts
4. **Service Scaffolding** - Create service stubs
5. **External API Setup** - Configure provider accounts
6. **Development** - Implement per sprint plan

---

## Appendix A: OpenAPI Specification Excerpts

See `/docs/openapi/tracking.yaml`, `/docs/openapi/ai.yaml`, `/docs/openapi/notifications.yaml` for full specifications.

## Appendix B: Email Template Examples

See `/app/services/email_templates/` for HTML templates.

## Appendix C: AI Prompt Templates

See `/app/services/ai_prompts/` for LLM prompt templates.
