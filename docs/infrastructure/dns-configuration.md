# DNS Configuration Guide - VIBOTAJ.com

## Overview

This document provides step-by-step instructions for configuring DNS records for vibotaj.com on Hostinger hPanel to resolve the www subdomain 403 error and ensure proper domain routing.

---

## Current Issue

- **Problem:** `www.vibotaj.com` returns a 403 Forbidden error
- **Root Cause:** Missing or misconfigured CNAME record for the www subdomain
- **Solution:** Add proper DNS records and configure redirects

---

## DNS Records Required

### Primary Records

| Type | Name | Value | TTL | Purpose |
|------|------|-------|-----|---------|
| A | @ | Hostinger Server IP* | 14400 | Points root domain to server |
| CNAME | www | vibotaj.com | 14400 | Points www to root domain |
| A | @ | (IPv4 from Hostinger) | 14400 | Backup A record |
| AAAA | @ | (IPv6 from Hostinger) | 14400 | IPv6 support (optional) |

*Get the exact IP from Hostinger hPanel → Hosting → Manage → Server IP

---

## Step-by-Step Configuration in Hostinger hPanel

### Step 1: Access DNS Zone Editor

1. Log in to [Hostinger hPanel](https://hpanel.hostinger.com)
2. Navigate to **Domains** → **vibotaj.com**
3. Click **DNS / Nameservers** in the left sidebar
4. Select **DNS Records** tab

### Step 2: Verify A Record for Root Domain

1. Look for existing A record with Name: `@`
2. If missing, click **Add Record**
3. Configure:
   - **Type:** A
   - **Name:** @ (or leave blank for root)
   - **Points to:** Your Hostinger server IP (found in Hosting → Manage → Details)
   - **TTL:** 14400 (4 hours)
4. Click **Add Record**

### Step 3: Add CNAME Record for WWW Subdomain

1. Click **Add Record** button
2. Configure the following:
   - **Type:** CNAME
   - **Name:** www
   - **Target:** vibotaj.com (without trailing period)
   - **TTL:** 14400
3. Click **Add Record** to save

### Step 4: Remove Conflicting Records (If Any)

Check for and delete any conflicting records:
- Duplicate A records for www
- Old CNAME records pointing elsewhere
- Any TXT records that might interfere

### Step 5: Verify Nameservers

Ensure nameservers are set to Hostinger's:
```
ns1.dns-parking.com
ns2.dns-parking.com
```
Or if using Hostinger hosting nameservers:
```
ns1.hostinger.com
ns2.hostinger.com
```

---

## DNS Propagation

### Expected Propagation Time
- **Hostinger internal:** 5-15 minutes
- **Global propagation:** 24-48 hours (typically faster)

### Verification Commands

Run these commands to verify DNS propagation:

```bash
# Check A record for root domain
dig vibotaj.com A +short

# Check CNAME record for www
dig www.vibotaj.com CNAME +short

# Check what www resolves to
dig www.vibotaj.com A +short

# Full DNS lookup
nslookup vibotaj.com
nslookup www.vibotaj.com

# Check from multiple DNS servers
dig @8.8.8.8 www.vibotaj.com A +short      # Google DNS
dig @1.1.1.1 www.vibotaj.com A +short      # Cloudflare DNS
dig @208.67.222.222 www.vibotaj.com A +short # OpenDNS
```

### Online Verification Tools
- [DNS Checker](https://dnschecker.org/#CNAME/www.vibotaj.com)
- [What's My DNS](https://www.whatsmydns.net/#CNAME/www.vibotaj.com)
- [MX Toolbox](https://mxtoolbox.com/DNSLookup.aspx)

---

## Hostinger API Configuration (Optional)

If using Hostinger API for DNS management:

```bash
# Load API token
source .secrets/hostinger.env

# List current DNS records
curl -X GET "https://api.hostinger.com/v1/dns/vibotaj.com/records" \
  -H "Authorization: Bearer $HOSTINGER_API_TOKEN" \
  -H "Content-Type: application/json"

# Add CNAME record via API
curl -X POST "https://api.hostinger.com/v1/dns/vibotaj.com/records" \
  -H "Authorization: Bearer $HOSTINGER_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "CNAME",
    "name": "www",
    "content": "vibotaj.com",
    "ttl": 14400
  }'
```

---

## Troubleshooting

### WWW Still Shows 403 After DNS Update

1. **Clear DNS cache locally:**
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   
   # Clear browser cache or use incognito mode
   ```

2. **Check .htaccess for blocking rules:**
   - Access Hostinger File Manager
   - Navigate to `public_html/.htaccess`
   - Look for `Deny from all` or restrictive rules

3. **Verify addon domain/subdomain configuration:**
   - hPanel → Hosting → Manage → Subdomains
   - Ensure www is not configured as a separate subdomain with its own directory

### DNS Records Not Updating

1. Wait for TTL expiration (check current TTL values)
2. Verify you're editing the correct domain in hPanel
3. Check if domain is using external nameservers (Cloudflare, etc.)

### Mixed Content After Configuration

After DNS is working, ensure SSL covers both:
- `https://vibotaj.com`
- `https://www.vibotaj.com`

See `ssl-configuration.md` for SSL setup details.

---

## Post-Configuration Checklist

- [ ] A record exists for root domain (@)
- [ ] CNAME record added for www subdomain
- [ ] No conflicting DNS records
- [ ] DNS propagation verified (dig/nslookup)
- [ ] `www.vibotaj.com` resolves correctly
- [ ] No 403 error on www subdomain
- [ ] SSL certificate covers both www and non-www
- [ ] Redirects configured in .htaccess

---

## Related Documentation

- [SSL Configuration](./ssl-configuration.md)
- [.htaccess Template](../../src/config/.htaccess.template)
- [Backup Strategy](./backup-strategy.md)

---

*Last Updated: December 2024*
*Author: DevOps Engineer - VIBOTAJ Revamp Project*
