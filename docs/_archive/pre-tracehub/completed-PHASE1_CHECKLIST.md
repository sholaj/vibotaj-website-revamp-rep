# Phase 1 Execution Checklist - VIBOTAJ Website Revamp

**Date Started:** December 27, 2025  
**Status:** 🟡 In Progress

---

## Infrastructure Overview

| Service | Role | Access |
|---------|------|--------|
| **Squarespace** | DNS Management | domains.squarespace.com |
| **Hostinger** | Web Hosting, SSL, WordPress | hpanel.hostinger.com |

```
Traffic Flow: User → Squarespace DNS → Hostinger (178.16.128.48) → WordPress
```

---

## Current DNS Status

| Domain | Record Type | Value | Status |
|--------|-------------|-------|--------|
| vibotaj.com | A | 178.16.128.48 | ✅ Working |
| www.vibotaj.com | CNAME | (missing) | ❌ Not configured |

---

## Task 1.1: Fix www Subdomain ✅ COMPLETE

**Status:** 🟢 Complete

### What was done:

1. **Squarespace DNS** - Added CNAME record:
   - Type: CNAME
   - Host: www
   - Target: vibotaj.com
   - TTL: 4 hrs

2. **Hostinger Subdomain** - Created www subdomain:
   - Subdomain: www.vibotaj.com
   - Points to: /public_html (same as main domain)

### Verification:
```bash
dig www.vibotaj.com CNAME +short
# Output: vibotaj.com.
```

---

## Task 1.2: Configure 301 Redirects ✅ COMPLETE

**Status:** 🟢 Complete (Auto-configured by Hostinger)

Hostinger automatically handles redirects:
- `www.vibotaj.com` → `vibotaj.com` (301)
- `http://` → `https://` (301)

### Verification:
```bash
curl -sI https://www.vibotaj.com | grep -i location
# Output: location: https://vibotaj.com/
```

### Files Prepared (if manual config needed):
- `src/config/.htaccess.template` - Full configuration
- `scripts/deploy-phase1.sh` - Deployment script

---

## Task 1.3: SSL Certificate Verification ⚠️ ACTION NEEDED

**Status:** 🟡 Certificate needs update to include www

**Where to fix:** Hostinger hPanel (not Squarespace)

### Current Certificate Status:
```
Subject: CN=vibotaj.com
Valid: Dec 13, 2025 - Mar 13, 2026
SANs: vibotaj.com (MISSING: www.vibotaj.com)
```

### Steps to Fix (in Hostinger hPanel):

1. **Go to SSL settings:**
   - hPanel → Security → SSL
   - Select vibotaj.com
   - Click **Reinstall** or **Manage**

2. **Ensure www is included:**
   - Check "Include www subdomain" option
   - Or add www.vibotaj.com as additional domain

3. **Wait for certificate issuance** (5-10 minutes)

4. **Verify Certificate:**
   ```bash
   echo | openssl s_client -connect www.vibotaj.com:443 -servername www.vibotaj.com 2>/dev/null | openssl x509 -noout -text | grep -A1 "Subject Alternative Name"
   # Expected: DNS:vibotaj.com, DNS:www.vibotaj.com
   ```

---

## Task 1.4: Backup System Setup ⏳ PENDING

**Status:** ⬜ Not started

**Where to configure:** Hostinger (WordPress Admin)

### WordPress Admin Steps:

1. **Access WordPress Admin:**
   - URL: https://vibotaj.com/wp-admin
   - Search: "UpdraftPlus"
   - Install & Activate

2. **Configure Backup Schedule**
   - Settings → UpdraftPlus Backups → Settings tab
   - Files backup schedule: Weekly
   - Database backup schedule: Daily
   - Retention: 4 weeks

3. **Configure Remote Storage**
   - Choose: Google Drive
   - Click "Authenticate with Google"
   - Complete OAuth flow
   - Verify connection

4. **Run Test Backup**
   - Click "Backup Now"
   - Include: Database + Files
   - Verify backup appears in Google Drive

---

## Task 1.5: Google Analytics Setup ⏳ PENDING

**Status:** ⬜ Not started

### Steps:

1. **Create GA4 Property**
   - Go to: https://analytics.google.com
   - Admin → Create Property
   - Property name: VIBOTAJ Global
   - Select: Nigeria, NGN

2. **Get Measurement ID**
   - Data Streams → Web
   - URL: https://vibotaj.com
   - Copy Measurement ID (G-XXXXXXXXXX)

3. **Configure WordPress**
   - Plugins → MonsterInsights → Settings
   - Connect Google Analytics
   - Select your GA4 property

4. **Verify Tracking**
   - Visit vibotaj.com
   - Check GA4 Realtime report

---

## Verification Commands

Run these commands to verify Phase 1 completion:

```bash
# DNS Check
dig www.vibotaj.com CNAME +short

# HTTP Response Check
curl -sI http://vibotaj.com | head -3
curl -sI https://vibotaj.com | head -3
curl -sI https://www.vibotaj.com | head -3

# SSL Certificate Check
echo | openssl s_client -connect vibotaj.com:443 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName

# Security Headers Check
curl -sI https://vibotaj.com | grep -iE "strict-transport|x-frame|x-content-type"
```

---

## Progress Summary

| Task | Description | Status | Where |
|------|-------------|--------|-------|
| 1.1 | Fix www DNS | ✅ Complete | Squarespace + Hostinger |
| 1.2 | 301 Redirects | ✅ Complete | Hostinger (auto) |
| 1.3 | SSL Certificate | 🟡 Pending | Hostinger hPanel |
| 1.4 | Backup System | ⬜ Not started | Hostinger (WP Admin) |
| 1.5 | Google Analytics | ⬜ Not started | Hostinger (WP Admin) |

---

**Next Action:** Task 1.3 - Reissue SSL certificate in Hostinger hPanel to include www
