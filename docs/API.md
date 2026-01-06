# TraceHub API Documentation

> API endpoints and integration guide

## Status

**PLACEHOLDER** - To be completed with full API specification

## Base URLs

- **Development:** http://localhost:8000
- **Staging:** https://staging.tracehub.vibotaj.com
- **Production:** https://api.tracehub.vibotaj.com

## Authentication

All API requests require authentication using JWT tokens.

```bash
# Get access token
curl -X POST https://api.tracehub.vibotaj.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in requests
curl -X GET https://api.tracehub.vibotaj.com/shipments \
  -H "Authorization: Bearer <token>"
```

## Core Endpoints

### Shipments

- `GET /shipments` - List all shipments
- `GET /shipments/{id}` - Get shipment details
- `POST /shipments` - Create new shipment
- `PUT /shipments/{id}` - Update shipment
- `DELETE /shipments/{id}` - Delete shipment

### Documents

- `GET /shipments/{id}/documents` - List shipment documents
- `POST /shipments/{id}/documents` - Upload document
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete document

### Compliance

- `GET /shipments/{id}/compliance` - Check compliance status
- `GET /shipments/{id}/audit-pack` - Download audit pack

### Tracking

- `GET /shipments/{id}/tracking` - Get container tracking events
- `POST /webhooks/tracking` - Receive tracking updates (webhook)

## Interactive Documentation

Full interactive API documentation available at:
- **Development:** http://localhost:8000/docs
- **Production:** https://api.tracehub.vibotaj.com/docs

---

**TODO:**
- [ ] Add complete endpoint specifications
- [ ] Add request/response examples
- [ ] Add error code documentation
- [ ] Add rate limiting information
- [ ] Add webhook documentation
