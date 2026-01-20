# TraceHub Azure SaaS Migration Guide

> Mapping the "Super Pack" (Next.js + Supabase + Clerk + Sentry) to Azure Services

**Document Version:** 1.0
**Created:** 2026-01-20
**Status:** Planning

---

## Executive Summary

This document maps the recommended "super pack" SaaS stack to Azure equivalents, tailored for TraceHub's existing multi-tenant architecture. The goal is to transition from the current self-hosted POC (Hostinger VPS) to a scalable, enterprise-grade Azure infrastructure while preserving the robust business logic already implemented.

### Current State → Target State

| Component | Current (POC) | Super Pack | **Azure Equivalent** |
|-----------|--------------|------------|---------------------|
| Frontend | React 18 + Vite | Next.js | **Azure Static Web Apps** or **Azure Container Apps** |
| Backend API | FastAPI (Python) | Next.js API Routes | **Azure Container Apps** + **Azure Functions** |
| Database | PostgreSQL 15 (self-hosted) | Supabase | **Azure Database for PostgreSQL Flexible Server** |
| Auth | Custom JWT | Clerk | **Azure AD B2C** or **Clerk** (cloud-agnostic) |
| Realtime | None (polling) | Supabase Realtime | **Azure SignalR Service** |
| File Storage | Docker volumes | Supabase Storage | **Azure Blob Storage** |
| Edge Functions | None | Supabase Edge Functions | **Azure Functions** |
| Observability | Basic logging | Sentry | **Azure Application Insights** |
| CI/CD | GitHub Actions | GitHub Actions | **Azure DevOps** or **GitHub Actions** |
| Secrets | .env files | Vault | **Azure Key Vault** |

---

## 1. Application Hosting (Next.js → Azure)

### Option A: Azure Static Web Apps (Recommended for Start)

**Best for:** Hybrid static + serverless architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Azure Static Web Apps                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   Next.js App   │    │   Managed API Functions         │ │
│  │  (SSG/ISR/CSR)  │───>│   (Node.js serverless)          │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│           │                          │                       │
│           └──────────────────────────┼───────────────────────┤
│                                      ▼                       │
│                         ┌───────────────────────┐            │
│                         │  Azure CDN (built-in) │            │
│                         └───────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Built-in GitHub/Azure DevOps CI/CD
- Global CDN with edge caching
- Managed SSL certificates (automatic)
- Preview environments for PRs
- Custom domains support
- Authentication integration (Azure AD, GitHub, etc.)

**Pricing:** Free tier available; Standard ~$9/month

**Configuration:**
```yaml
# staticwebapp.config.json
{
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/api/*", "/_next/*"]
  },
  "routes": [
    {
      "route": "/api/*",
      "allowedRoles": ["authenticated"]
    }
  ],
  "responseOverrides": {
    "401": {
      "redirect": "/login",
      "statusCode": 302
    }
  }
}
```

### Option B: Azure Container Apps (Recommended for Full SSR)

**Best for:** Server-side rendering, complex API requirements

```
┌──────────────────────────────────────────────────────────────────┐
│                    Azure Container Apps Environment               │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐     ┌────────────────────────────────┐   │
│  │  Next.js Container │     │  FastAPI Backend Container     │   │
│  │  (SSR + API Routes)│────>│  (Existing Python logic)       │   │
│  │  Scale: 0-10       │     │  Scale: 1-5                    │   │
│  └────────────────────┘     └────────────────────────────────┘   │
│           │                              │                        │
│           └──────────────┬───────────────┘                        │
│                          ▼                                        │
│               ┌────────────────────┐                              │
│               │  Azure Front Door  │                              │
│               │  (CDN + WAF + SSL) │                              │
│               └────────────────────┘                              │
└──────────────────────────────────────────────────────────────────┘
```

**Advantages over Static Web Apps:**
- True SSR with Node.js runtime
- Scale to zero when idle
- Dapr integration for service communication
- Better for keeping FastAPI backend alongside Next.js
- Managed KEDA autoscaling

**Pricing:** Pay-per-use; ~$0.000024/vCPU-second

### Recommendation

**Phase 1:** Use **Azure Container Apps** to:
1. Keep existing FastAPI backend (preserve all business logic)
2. Add Next.js frontend container alongside
3. Migrate incrementally from React SPA to Next.js

**Phase 2:** Consider migrating some FastAPI endpoints to Next.js API Routes or Azure Functions for simpler operations.

---

## 2. Database (Supabase → Azure PostgreSQL)

### Azure Database for PostgreSQL Flexible Server

**Why Flexible Server over Single Server:**
- Better price/performance
- Zone-redundant HA
- Stop/start capability (cost savings)
- Intelligent performance recommendations
- Same-zone and cross-zone replicas

```
┌─────────────────────────────────────────────────────────────────┐
│              Azure Database for PostgreSQL                       │
│                    (Flexible Server)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Primary    │  │   Read       │  │   Automatic Backups  │   │
│  │   Instance   │──│   Replica    │  │   (35-day retention) │   │
│  │   (General   │  │   (optional) │  └──────────────────────┘   │
│  │    Purpose)  │  └──────────────┘                              │
│  └──────────────┘                                                │
│         │                                                        │
│         ├── Connection Pooling (PgBouncer built-in)              │
│         ├── Private Link (VNet integration)                      │
│         └── Microsoft Defender for Cloud                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Migration Path

**Current Schema (preserve entirely):**
```
users, organizations, organization_memberships, invitations
shipments, products, documents, document_issues, document_contents
container_events, origins, audit_logs
```

**Migration Steps:**
1. Create Azure PostgreSQL Flexible Server (General Purpose, 2 vCores)
2. Enable pgcrypto, uuid-ossp extensions (already used)
3. Use Azure Database Migration Service for zero-downtime migration
4. Update connection strings via Azure Key Vault
5. Enable row-level security policies (RLS) at database level

### Row-Level Security (RLS) Implementation

**Supabase-style RLS on Azure PostgreSQL:**

```sql
-- Enable RLS on shipments table
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their organization's shipments
CREATE POLICY shipments_org_isolation ON shipments
    USING (
        organization_id = current_setting('app.current_org_id')::uuid
        OR buyer_organization_id = current_setting('app.current_org_id')::uuid
    );

-- Set session variable in application code
SET app.current_org_id = 'org-uuid-here';
```

**FastAPI integration:**
```python
# In database session setup
async def set_tenant_context(db: AsyncSession, org_id: str):
    await db.execute(text(f"SET app.current_org_id = '{org_id}'"))
```

### Pricing Comparison

| Tier | vCores | RAM | Storage | Monthly Cost |
|------|--------|-----|---------|--------------|
| Burstable B1ms | 1 | 2 GB | 32 GB | ~$15 |
| General Purpose D2s_v3 | 2 | 8 GB | 64 GB | ~$100 |
| General Purpose D4s_v3 | 4 | 16 GB | 128 GB | ~$200 |

**Recommendation:** Start with General Purpose D2s_v3 for production.

---

## 3. Authentication (Clerk → Azure Options)

### Option A: Keep Clerk (Recommended)

**Why keep Clerk:**
- Already designed for multi-tenant SaaS
- Works on any cloud (not tied to Supabase)
- Excellent Next.js integration
- Organizations feature matches TraceHub's model
- Faster implementation time

**Azure + Clerk Architecture:**
```
┌───────────────────────────────────────────────────────────────┐
│                         User Request                          │
└───────────────────────────┬───────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                    Clerk Auth (SaaS)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐  │
│  │   Sign In   │  │Organizations│  │   Session Management  │  │
│  │   SSO/MFA   │  │   & Roles   │  │   JWT Tokens          │  │
│  └─────────────┘  └─────────────┘  └───────────────────────┘  │
└───────────────────────────┬───────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                Azure Container Apps (Next.js + FastAPI)        │
│                                                                │
│  1. Verify Clerk JWT                                           │
│  2. Extract org_id from Clerk session                          │
│  3. Set PostgreSQL RLS context                                 │
│  4. Query with automatic tenant isolation                      │
└───────────────────────────────────────────────────────────────┘
```

**Clerk → TraceHub Model Mapping:**
```typescript
// Clerk Organization → TraceHub Organization
clerk.organization.id     → organization.id
clerk.organization.name   → organization.name
clerk.organization.role   → organization_membership.org_role

// Clerk User → TraceHub User
clerk.user.id             → user.clerk_id (new field)
clerk.user.email          → user.email
clerk.user.orgMemberships → organization_memberships
```

**Migration Steps:**
1. Add `clerk_id` column to users table
2. Create Clerk webhook endpoint to sync users/orgs
3. Replace JWT auth with Clerk middleware
4. Update frontend to use Clerk components

### Option B: Azure AD B2C

**When to choose Azure AD B2C:**
- Enterprise customers require Azure AD SSO
- Compliance requires Microsoft-backed auth
- Want unified Azure billing

**Azure AD B2C Architecture:**
```
┌───────────────────────────────────────────────────────────────┐
│                     Azure AD B2C Tenant                        │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────┐ │
│  │   User Flows        │  │   Custom Policies (IEF)         │ │
│  │   - Sign up/Sign in │  │   - Multi-tenant isolation      │ │
│  │   - Password reset  │  │   - Custom claims mapping       │ │
│  │   - Profile edit    │  │   - Organization assignment     │ │
│  └─────────────────────┘  └─────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐ │
│  │   Identity          │  │   API Connectors                │ │
│  │   Providers         │  │   - Validate email domain       │ │
│  │   - Local accounts  │  │   - Assign to organization      │ │
│  │   - Enterprise SSO  │  │   - Custom attributes           │ │
│  └─────────────────────┘  └─────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

**Challenges with Azure AD B2C:**
- Organizations feature requires custom implementation
- More complex setup than Clerk
- Custom policies (XML-based) have steep learning curve
- Multi-tenant organization management is DIY

**Pricing:**
- First 50,000 MAU free
- ~$0.00325/MAU after (Standard tier)

### Recommendation

**Use Clerk** for TraceHub because:
1. Built-in organization management matches your multi-tenancy model
2. Faster time-to-market
3. Better developer experience
4. Works seamlessly with Azure infrastructure
5. Can add Azure AD as identity provider later for enterprise SSO

---

## 4. Realtime (Supabase Realtime → Azure SignalR)

### Azure SignalR Service

**Purpose:** Real-time container tracking updates, document status changes

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure SignalR Service                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Hub: TrackingHub                        │ │
│  │                                                            │ │
│  │  Groups:                                                   │ │
│  │  - org_{org_id}           (organization-scoped updates)    │ │
│  │  - shipment_{shipment_id} (shipment-specific events)       │ │
│  │  - user_{user_id}         (personal notifications)         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                 Event Types                                │ │
│  │  - ContainerEvent (tracking milestones)                    │ │
│  │  - DocumentStatusChange (validation results)               │ │
│  │  - ShipmentStatusChange (workflow transitions)             │ │
│  │  - Notification (user alerts)                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Integration with FastAPI

```python
# backend/app/services/realtime.py
from azure.messaging.webpubsubservice import WebPubSubServiceClient
from azure.core.credentials import AzureKeyCredential

class AzureRealtimeService:
    def __init__(self, connection_string: str):
        self.client = WebPubSubServiceClient.from_connection_string(
            connection_string, hub="tracehub"
        )

    async def broadcast_container_event(
        self,
        org_id: str,
        shipment_id: str,
        event: ContainerEvent
    ):
        """Push tracking event to all org members watching this shipment."""
        await self.client.send_to_group(
            group=f"org_{org_id}",
            message={
                "type": "ContainerEvent",
                "shipment_id": str(shipment_id),
                "data": event.model_dump()
            },
            content_type="application/json"
        )

    async def notify_document_validated(
        self,
        org_id: str,
        document: Document
    ):
        """Notify when document validation completes."""
        await self.client.send_to_group(
            group=f"org_{org_id}",
            message={
                "type": "DocumentStatusChange",
                "document_id": str(document.id),
                "status": document.status,
                "validation_notes": document.validation_notes
            },
            content_type="application/json"
        )
```

### Frontend Integration (Next.js)

```typescript
// hooks/useRealtime.ts
import { useEffect } from 'react';
import { WebPubSubClient } from '@azure/web-pubsub-client';

export function useRealtimeTracking(shipmentId: string, onEvent: (event: ContainerEvent) => void) {
  useEffect(() => {
    const client = new WebPubSubClient({
      getClientAccessUrl: async () => {
        const response = await fetch('/api/realtime/token');
        const { url } = await response.json();
        return url;
      }
    });

    client.on('server-message', (e) => {
      if (e.message.type === 'ContainerEvent' && e.message.shipment_id === shipmentId) {
        onEvent(e.message.data);
      }
    });

    client.start();
    client.joinGroup(`shipment_${shipmentId}`);

    return () => {
      client.leaveGroup(`shipment_${shipmentId}`);
      client.stop();
    };
  }, [shipmentId, onEvent]);
}
```

### Pricing

| Tier | Units | Messages/day | Monthly Cost |
|------|-------|--------------|--------------|
| Free | 1 | 20,000 | $0 |
| Standard | 1 | 1M | ~$49 |
| Standard | 5 | 5M | ~$245 |

**Recommendation:** Start with Free tier, upgrade to Standard when exceeding 20K messages/day.

---

## 5. File Storage (Docker Volumes → Azure Blob Storage)

### Azure Blob Storage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Azure Storage Account                          │
│                   (tracehubstorage)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Container: documents                                        ││
│  │ Access: Private (SAS tokens for downloads)                  ││
│  │                                                             ││
│  │ Structure:                                                  ││
│  │ /{org_id}/                                                  ││
│  │   ├── shipments/                                            ││
│  │   │   └── {shipment_id}/                                    ││
│  │   │       ├── bill_of_lading/                               ││
│  │   │       │   └── {document_id}.pdf                         ││
│  │   │       ├── commercial_invoice/                           ││
│  │   │       └── ...                                           ││
│  │   └── audit_packs/                                          ││
│  │       └── {shipment_reference}_audit_pack.zip               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Container: processed                                        ││
│  │ Access: Private                                             ││
│  │                                                             ││
│  │ Structure:                                                  ││
│  │ /{document_id}/                                             ││
│  │   ├── original.pdf                                          ││
│  │   ├── text_extracted.txt                                    ││
│  │   ├── ocr_output.txt                                        ││
│  │   └── classification.json                                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Lifecycle Management                                        ││
│  │ - Move to Cool tier after 30 days                           ││
│  │ - Move to Archive tier after 1 year                         ││
│  │ - Delete after 7 years (compliance retention)               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### FastAPI Integration

```python
# backend/app/services/azure_storage.py
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

class AzureBlobStorageService:
    def __init__(self, connection_string: str):
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.documents_container = "documents"

    async def upload_document(
        self,
        org_id: str,
        shipment_id: str,
        document_type: str,
        document_id: str,
        file_content: bytes,
        content_type: str = "application/pdf"
    ) -> str:
        """Upload document and return blob path."""
        blob_path = f"{org_id}/shipments/{shipment_id}/{document_type}/{document_id}.pdf"

        container_client = self.client.get_container_client(self.documents_container)
        blob_client = container_client.get_blob_client(blob_path)

        await blob_client.upload_blob(
            file_content,
            content_type=content_type,
            overwrite=True,
            metadata={
                "organization_id": org_id,
                "shipment_id": shipment_id,
                "document_type": document_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )

        return blob_path

    def generate_download_url(
        self,
        blob_path: str,
        expiry_hours: int = 1
    ) -> str:
        """Generate time-limited SAS URL for secure download."""
        sas_token = generate_blob_sas(
            account_name=self.client.account_name,
            container_name=self.documents_container,
            blob_name=blob_path,
            account_key=self.client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )

        return f"{self.client.url}/{self.documents_container}/{blob_path}?{sas_token}"
```

### CDN Integration (Azure Front Door)

```
User Request
     │
     ▼
┌─────────────────────────────┐
│   Azure Front Door          │
│   (Global CDN + WAF)        │
│                             │
│   - Cache static assets     │
│   - SSL termination         │
│   - DDoS protection         │
│   - Geographic routing      │
└─────────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│   Azure Blob Storage        │
│   (Origin)                  │
└─────────────────────────────┘
```

### Pricing

| Storage Tier | $/GB/month | Access Cost |
|--------------|------------|-------------|
| Hot | $0.0208 | $0.004/10K reads |
| Cool | $0.01 | $0.01/10K reads |
| Archive | $0.002 | $0.02/10K reads + rehydration |

**Recommendation:**
- Use Hot tier for active documents
- Lifecycle policy to Cool after 30 days
- Archive after 1 year (compliance retention)

---

## 6. Serverless Functions (Supabase Edge → Azure Functions)

### Azure Functions for Document Processing

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure Functions App                           │
│                    (tracehub-functions)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Function: ProcessDocument (Blob Trigger)                  │ │
│  │                                                            │ │
│  │  Trigger: New blob in documents container                  │ │
│  │  Actions:                                                  │ │
│  │  1. Extract text (PyMuPDF)                                 │ │
│  │  2. OCR if needed (Azure Form Recognizer)                  │ │
│  │  3. Classify document type (Azure OpenAI)                  │ │
│  │  4. Update database record                                 │ │
│  │  5. Push realtime notification                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Function: FetchContainerTracking (Timer Trigger)          │ │
│  │                                                            │ │
│  │  Schedule: Every 15 minutes                                │ │
│  │  Actions:                                                  │ │
│  │  1. Query shipments with active tracking                   │ │
│  │  2. Call JSONCargo API for each container                  │ │
│  │  3. Insert new container_events                            │ │
│  │  4. Push realtime updates via SignalR                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Function: GenerateAuditPack (HTTP Trigger)                │ │
│  │                                                            │ │
│  │  Trigger: POST /api/audit-pack/{shipment_id}               │ │
│  │  Actions:                                                  │ │
│  │  1. Fetch shipment + documents                             │ │
│  │  2. Generate compliance report PDF                         │ │
│  │  3. Create ZIP with all documents                          │ │
│  │  4. Upload to Blob Storage                                 │ │
│  │  5. Return download URL                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Function: ValidateEUDR (HTTP Trigger)                     │ │
│  │                                                            │ │
│  │  Trigger: POST /api/eudr/validate                          │ │
│  │  Actions:                                                  │ │
│  │  1. Check HS code (skip for horn/hoof)                     │ │
│  │  2. Validate geolocation coordinates                       │ │
│  │  3. Verify production date                                 │ │
│  │  4. Calculate risk score                                   │ │
│  │  5. Return compliance status                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Azure Form Recognizer Integration

**Replace Tesseract OCR with Azure Document Intelligence:**

```python
# functions/process_document/main.py
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

async def extract_document_data(blob_content: bytes) -> dict:
    """Extract text and structured data using Azure Form Recognizer."""
    client = DocumentAnalysisClient(
        endpoint=os.environ["FORM_RECOGNIZER_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["FORM_RECOGNIZER_KEY"])
    )

    # Use prebuilt invoice model for commercial invoices
    poller = await client.begin_analyze_document(
        "prebuilt-invoice",
        blob_content
    )
    result = await poller.result()

    return {
        "vendor_name": result.documents[0].fields.get("VendorName"),
        "invoice_total": result.documents[0].fields.get("InvoiceTotal"),
        "items": [
            {
                "description": item.value.get("Description"),
                "quantity": item.value.get("Quantity"),
                "amount": item.value.get("Amount")
            }
            for item in result.documents[0].fields.get("Items", [])
        ]
    }
```

### Pricing

| Plan | Executions | GB-seconds | Monthly Cost |
|------|------------|------------|--------------|
| Consumption | 1M free | 400K free | ~$0 (small scale) |
| Premium EP1 | Unlimited | Dedicated | ~$173 |

**Recommendation:** Start with Consumption plan, upgrade to Premium if cold starts become an issue.

---

## 7. Observability (Sentry → Azure Application Insights)

### Azure Monitor + Application Insights Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure Monitor                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Application Insights (tracehub-insights)                  │ │
│  │                                                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │ │
│  │  │ Next.js SDK  │  │ FastAPI SDK  │  │ Azure Functions  │ │ │
│  │  │ (Browser +   │  │ (OpenCensus  │  │ (Auto-instrumented)│ │
│  │  │  Server)     │  │  Azure)      │  │                  │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ │ │
│  │                                                            │ │
│  │  Collected Data:                                           │ │
│  │  - Request traces (with user context)                      │ │
│  │  - Exceptions (full stack traces)                          │ │
│  │  - Dependencies (database, blob, SignalR)                  │ │
│  │  - Custom events (document uploads, tracking syncs)        │ │
│  │  - Performance metrics (page load, API latency)            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Log Analytics Workspace                                   │ │
│  │                                                            │ │
│  │  Queries:                                                  │ │
│  │  - Failed document uploads by organization                 │ │
│  │  - Tracking API latency percentiles                        │ │
│  │  - User activity patterns                                  │ │
│  │  - Compliance check failure rates                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Alerts                                                    │ │
│  │                                                            │ │
│  │  - API error rate > 5% (5 min window)                      │ │
│  │  - Database connection failures                            │ │
│  │  - Document processing queue depth > 100                   │ │
│  │  - Tracking API unreachable                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### FastAPI Integration

```python
# backend/app/middleware/telemetry.py
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

# Configure Application Insights
exporter = AzureExporter(connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"])
tracer = Tracer(exporter=exporter, sampler=ProbabilitySampler(1.0))

# Configure logging to Application Insights
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]))

# Custom telemetry for business events
def track_document_upload(org_id: str, document_type: str, file_size: int):
    tracer.current_span().add_annotation(
        "DocumentUpload",
        organization_id=org_id,
        document_type=document_type,
        file_size_bytes=file_size
    )

def track_compliance_check(shipment_id: str, result: str, issues_count: int):
    tracer.current_span().add_annotation(
        "ComplianceCheck",
        shipment_id=shipment_id,
        result=result,
        issues_count=issues_count
    )
```

### Next.js Integration

```typescript
// instrumentation.ts (Next.js 13+)
import { ApplicationInsights } from '@microsoft/applicationinsights-web';

export const appInsights = new ApplicationInsights({
  config: {
    connectionString: process.env.NEXT_PUBLIC_APPLICATIONINSIGHTS_CONNECTION_STRING,
    enableAutoRouteTracking: true,
    enableCorsCorrelation: true,
    enableRequestHeaderTracking: true,
    enableResponseHeaderTracking: true,
  }
});

appInsights.loadAppInsights();

// Track custom events
export function trackDocumentDownload(shipmentId: string, documentType: string) {
  appInsights.trackEvent({
    name: 'DocumentDownload',
    properties: {
      shipmentId,
      documentType,
      timestamp: new Date().toISOString()
    }
  });
}
```

### Dashboard: TraceHub Operations

```kusto
// Application Insights KQL queries

// 1. Document processing success rate by type
requests
| where name startswith "POST /api/documents"
| summarize
    total = count(),
    success = countif(success == true),
    success_rate = round(100.0 * countif(success == true) / count(), 2)
    by bin(timestamp, 1h), tostring(customDimensions.document_type)
| order by timestamp desc

// 2. Tracking sync latency
dependencies
| where name == "JSONCargo API"
| summarize
    p50 = percentile(duration, 50),
    p95 = percentile(duration, 95),
    p99 = percentile(duration, 99)
    by bin(timestamp, 15m)

// 3. Compliance check failures by organization
customEvents
| where name == "ComplianceCheck"
| where customDimensions.result == "FAILED"
| summarize failure_count = count() by tostring(customDimensions.organization_id)
| order by failure_count desc
```

### Pricing

| Feature | Cost |
|---------|------|
| Data Ingestion | $2.76/GB |
| Data Retention | Free (90 days), $0.12/GB/month (extended) |
| Alerts | ~$0.10/alert rule/month |

**Recommendation:** Set daily cap at 5GB initially (~$14/day max).

---

## 8. CI/CD & Infrastructure

### GitHub Actions + Azure DevOps Hybrid

```yaml
# .github/workflows/deploy.yml
name: Deploy TraceHub

on:
  push:
    branches: [main, develop]

env:
  AZURE_RESOURCE_GROUP: tracehub-rg
  CONTAINER_REGISTRY: tracehubacr.azurecr.io

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run backend tests
        run: |
          cd tracehub/backend
          pip install -r requirements.txt
          pytest --cov=app

      - name: Run frontend tests
        run: |
          cd tracehub/frontend
          npm ci
          npm run test

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Login to ACR
        run: az acr login --name tracehubacr

      - name: Build and push backend
        run: |
          docker build -t ${{ env.CONTAINER_REGISTRY }}/tracehub-backend:${{ github.sha }} ./tracehub/backend
          docker push ${{ env.CONTAINER_REGISTRY }}/tracehub-backend:${{ github.sha }}

      - name: Build and push frontend
        run: |
          docker build -t ${{ env.CONTAINER_REGISTRY }}/tracehub-frontend:${{ github.sha }} ./tracehub/frontend
          docker push ${{ env.CONTAINER_REGISTRY }}/tracehub-frontend:${{ github.sha }}

  deploy-staging:
    needs: build-and-push
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to Azure Container Apps (Staging)
        uses: azure/container-apps-deploy-action@v1
        with:
          resourceGroup: ${{ env.AZURE_RESOURCE_GROUP }}
          containerAppName: tracehub-staging
          imageToDeploy: ${{ env.CONTAINER_REGISTRY }}/tracehub-backend:${{ github.sha }}

  deploy-production:
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Azure Container Apps (Production)
        uses: azure/container-apps-deploy-action@v1
        with:
          resourceGroup: ${{ env.AZURE_RESOURCE_GROUP }}
          containerAppName: tracehub-production
          imageToDeploy: ${{ env.CONTAINER_REGISTRY }}/tracehub-backend:${{ github.sha }}

      - name: Run database migrations
        run: |
          az containerapp exec \
            --name tracehub-production \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --command "alembic upgrade head"
```

### Azure Key Vault Integration

```python
# backend/app/config.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_settings():
    if os.environ.get("AZURE_KEY_VAULT_URL"):
        credential = DefaultAzureCredential()
        client = SecretClient(
            vault_url=os.environ["AZURE_KEY_VAULT_URL"],
            credential=credential
        )
        return Settings(
            database_url=client.get_secret("DATABASE-URL").value,
            jwt_secret=client.get_secret("JWT-SECRET").value,
            jsoncargo_api_key=client.get_secret("JSONCARGO-API-KEY").value,
            anthropic_api_key=client.get_secret("ANTHROPIC-API-KEY").value,
        )
    else:
        return Settings()  # Use environment variables
```

---

## 9. Complete Azure Architecture Diagram

```
                                    ┌─────────────────────────────┐
                                    │      Users (Browsers)       │
                                    └─────────────┬───────────────┘
                                                  │
                                    ┌─────────────▼───────────────┐
                                    │     Azure Front Door        │
                                    │   (CDN + WAF + SSL + DDOS)  │
                                    └─────────────┬───────────────┘
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     │                            │                            │
           ┌─────────▼─────────┐       ┌─────────▼─────────┐        ┌─────────▼─────────┐
           │   Azure Static    │       │   Clerk (SaaS)    │        │   Azure SignalR   │
           │   Web Apps or     │       │   Authentication  │        │   Service         │
           │   Container Apps  │       │   + Orgs          │        │   (Realtime)      │
           │   (Next.js)       │       └───────────────────┘        └───────────────────┘
           └─────────┬─────────┘
                     │
           ┌─────────▼─────────────────────────────────────────────────────────┐
           │                   Azure Container Apps Environment                 │
           │ ┌─────────────────────────┐    ┌─────────────────────────────────┐│
           │ │   Next.js Container     │    │   FastAPI Backend Container     ││
           │ │   (Frontend + BFF)      │───▶│   (Business Logic)              ││
           │ │   Scale: 0-10           │    │   Scale: 1-5                    ││
           │ └─────────────────────────┘    └──────────────┬──────────────────┘│
           └───────────────────────────────────────────────┼───────────────────┘
                                                           │
              ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
              │                                            │                                            │
    ┌─────────▼─────────┐                       ┌─────────▼─────────┐                       ┌─────────▼─────────┐
    │  Azure Database   │                       │   Azure Blob      │                       │  Azure Functions  │
    │  for PostgreSQL   │                       │   Storage         │                       │  (Processing)     │
    │  (Flexible)       │                       │   (Documents)     │                       │                   │
    │                   │                       │                   │                       │  - ProcessDocument│
    │  - RLS policies   │                       │  - Lifecycle      │                       │  - FetchTracking  │
    │  - Auto backups   │                       │  - CDN enabled    │                       │  - GenerateAudit  │
    │  - Read replicas  │                       │  - SAS tokens     │                       │  - ValidateEUDR   │
    └───────────────────┘                       └───────────────────┘                       └───────────────────┘
              │                                            │                                            │
              └────────────────────────────────────────────┼────────────────────────────────────────────┘
                                                           │
                                            ┌──────────────▼──────────────┐
                                            │   Azure Application         │
                                            │   Insights + Log Analytics  │
                                            │   (Observability)           │
                                            └─────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │                                     Supporting Services                                              │
    │                                                                                                      │
    │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
    │  │ Azure Key      │  │ Azure          │  │ Azure Form     │  │ Azure OpenAI   │  │ Azure          │ │
    │  │ Vault          │  │ Container      │  │ Recognizer     │  │ Service        │  │ Communication  │ │
    │  │ (Secrets)      │  │ Registry       │  │ (OCR/Extract)  │  │ (AI Classify)  │  │ Services       │ │
    │  └────────────────┘  └────────────────┘  └────────────────┘  └────────────────┘  │ (Email/SMS)    │ │
    │                                                                                   └────────────────┘ │
    └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Cost Estimation

### Monthly Cost Breakdown (Production)

| Service | Configuration | Est. Monthly Cost |
|---------|---------------|-------------------|
| **Azure Container Apps** | 2 containers, ~50% utilization | $50-100 |
| **Azure Database for PostgreSQL** | D2s_v3 (2 vCores, 8GB RAM) | $100 |
| **Azure Blob Storage** | 100GB Hot, 500GB Cool | $15 |
| **Azure Front Door** | Standard tier, 100GB/month | $35 |
| **Azure SignalR** | Standard, 1 unit | $49 |
| **Azure Functions** | Consumption, moderate usage | $10-20 |
| **Azure Application Insights** | 5GB/day ingestion | $14/day → ~$420 |
| **Azure Key Vault** | Standard, 10K operations | $5 |
| **Clerk** | Pro plan (10K MAU) | $25 |

**Total Estimated: $700-850/month** (production workload)

### Cost Optimization Tips

1. **Reserved Instances:** 1-year reservation saves 20-30% on PostgreSQL
2. **Spot Instances:** Use for non-critical Azure Functions
3. **Auto-scaling:** Scale to zero during off-hours (Container Apps)
4. **Log Sampling:** Reduce Application Insights ingestion to 10% sampling
5. **Blob Lifecycle:** Aggressive tiering to Cool/Archive

---

## 11. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Set up Azure infrastructure without changing existing code

```
Tasks:
□ Create Azure resource group and subscription
□ Deploy Azure Database for PostgreSQL Flexible Server
□ Configure Azure Blob Storage account
□ Set up Azure Container Registry
□ Deploy Azure Key Vault with secrets
□ Configure Azure Application Insights
□ Set up GitHub Actions CI/CD pipeline
□ Migrate database from Hostinger to Azure PostgreSQL
```

### Phase 2: Storage & Processing (Weeks 3-4)

**Goal:** Migrate file storage and add serverless processing

```
Tasks:
□ Update FastAPI to use Azure Blob Storage SDK
□ Migrate existing documents to Azure Blob
□ Deploy Azure Functions for document processing
□ Integrate Azure Form Recognizer (replace Tesseract)
□ Set up Azure OpenAI for document classification
□ Configure blob lifecycle policies
```

### Phase 3: Authentication (Weeks 5-6)

**Goal:** Replace custom JWT with Clerk

```
Tasks:
□ Set up Clerk project and configure organizations
□ Add Clerk Next.js SDK to frontend
□ Create Clerk webhook for user/org sync
□ Add clerk_id column to users table
□ Update FastAPI auth middleware for Clerk JWT
□ Migrate existing users to Clerk
□ Remove legacy JWT code
```

### Phase 4: Frontend Migration (Weeks 7-10)

**Goal:** Migrate React SPA to Next.js

```
Tasks:
□ Create Next.js 14 project with App Router
□ Set up Tailwind CSS (match existing design tokens)
□ Migrate page components to Next.js pages
□ Implement server components for data fetching
□ Add Clerk auth components
□ Implement API routes as BFF layer
□ Test and validate all user flows
□ Deploy to Azure Static Web Apps / Container Apps
```

### Phase 5: Realtime & Polish (Weeks 11-12)

**Goal:** Add realtime features and production hardening

```
Tasks:
□ Deploy Azure SignalR Service
□ Implement realtime tracking updates
□ Add realtime document status notifications
□ Configure alerts in Application Insights
□ Set up Azure Front Door with WAF
□ Performance testing and optimization
□ Documentation and team training
```

---

## 12. Migration Checklist

### Pre-Migration

- [ ] Audit current database schema and data volume
- [ ] Document all environment variables and secrets
- [ ] Backup existing PostgreSQL database
- [ ] Export existing documents from Docker volumes
- [ ] Create Azure subscription and resource group
- [ ] Set up Azure AD for team access

### Database Migration

- [ ] Create Azure PostgreSQL Flexible Server
- [ ] Enable required extensions (uuid-ossp, pgcrypto)
- [ ] Use Azure Database Migration Service
- [ ] Validate data integrity post-migration
- [ ] Update connection strings in Key Vault
- [ ] Test application connectivity

### Application Migration

- [ ] Build Docker images and push to ACR
- [ ] Deploy to Azure Container Apps (staging)
- [ ] Configure environment variables from Key Vault
- [ ] Run Alembic migrations on Azure PostgreSQL
- [ ] Test all API endpoints
- [ ] Deploy to production

### Authentication Migration

- [ ] Create Clerk project
- [ ] Configure organizations and roles
- [ ] Implement webhook endpoint
- [ ] Migrate users (batch script)
- [ ] Test login/logout/refresh flows
- [ ] Verify organization isolation

### Storage Migration

- [ ] Create Azure Storage account
- [ ] Configure containers and access policies
- [ ] Migrate existing documents (azcopy)
- [ ] Update file_path references in database
- [ ] Test upload/download flows
- [ ] Configure lifecycle management

### Observability Migration

- [ ] Create Application Insights resource
- [ ] Add SDK to frontend and backend
- [ ] Configure custom events and metrics
- [ ] Set up alert rules
- [ ] Create operational dashboards
- [ ] Test end-to-end tracing

### Post-Migration

- [ ] Decommission Hostinger VPS
- [ ] Update DNS records
- [ ] Monitor for 2 weeks
- [ ] Performance baseline
- [ ] Cost monitoring setup
- [ ] Team training on Azure portal

---

## Appendix A: Key Azure Resources

| Resource | Azure Service | Pricing Tier |
|----------|--------------|--------------|
| Compute | Azure Container Apps | Consumption |
| Database | Azure Database for PostgreSQL | General Purpose D2s_v3 |
| Storage | Azure Blob Storage | Hot + Cool tiers |
| CDN/WAF | Azure Front Door | Standard |
| Auth | Clerk (external) | Pro |
| Realtime | Azure SignalR Service | Standard |
| Serverless | Azure Functions | Consumption |
| AI/ML | Azure Form Recognizer | S0 |
| AI/ML | Azure OpenAI Service | Pay-as-you-go |
| Secrets | Azure Key Vault | Standard |
| Monitoring | Azure Application Insights | Pay-as-you-go |
| CI/CD | GitHub Actions | Free tier |
| Registry | Azure Container Registry | Basic |

---

## Appendix B: Environment Variables

```bash
# Azure Core
AZURE_SUBSCRIPTION_ID=
AZURE_RESOURCE_GROUP=tracehub-rg
AZURE_KEY_VAULT_URL=https://tracehub-kv.vault.azure.net/

# Database
DATABASE_URL=postgresql://tracehub@tracehub-db.postgres.database.azure.com/tracehub?sslmode=require

# Storage
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER_DOCUMENTS=documents
AZURE_STORAGE_CONTAINER_PROCESSED=processed

# SignalR
AZURE_SIGNALR_CONNECTION_STRING=

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=

# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
CLERK_WEBHOOK_SECRET=

# Azure AI
FORM_RECOGNIZER_ENDPOINT=
FORM_RECOGNIZER_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=

# External APIs
JSONCARGO_API_KEY=

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## Appendix C: Decision Matrix - Clerk vs Azure AD B2C

| Criteria | Clerk | Azure AD B2C | Winner |
|----------|-------|--------------|--------|
| Setup Time | Hours | Days-Weeks | Clerk |
| Multi-tenant Orgs | Built-in | Custom required | Clerk |
| Next.js Integration | Excellent | Good | Clerk |
| Enterprise SSO | Via providers | Native | Azure AD B2C |
| Pricing (10K MAU) | $25/month | ~$32/month | Clerk |
| Azure Integration | Good | Native | Azure AD B2C |
| Developer Experience | Excellent | Complex | Clerk |
| Compliance (SOC2) | Yes | Yes | Tie |

**Recommendation:** Use **Clerk** initially. Add Azure AD B2C as an identity provider later if enterprise customers require it.

---

*Document maintained by TraceHub Engineering Team*
