# VIBOTAJ Architecture Overview

## System Components

### 1. WordPress Backend
- **WooCommerce**: Product catalog, orders, payments
- **REST API**: Custom endpoints for React frontend
- **Admin Panel**: Content management, order processing

### 2. React Frontend (Customer Portal)
- **Order Tracking**: Real-time shipment status
- **Account Dashboard**: Order history, profile management
- **Product Catalog**: Headless WooCommerce integration

### 3. External APIs
- **Maersk Tracking API**: Container/shipment tracking
- **Payment Gateways**: Stripe, PayPal integration
- **Email Service**: Transactional emails (SMTP)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         VIBOTAJ SYSTEM                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐         ┌──────────────────────────────────────┐ │
│  │   BROWSER    │         │         HOSTINGER SERVER             │ │
│  │              │         │                                      │ │
│  │ ┌──────────┐ │  HTTPS  │  ┌────────────┐    ┌──────────────┐ │ │
│  │ │  React   │◄─────────►│  │ WordPress  │◄──►│    MySQL     │ │ │
│  │ │ Frontend │ │         │  │    PHP     │    │   Database   │ │ │
│  │ └────┬─────┘ │         │  └─────┬──────┘    └──────────────┘ │ │
│  │      │       │         │        │                             │ │
│  └──────┼───────┘         │        │ WP REST API                 │ │
│         │                 │        ▼                             │ │
│         │                 │  ┌────────────┐                      │ │
│         │                 │  │WooCommerce │                      │ │
│         │                 │  │  Plugin    │                      │ │
│         │                 │  └────────────┘                      │ │
│         │                 └──────────────────────────────────────┘ │
│         │                                                          │
│         │                 ┌──────────────────────────────────────┐ │
│         │                 │        EXTERNAL SERVICES             │ │
│         │                 │                                      │ │
│         └────────────────►│  ┌─────────┐  ┌─────────┐  ┌──────┐ │ │
│                           │  │ Maersk  │  │ Stripe  │  │ SMTP │ │ │
│                           │  │   API   │  │ PayPal  │  │Email │ │ │
│                           │  └─────────┘  └─────────┘  └──────┘ │ │
│                           └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

DATA FLOW:
──────────
1. User Request ──► React Frontend ──► WP REST API ──► MySQL
2. Order Tracking ──► React ──► Maersk API ──► Tracking Data
3. Checkout ──► WooCommerce ──► Payment Gateway ──► Confirmation
```

---

## Tech Stack

| Layer      | Technology                          | Purpose                    |
|------------|-------------------------------------|----------------------------|
| Frontend   | React 18 + TypeScript               | Customer portal SPA        |
| Styling    | Tailwind CSS                        | Utility-first styling      |
| Backend    | WordPress 6.x + PHP 8.1             | CMS & API server           |
| E-commerce | WooCommerce 8.x                     | Products, orders, payments |
| Database   | MySQL 8.0                           | Existing WordPress DB      |
| API        | WP REST API + Custom Endpoints      | Frontend data layer        |
| Tracking   | Maersk Track & Trace API            | Shipment status            |

### Custom REST Endpoints

```
GET  /wp-json/vibotaj/v1/tracking/{order_id}   → Shipment status
GET  /wp-json/vibotaj/v1/orders                → Customer orders
POST /wp-json/vibotaj/v1/quote-request         → Quote submission
GET  /wp-json/wc/v3/products                   → Product catalog
```

---

## Deployment Architecture

### Hostinger Shared Hosting Constraints

| Constraint          | Limit           | Mitigation                      |
|---------------------|-----------------|----------------------------------|
| PHP Memory          | 256MB           | Optimize queries, use caching   |
| Max Execution Time  | 300s            | Async processing for heavy ops  |
| Storage             | 100GB           | CDN for media assets            |
| No SSH Root         | Limited CLI     | Use FTP/SFTP, hPanel tools      |
| No Docker           | Shared env      | Native PHP/WordPress only       |

### Deployment Strategy

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Development   │────►│    Staging      │────►│   Production    │
│   (Local)       │     │ (Subdomain)     │     │  (vibotaj.com)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
    Git Push              FTP Sync              FTP/Auto Deploy
```

### File Structure (Production)

```
public_html/
├── wp-content/
│   ├── themes/vibotaj/          # Custom theme
│   ├── plugins/vibotaj-core/    # Custom functionality
│   └── uploads/                 # Media files
├── react-portal/                # Built React app (static)
│   ├── index.html
│   └── assets/
└── wp-config.php                # Environment config
```

---

## Security Considerations

- **Authentication**: JWT tokens for React ↔ WP API
- **CORS**: Whitelist vibotaj.com domains only
- **Rate Limiting**: Limit API requests per IP
- **SSL**: Enforced via Hostinger (Let's Encrypt)
- **Secrets**: Environment variables in wp-config.php
