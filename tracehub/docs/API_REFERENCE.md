# TraceHub API Reference

> Base URL: `/api` | Authentication: JWT Bearer Token

## Overview

TraceHub exposes a RESTful API with 75+ endpoints across 10 routers. All endpoints (except auth) require JWT authentication.

**Multi-Tenancy:** All data queries are filtered by `organization_id` from the authenticated user's context.

---

## Authentication

### POST /auth/login
Authenticate user and receive JWT token.

**Request:**
```json
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Token Expiry:** 24 hours

---

### GET /auth/me
Get current user (legacy format).

**Response:**
```json
{
  "username": "user@example.com",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin"
}
```

---

### GET /auth/me/full
Get current user with full permissions and organization context.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "is_active": true,
  "organization_id": "uuid",
  "permissions": ["shipments:create", "documents:validate", ...],
  "org_role": "admin",
  "org_type": "vibotaj",
  "org_permissions": ["org:members:manage", ...]
}
```

---

### GET /auth/permissions
Get current user's permission list.

**Response:**
```json
{
  "permissions": ["shipments:view", "shipments:create", ...]
}
```

---

## Shipments

### POST /shipments
Create a new shipment.

**Required Permissions:** `shipments:create`

**Request:**
```json
{
  "reference": "VIBO-2026-001",
  "container_number": "MSCU1234567",
  "product_type": "horn_hoof",
  "vessel_name": "MSC AURORA",
  "buyer_organization_id": "uuid (optional)"
}
```

**Note:** `organization_id` is auto-injected from authenticated user.

**Response:** `201 Created` with Shipment object

---

### GET /shipments
List shipments for current organization.

**Query Parameters:**
- `status` (optional): Filter by status
- `limit` (default: 50, max: 100)
- `offset` (default: 0)

**Response:**
```json
[
  {
    "id": "uuid",
    "reference": "VIBO-2026-001",
    "container_number": "MSCU1234567",
    "status": "in_transit",
    "product_type": "horn_hoof",
    "eta": "2026-01-15T00:00:00Z",
    ...
  }
]
```

---

### GET /shipments/{shipment_id}
Get shipment details with documents and tracking.

**Response:**
```json
{
  "shipment": { ... },
  "organization": { "id": "uuid", "name": "...", "slug": "...", "type": "..." },
  "latest_event": { ... },
  "documents": [ ... ],
  "document_summary": {
    "total_required": 6,
    "total_uploaded": 4,
    "complete": 3,
    "missing": ["phytosanitary_certificate", "fumigation_certificate"],
    "pending_validation": 1,
    "is_complete": false
  }
}
```

---

### PATCH /shipments/{shipment_id}
Update a shipment.

**Required Permissions:** `shipments:update`

**Request:** Partial shipment object with fields to update.

---

### DELETE /shipments/{shipment_id}
Delete a shipment and all related records.

**Required Permissions:** `shipments:delete` (admin only)

---

### GET /shipments/{shipment_id}/documents
List documents for a shipment with compliance summary.

---

### GET /shipments/{shipment_id}/events
Get container tracking events.

---

### GET /shipments/{shipment_id}/audit-pack
Download audit pack as ZIP file.

---

## Documents

### POST /documents/upload
Upload a document with optional auto-detection.

**Required Permissions:** `documents:upload`

**Request:** `multipart/form-data`
- `shipment_id`: UUID
- `file`: File
- `document_type`: DocumentType enum
- `auto_detect`: boolean (optional, enables AI classification)
- `reference_number`: string (optional)
- `issue_date`: ISO date (optional)
- `expiry_date`: ISO date (optional)
- `issuing_authority`: string (optional)

---

### GET /documents/{document_id}
Get document metadata.

---

### GET /documents/{document_id}/download
Download document file.

---

### DELETE /documents/{document_id}
Delete a document.

**Required Permissions:** `documents:delete`

---

### DELETE /documents/shipment/{shipment_id}/all
Delete all documents for a shipment.

**Required Permissions:** `documents:delete`

---

### PATCH /documents/{document_id}/validate
Mark document as validated (legacy endpoint).

---

### GET /documents/{document_id}/validation
Get validation status and checks.

---

### GET /documents/{document_id}/transitions
Get allowed workflow state transitions.

---

### POST /documents/{document_id}/transition
Transition document to new state.

**Request:**
```json
{
  "target_status": "validated",
  "notes": "Approved after review"
}
```

---

### POST /documents/{document_id}/approve
Approve document (shortcut for transition to validated).

**Required Permissions:** `documents:approve`

---

### POST /documents/{document_id}/reject
Reject document with required notes.

**Required Permissions:** `documents:approve`

**Request:**
```json
{
  "notes": "Missing signature on page 2"
}
```

---

### PATCH /documents/{document_id}/metadata
Update document metadata.

---

### GET /documents/{document_id}/contents
Get individual documents within a combined PDF.

---

### POST /documents/{document_id}/contents/{content_id}/validate
Validate specific content within combined PDF.

---

### POST /documents/{document_id}/contents/{content_id}/reject
Reject specific content within combined PDF.

---

### POST /documents/{document_id}/confirm-detection
Confirm auto-detected document types.

---

### GET /documents/{document_id}/analyze
Re-analyze document to detect document types.

---

### GET /documents/shipments/{shipment_id}/duplicates
Find duplicate documents in shipment.

**Multi-Tenancy:** ✅ Secure - Verifies shipment belongs to user's organization

---

### GET /documents/check-duplicate
Check if reference number already exists.

**Multi-Tenancy:** ✅ Secure - Verifies shipment belongs to user's organization

---

### GET /documents/expiring
Get documents expiring within N days.

**Query Parameters:**
- `days` (default: 30)
- `shipment_id` (optional)

---

### GET /documents/types/{document_type}/requirements
Get validation requirements for document type.

---

### GET /documents/workflow/summary
Get workflow summary for shipment.

---

### GET /documents/ai/status
Check if AI classification is available.

---

### POST /documents/ai/test
Test AI classification with sample text.

---

### POST /documents/{document_id}/extract
Extract shipment data from document.

---

### GET /documents/{document_id}/preview-extraction
Preview extraction without applying.

---

## Organizations

### POST /organizations
Create organization.

**Required Permissions:** Admin only

---

### GET /organizations
List all organizations.

**Required Permissions:** Admin only

---

### GET /organizations/buyers
List buyer organizations (for dropdowns).

**Permissions:** Any authenticated user

---

### GET /organizations/{org_id}
Get organization details.

**Required Permissions:** Admin only

---

### PATCH /organizations/{org_id}
Update organization.

**Required Permissions:** Admin only

---

### GET /organizations/{org_id}/members
List organization members.

**Required Permissions:** Admin only

---

### POST /organizations/{org_id}/members
Add member to organization.

**Required Permissions:** Admin only

---

### PATCH /organizations/{org_id}/members/{user_id}
Update member role/status.

**Required Permissions:** Admin only

---

### DELETE /organizations/{org_id}/members/{user_id}
Remove member from organization.

**Required Permissions:** Admin only

---

## Users

### POST /users
Create user (inherits organization from current user).

**Required Permissions:** `users:create`

---

### GET /users
List users in current organization.

---

### GET /users/me
Get current user profile.

---

### GET /users/{user_id}
Get user details.

---

### PATCH /users/{user_id}
Update user.

**Required Permissions:** `users:update`

---

### PATCH /users/{user_id}/password
Update own password.

---

### POST /users/{user_id}/reset-password
Admin password reset.

**Required Permissions:** Admin only

---

### DELETE /users/{user_id}
Deactivate user.

**Required Permissions:** `users:delete`

---

### POST /users/{user_id}/activate
Reactivate user.

**Required Permissions:** `users:update`

---

### GET /users/roles
List available roles.

---

### GET /users/permissions-matrix
Get role-permission matrix.

**Required Permissions:** Admin only

---

## EUDR Compliance

### GET /eudr/shipment/{shipment_id}/status
Get EUDR compliance status.

---

### POST /eudr/shipment/{shipment_id}/validate
Run full EUDR validation.

---

### GET /eudr/shipment/{shipment_id}/report
Generate compliance report.

**Query Parameters:**
- `format`: "json" or "pdf"

---

### POST /eudr/origin/{origin_id}/verify
Verify origin data.

---

### GET /eudr/origin/{origin_id}/risk
Get deforestation risk assessment.

---

### POST /eudr/check/geolocation
Validate geolocation coordinates.

---

### POST /eudr/check/production-date
Check production date compliance.

---

### GET /eudr/countries/risk-levels
Get country risk classifications.

---

### GET /eudr/regulation/info
Get EUDR regulation information.

---

## Tracking

### GET /tracking/status/{container_number}
Get container status (database + live).

---

### GET /tracking/live/{container_number}
Get live tracking from JSONCargo.

---

### GET /tracking/bol/{bl_number}
Get tracking by Bill of Lading.

---

### POST /tracking/refresh/{shipment_id}
Refresh tracking data from JSONCargo.

---

### GET /tracking/usage
Get JSONCargo API usage stats.

---

## Notifications

### GET /notifications
Get current user's notifications.

**Query Parameters:**
- `unread_only` (default: false)
- `limit` (default: 50)
- `offset` (default: 0)

---

### GET /notifications/unread-count
Get unread notification count.

---

### PATCH /notifications/{notification_id}/read
Mark notification as read.

---

### POST /notifications/read-all
Mark all notifications as read.

---

### DELETE /notifications/{notification_id}
Delete notification.

---

### GET /notifications/types
Get notification type descriptions.

---

## Audit Logs

### GET /audit
Query audit logs with filtering.

**Required Permissions:** Admin only

**Query Parameters:**
- `user_id` (optional)
- `action` (optional)
- `resource_type` (optional)
- `resource_id` (optional)
- `start_date` (optional)
- `end_date` (optional)
- `limit` (default: 100)
- `offset` (default: 0)

**Multi-Tenancy:** ✅ Secure - Filtered by user's organization_id

---

### GET /audit/recent
Get recent activity feed.

**Query Parameters:**
- `limit` (default: 20)

---

### GET /audit/summary
Get audit summary statistics.

---

## Analytics

### GET /analytics/dashboard
Dashboard overview statistics.

---

### GET /analytics/shipments
Shipment metrics.

---

### GET /analytics/shipments/trends
Shipment trends over time.

**Query Parameters:**
- `days` (default: 30)
- `group_by`: "day", "week", or "month"

---

### GET /analytics/documents
Document statistics.

---

### GET /analytics/documents/distribution
Document status distribution.

---

### GET /analytics/compliance
Compliance metrics.

---

### GET /analytics/tracking
Tracking statistics.

---

## Health Check

### GET /health
System health status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.3.x"
}
```

---

## Multi-Tenancy Summary

| Router | Status | Filter Method |
|--------|--------|---------------|
| shipments | ✅ Secure | `organization_id == current_user.organization_id` |
| documents | ✅ Secure | All endpoints verify shipment belongs to user's organization |
| users | ✅ Secure | Filtered by organization |
| organizations | ✅ Secure | Admin-only access |
| eudr | ✅ Secure | Checks shipment ownership |
| tracking | ✅ Secure | Verifies shipment in organization |
| notifications | ✅ User-scoped | Filtered by user_id |
| audit | ✅ Secure | Filtered by `organization_id` |
| analytics | ✅ Secure | Passed as parameter to service |

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message" | [{"loc": ["body", "field"], "msg": "...", "type": "..."}]
}
```

**Status Codes:**
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error (Pydantic)
- `500` - Internal Server Error
