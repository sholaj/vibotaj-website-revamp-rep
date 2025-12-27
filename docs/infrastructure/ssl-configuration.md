# SSL Configuration Guide - VIBOTAJ.com

## Overview

This document provides comprehensive SSL/TLS configuration instructions for vibotaj.com hosted on Hostinger. Proper SSL ensures secure connections and is essential for WooCommerce payment processing.

---

## Current Requirements

- **Primary Domain:** vibotaj.com (HTTPS required)
- **WWW Subdomain:** www.vibotaj.com (must redirect to primary with HTTPS)
- **WooCommerce:** Requires valid SSL for payment gateways
- **SEO:** Google prefers HTTPS sites

---

## SSL Certificate Options on Hostinger

### Option 1: Free Let's Encrypt SSL (Recommended)

Hostinger provides free Let's Encrypt certificates that auto-renew.

**Coverage:**
- vibotaj.com
- www.vibotaj.com

**Validity:** 90 days (auto-renews)

### Option 2: Premium SSL (Comodo/Sectigo)

Available through Hostinger for ~$9.99/year:
- Extended validation available
- Warranty included
- Priority support

---

## Installing Free SSL Certificate

### Step 1: Access SSL Settings

1. Log in to [Hostinger hPanel](https://hpanel.hostinger.com)
2. Navigate to **Hosting** → **Manage** (for vibotaj.com)
3. Find **Security** section in left sidebar
4. Click **SSL**

### Step 2: Install Let's Encrypt Certificate

1. In SSL section, locate your domain
2. Click **Setup** or **Install** next to vibotaj.com
3. Select **Free SSL (Let's Encrypt)**
4. Ensure both domains are selected:
   - [x] vibotaj.com
   - [x] www.vibotaj.com
5. Click **Install SSL**
6. Wait for installation (typically 1-5 minutes)

### Step 3: Verify Installation

1. Status should change to **Active**
2. Check expiration date (90 days from installation)
3. Note: Auto-renewal is enabled by default

---

## Force HTTPS Configuration

### Method 1: Hostinger hPanel (Recommended)

1. In hPanel, go to **Hosting** → **Manage**
2. Navigate to **Security** → **SSL**
3. Find **Force HTTPS** toggle
4. Enable it for vibotaj.com
5. Changes apply immediately

### Method 2: WordPress Settings

1. Log in to WordPress admin
2. Go to **Settings** → **General**
3. Update both URLs to HTTPS:
   - **WordPress Address (URL):** `https://vibotaj.com`
   - **Site Address (URL):** `https://vibotaj.com`
4. Click **Save Changes**
5. You'll be logged out - log back in via HTTPS

### Method 3: wp-config.php Configuration

Add these lines to `wp-config.php` above "That's all, stop editing!":

```php
/* Force SSL */
define('FORCE_SSL_ADMIN', true);

/* If behind a reverse proxy */
if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https') {
    $_SERVER['HTTPS'] = 'on';
}

/* Ensure proper URL scheme */
define('WP_HOME', 'https://vibotaj.com');
define('WP_SITEURL', 'https://vibotaj.com');
```

### Method 4: .htaccess Redirect

Already included in `.htaccess.template`, but here's the specific rule:

```apache
# Force HTTPS
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

---

## Certificate Verification

### Online Tools

1. **SSL Labs Test:** https://www.ssllabs.com/ssltest/analyze.html?d=vibotaj.com
   - Aim for Grade A or A+
   
2. **SSL Checker:** https://www.sslshopper.com/ssl-checker.html#hostname=vibotaj.com

3. **Why No Padlock:** https://www.whynopadlock.com/

### Command Line Verification

```bash
# Check certificate details
openssl s_client -connect vibotaj.com:443 -servername vibotaj.com 2>/dev/null | openssl x509 -noout -dates

# Check certificate chain
openssl s_client -connect vibotaj.com:443 -servername vibotaj.com -showcerts

# Verify www subdomain
openssl s_client -connect www.vibotaj.com:443 -servername www.vibotaj.com 2>/dev/null | openssl x509 -noout -dates

# Check certificate issuer
echo | openssl s_client -connect vibotaj.com:443 -servername vibotaj.com 2>/dev/null | openssl x509 -noout -issuer

# Test TLS versions
openssl s_client -connect vibotaj.com:443 -tls1_2
openssl s_client -connect vibotaj.com:443 -tls1_3
```

### Browser Verification

1. Visit https://vibotaj.com
2. Click the padlock icon in the address bar
3. Click **Certificate** or **Connection is secure**
4. Verify:
   - Issued to: vibotaj.com
   - Issued by: Let's Encrypt (or your CA)
   - Valid dates
   - Certificate chain is complete

---

## Mixed Content Issues

Mixed content occurs when HTTPS pages load HTTP resources.

### Identifying Mixed Content

1. **Browser Console:** Press F12 → Console tab
   - Look for "Mixed Content" warnings
   
2. **Why No Padlock:** Scans page for HTTP resources

3. **WordPress Plugin:** Install "Really Simple SSL" temporarily to identify issues

### Fixing Mixed Content

#### Database URL Update

Run these SQL queries via phpMyAdmin or WP-CLI:

```sql
-- Update WordPress URLs
UPDATE wp_options SET option_value = replace(option_value, 'http://vibotaj.com', 'https://vibotaj.com') WHERE option_name = 'home' OR option_name = 'siteurl';

-- Update post content
UPDATE wp_posts SET post_content = replace(post_content, 'http://vibotaj.com', 'https://vibotaj.com');

-- Update post excerpts
UPDATE wp_posts SET post_excerpt = replace(post_excerpt, 'http://vibotaj.com', 'https://vibotaj.com');

-- Update post GUIDs
UPDATE wp_posts SET guid = replace(guid, 'http://vibotaj.com', 'https://vibotaj.com');

-- Update postmeta
UPDATE wp_postmeta SET meta_value = replace(meta_value, 'http://vibotaj.com', 'https://vibotaj.com');

-- Update comments
UPDATE wp_comments SET comment_content = replace(comment_content, 'http://vibotaj.com', 'https://vibotaj.com');

-- Update usermeta
UPDATE wp_usermeta SET meta_value = replace(meta_value, 'http://vibotaj.com', 'https://vibotaj.com');
```

#### Using WP-CLI (Preferred)

```bash
# SSH into server, then:
cd public_html
wp search-replace 'http://vibotaj.com' 'https://vibotaj.com' --all-tables --precise
```

#### Using Better Search Replace Plugin

1. Install "Better Search Replace" plugin
2. Go to **Tools** → **Better Search Replace**
3. Search for: `http://vibotaj.com`
4. Replace with: `https://vibotaj.com`
5. Select all tables
6. Run as dry run first
7. Then run actual replacement

---

## WooCommerce SSL Requirements

### Payment Gateway Requirements

All payment gateways require SSL:
- PayPal
- Stripe
- Credit card processors
- Bank transfers (for customer trust)

### WooCommerce SSL Settings

1. Go to **WooCommerce** → **Settings** → **Advanced**
2. Ensure **Force secure checkout** is enabled
3. Under **Page Setup**, verify checkout page exists

### Testing Checkout SSL

1. Add product to cart
2. Proceed to checkout
3. Verify:
   - URL shows `https://`
   - Padlock icon is visible
   - No mixed content warnings
   - Payment form loads correctly

---

## Security Headers Configuration

The `.htaccess.template` includes these headers. Verify they're active:

### HSTS (HTTP Strict Transport Security)

```apache
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
```

**Note:** Only enable HSTS after confirming SSL works perfectly. HSTS tells browsers to always use HTTPS, and errors can lock users out.

### HSTS Preload (Optional)

After SSL is stable for several months:

1. Visit https://hstspreload.org/
2. Enter vibotaj.com
3. Follow submission requirements
4. Submit for inclusion in browser preload lists

---

## SSL Certificate Renewal

### Automatic Renewal (Let's Encrypt)

Hostinger automatically renews Let's Encrypt certificates:
- Renewal attempts start 30 days before expiry
- Multiple retry attempts if failed
- Email notifications for issues

### Manual Renewal (If Needed)

1. hPanel → Security → SSL
2. Click **Renew** if available
3. Or reinstall the certificate

### Monitoring Expiration

Set up monitoring:

```bash
# Check expiration date
echo | openssl s_client -servername vibotaj.com -connect vibotaj.com:443 2>/dev/null | openssl x509 -noout -enddate

# Expected output: notAfter=Mar 28 00:00:00 2025 GMT
```

**Free monitoring services:**
- https://www.sslshopper.com/ssl-certificate-reminder.html
- UptimeRobot (also monitors uptime)

---

## Troubleshooting

### ERR_SSL_PROTOCOL_ERROR

1. Check if SSL is installed in hPanel
2. Clear browser cache
3. Try incognito/private window
4. Verify DNS is pointing to Hostinger

### ERR_CERT_COMMON_NAME_INVALID

1. Certificate doesn't cover the domain you're accessing
2. Reinstall SSL with correct domains
3. Ensure www subdomain is included

### NET::ERR_CERT_AUTHORITY_INVALID

1. Certificate chain is incomplete
2. Self-signed certificate (reinstall Let's Encrypt)
3. Contact Hostinger support

### Redirect Loops

1. Disable HTTPS forcing temporarily
2. Check .htaccess for conflicting rules
3. Check wp-config.php for duplicate HTTPS settings
4. Disable plugins that modify redirects

### Mixed Content After Migration

1. Run database search-replace for URLs
2. Check theme settings for hardcoded URLs
3. Review plugin settings for HTTP URLs
4. Check custom CSS for HTTP resources

---

## SSL Configuration Checklist

### Initial Setup
- [ ] Free SSL installed in Hostinger hPanel
- [ ] Both vibotaj.com and www.vibotaj.com covered
- [ ] Certificate status shows "Active"

### WordPress Configuration
- [ ] WordPress Address URL set to https://
- [ ] Site Address URL set to https://
- [ ] FORCE_SSL_ADMIN defined in wp-config.php

### Redirect Configuration
- [ ] HTTP to HTTPS redirect working
- [ ] www to non-www redirect working
- [ ] .htaccess rules in place

### Verification
- [ ] SSL Labs grade A or higher
- [ ] No mixed content warnings
- [ ] Padlock visible on all pages
- [ ] Checkout page secure

### WooCommerce
- [ ] Checkout loads via HTTPS
- [ ] Payment forms display correctly
- [ ] Order confirmation pages secure
- [ ] Customer account pages secure

### Security Headers
- [ ] HSTS header active
- [ ] X-Frame-Options set
- [ ] X-Content-Type-Options set
- [ ] Security headers test passes

---

## Related Documentation

- [DNS Configuration](./dns-configuration.md)
- [.htaccess Template](../../src/config/.htaccess.template)
- [Backup Strategy](./backup-strategy.md)

---

*Last Updated: December 2024*
*Author: DevOps Engineer - VIBOTAJ Revamp Project*
