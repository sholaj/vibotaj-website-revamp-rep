# Phase 1 Execution Checklist - VIBOTAJ Website Revamp

**Date Started:** December 27, 2025  
**Status:** 🟡 In Progress

---

## Current DNS Status

| Domain | Record Type | Value | Status |
|--------|-------------|-------|--------|
| vibotaj.com | A | 178.16.128.48 | ✅ Working |
| www.vibotaj.com | CNAME | (missing) | ❌ Not configured |

---

## Task 1.1: Fix www Subdomain DNS ⚠️ MANUAL ACTION REQUIRED

**Status:** 🔴 Blocked - Requires manual hPanel access

### Steps to Complete:

1. **Login to Hostinger hPanel**
   - URL: https://hpanel.hostinger.com
   - Use your Hostinger account credentials

2. **Navigate to DNS Settings**
   - Click **Domains** in left sidebar
   - Click on **vibotaj.com**
   - Click **DNS / Nameservers**
   - Select **DNS Records** tab

3. **Add CNAME Record**
   - Click **Add Record**
   - Configure:
     ```
     Type:   CNAME
     Name:   www
     Target: vibotaj.com
     TTL:    14400
     ```
   - Click **Add Record**

4. **Verify Propagation**
   ```bash
   # Run this command to verify (wait 5-15 minutes)
   dig www.vibotaj.com CNAME +short
   # Expected output: vibotaj.com.
   ```

5. **Test Access**
   ```bash
   curl -sI https://www.vibotaj.com | head -3
   ```

---

## Task 1.2: Configure 301 Redirects ✅ READY

**Status:** 🟢 Template ready, awaiting DNS fix

### Files Prepared:
- `src/config/.htaccess.template` - Full configuration
- `scripts/deploy-phase1.sh` - Deployment script

### Manual Deployment (if script fails):

1. **Connect via FTP/File Manager**
   - hPanel → Files → File Manager
   - Navigate to: `/public_html/`

2. **Backup Current .htaccess**
   - Download existing `.htaccess` file
   - Save as `.htaccess.backup.YYYYMMDD`

3. **Upload New .htaccess**
   - Upload contents of `src/config/.htaccess.template`
   - Rename to `.htaccess`

4. **Verify Redirects**
   ```bash
   # HTTP to HTTPS
   curl -sI http://vibotaj.com | grep -i location
   # Expected: Location: https://vibotaj.com/

   # www to non-www
   curl -sI https://www.vibotaj.com | grep -i location
   # Expected: Location: https://vibotaj.com/
   ```

---

## Task 1.3: SSL Certificate Verification ⚠️ ACTION NEEDED

**Status:** 🟡 Certificate needs update to include www

### Current Certificate Status:
```
Subject: CN=vibotaj.com
Valid: Dec 13, 2025 - Mar 13, 2026
SANs: vibotaj.com (MISSING: www.vibotaj.com)
```

### Steps to Fix:

1. **After DNS is configured**, reissue SSL certificate in hPanel:
   - hPanel → SSL → vibotaj.com
   - Click **Reinstall** or **Setup**
   - Ensure "Include www" is checked
   - Wait for certificate to be issued

2. **Verify Certificate**
   ```bash
   echo | openssl s_client -connect www.vibotaj.com:443 -servername www.vibotaj.com 2>/dev/null | openssl x509 -noout -text | grep -A1 "Subject Alternative Name"
   ```

3. **Test SSL Labs Rating**
   - URL: https://www.ssllabs.com/ssltest/analyze.html?d=vibotaj.com
   - Target: A or A+ rating

---

## Task 1.4: Backup System Setup ⏳ PENDING

**Status:** ⬜ Not started

### WordPress Admin Steps:

1. **Install UpdraftPlus**
   - WordPress Admin → Plugins → Add New
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

| Task | Description | Status | Owner |
|------|-------------|--------|-------|
| 1.1 | Fix www DNS | 🔴 Manual | DevOps |
| 1.2 | 301 Redirects | 🟢 Ready | DevOps |
| 1.3 | SSL Certificate | 🟡 Pending DNS | DevOps |
| 1.4 | Backup System | ⬜ Not started | DevOps |
| 1.5 | Google Analytics | ⬜ Not started | Content |

---

**Next Action:** Complete Task 1.1 (DNS configuration in hPanel)
