# Backup Strategy - VIBOTAJ.com

## Overview

This document outlines the comprehensive backup strategy for vibotaj.com using UpdraftPlus plugin with Google Drive integration. The strategy ensures data protection for the WordPress site and WooCommerce store.

---

## Backup Schedule

| Backup Type | Frequency | Retention | Storage Location |
|-------------|-----------|-----------|------------------|
| Database | Daily at 3:00 AM (server time) | 14 backups | Google Drive |
| Files (themes, plugins, uploads) | Weekly (Sunday 4:00 AM) | 4 backups | Google Drive |
| Full Site | Monthly (1st of month) | 3 backups | Google Drive + Local |

---

## UpdraftPlus Installation & Configuration

### Step 1: Install UpdraftPlus

1. Log in to WordPress admin: `https://vibotaj.com/wp-admin`
2. Navigate to **Plugins** → **Add New**
3. Search for "UpdraftPlus"
4. Click **Install Now** on "UpdraftPlus WordPress Backup Plugin"
5. Click **Activate**

### Step 2: Access UpdraftPlus Settings

1. Go to **Settings** → **UpdraftPlus Backups**
2. Click on the **Settings** tab

### Step 3: Configure Backup Schedule

#### Files Backup Schedule:
- **Schedule:** Weekly
- **Day:** Sunday
- **Time:** 04:00 (automatically set based on server time)
- **Retain:** 4 backups

#### Database Backup Schedule:
- **Schedule:** Daily
- **Time:** 03:00 (automatically set based on server time)
- **Retain:** 14 backups

### Step 4: Select What to Backup

Enable the following for inclusion in file backups:
- [x] **Plugins** - All installed plugins
- [x] **Themes** - All themes including child themes
- [x] **Uploads** - Media library and WooCommerce files
- [x] **Any other directories found inside wp-content** - Custom folders

#### Exclusion Rules (Recommended)

Add these to the exclusion field to reduce backup size:
```
backup*
cache
w3tc*
wfcache
updraft
*.log
*.zip
*.gz
*.tmp
```

---

## Google Drive Integration

### Step 1: Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Library**
4. Search for "Google Drive API" and enable it
5. Go to **APIs & Services** → **OAuth consent screen**
   - Choose **External** user type
   - Fill in app name: "UpdraftPlus Backup - VIBOTAJ"
   - Add your email as test user

### Step 2: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: "UpdraftPlus VIBOTAJ"
5. Add Authorized redirect URI:
   ```
   https://vibotaj.com/wp-admin/options-general.php?page=updraftplus
   ```
6. Click **Create**
7. Copy the **Client ID** and **Client Secret**

### Step 3: Configure UpdraftPlus with Google Drive

1. In UpdraftPlus Settings, scroll to **Choose your remote storage**
2. Click the **Google Drive** icon
3. Enter the following:
   - **Client ID:** (paste from Google Cloud Console)
   - **Client Secret:** (paste from Google Cloud Console)
4. Click **Save Changes**
5. Click the **Sign in with Google** link that appears
6. Authorize UpdraftPlus to access Google Drive
7. You'll be redirected back to WordPress - confirm the connection

### Step 4: Configure Google Drive Folder

1. After authentication, specify folder settings:
   - **Folder name:** `vibotaj-backups` (UpdraftPlus will create this)
   - Leave other settings as default
2. Click **Save Changes**

### Step 5: Verify Connection

1. Click **Test Google Drive Settings** button
2. Confirm you see: "The test was successful"
3. Check Google Drive for the new `vibotaj-backups` folder

---

## Alternative: Using UpdraftPlus Easy Setup

If the manual Google setup is complex, UpdraftPlus offers simplified authentication:

1. In remote storage, select **Google Drive**
2. Choose **"Sign in with Google"** (simplified method)
3. Follow the prompts to authenticate
4. UpdraftPlus will handle the OAuth flow automatically

*Note: This creates a folder in your Google Drive root named "UpdraftPlus"*

---

## Manual Backup Procedures

### Creating an Immediate Backup

1. Go to **Settings** → **UpdraftPlus Backups**
2. Click the **Backup Now** button
3. Select options:
   - [x] Include your database in the backup
   - [x] Include your files in the backup
   - [x] Send this backup to remote storage (Google Drive)
4. Click **Backup Now**
5. Monitor progress in the activity log

### Downloading Backups Locally

1. In UpdraftPlus, go to **Existing Backups** tab
2. Find the backup date you need
3. Click on individual components:
   - **Database** - Downloads .sql.gz file
   - **Plugins** - Downloads plugins archive
   - **Themes** - Downloads themes archive
   - **Uploads** - Downloads media files archive
   - **Others** - Downloads other wp-content files
4. Store downloaded files securely (external drive, separate cloud storage)

---

## Restoration Procedures

### Scenario 1: Full Site Restoration

1. Navigate to **Settings** → **UpdraftPlus Backups**
2. Go to **Existing Backups** tab
3. Find the backup you want to restore
4. Click **Restore** button next to the backup
5. Select components to restore:
   - [x] Plugins
   - [x] Themes
   - [x] Uploads
   - [x] Others
   - [x] Database
6. Click **Next**
7. Confirm the restoration
8. Wait for completion (do not navigate away)
9. Follow any post-restoration prompts

### Scenario 2: Database Only Restoration

Use this when you need to revert content/settings but keep files:

1. In **Existing Backups**, find your backup
2. Click **Restore**
3. Select only:
   - [x] Database
4. Proceed with restoration
5. You may need to re-save permalinks after:
   - Go to **Settings** → **Permalinks**
   - Click **Save Changes** (no changes needed)

### Scenario 3: Restore Specific Files

1. Click on the specific backup component (Plugins/Themes/Uploads)
2. Download the archive
3. Extract locally
4. Upload specific files via SFTP or File Manager

### Scenario 4: Restore from Google Drive (Fresh Install)

If WordPress is reinstalled or you're migrating:

1. Install WordPress fresh
2. Install and activate UpdraftPlus
3. Configure Google Drive connection (same credentials)
4. Go to **Existing Backups** tab
5. Click **Rescan remote storage**
6. Previous backups will appear
7. Restore from the cloud backup

---

## WooCommerce-Specific Considerations

### Critical Data to Backup

- **Database:** Contains all orders, customers, products, settings
- **Uploads:** Product images, downloadable files
- **Plugins:** WooCommerce and extensions configuration

### Pre-Backup Checklist for WooCommerce

Before major changes, create a manual backup:
- [ ] Before plugin updates
- [ ] Before theme changes
- [ ] Before WooCommerce version upgrades
- [ ] Before changing payment gateways
- [ ] Before bulk product imports

### WooCommerce Order Data

Orders are stored in the database. Ensure:
1. Daily database backups are running
2. Retention is sufficient for your refund policy period
3. Consider additional backup before major sales events

---

## Monitoring & Verification

### Weekly Backup Verification Checklist

- [ ] Log in to UpdraftPlus dashboard
- [ ] Verify last backup completed successfully
- [ ] Check Google Drive for new backup files
- [ ] Verify backup file sizes are reasonable
- [ ] Review any error messages in the log

### Monthly Backup Test

Perform a test restoration monthly (on staging if available):

1. Download a recent backup
2. Set up a local/staging environment
3. Restore the backup
4. Verify:
   - [ ] Site loads correctly
   - [ ] Products display properly
   - [ ] Checkout process works
   - [ ] Admin functions work
   - [ ] All plugins are active

### Backup Size Monitoring

Track backup sizes to ensure Google Drive capacity:

| Component | Expected Size Range |
|-----------|-------------------|
| Database | 50MB - 500MB |
| Plugins | 100MB - 300MB |
| Themes | 20MB - 100MB |
| Uploads | 500MB - 5GB+ |

*Adjust expectations based on your store size*

---

## Troubleshooting

### Backup Fails to Complete

1. **Increase PHP memory limit:**
   - Edit wp-config.php: `define('WP_MEMORY_LIMIT', '512M');`
   
2. **Increase execution time:**
   - Add to .htaccess: `php_value max_execution_time 600`
   
3. **Split backup:** In UpdraftPlus settings, reduce the archive split size:
   - Settings → Expert Settings → Split archives every X MB

### Google Drive Authentication Expires

1. Go to UpdraftPlus Settings
2. Click **Re-authenticate with Google Drive**
3. Complete the OAuth flow again

### Backup Files Missing from Google Drive

1. Check Google Drive trash
2. Verify correct Google account is connected
3. Check UpdraftPlus folder permissions
4. Re-authenticate if necessary

### Restoration Fails

1. **Database restoration:** 
   - Check MySQL user permissions
   - Verify database connection in wp-config.php
   
2. **File restoration:**
   - Check file permissions (755 for directories, 644 for files)
   - Verify sufficient disk space
   
3. **Memory errors:**
   - Restore components one at a time
   - Use manual SFTP restoration for large file archives

---

## Emergency Procedures

### Complete Site Failure

1. **Don't panic** - backups are available
2. Access Hostinger hPanel
3. Check if issue is hosting-related
4. If site files are corrupted:
   - Reinstall WordPress via Hostinger
   - Install UpdraftPlus
   - Connect to Google Drive
   - Restore from latest backup

### Accidental Deletion Recovery

1. Check if item is in WordPress trash
2. If not, restore from most recent backup
3. For single file recovery, download backup and extract specific file

### Ransomware/Hack Recovery

1. **Immediately:** Put site in maintenance mode
2. Download current (infected) files for analysis (optional)
3. Contact Hostinger support about the incident
4. Restore from a backup dated before the infection
5. Change all passwords (WordPress, FTP, database, hosting)
6. Update all plugins, themes, and WordPress core
7. Install security plugin (Wordfence, Sucuri)
8. Scan for remaining malware

---

## Backup Retention Policy

| Backup Type | Retention | Total Storage Estimate |
|-------------|-----------|----------------------|
| Daily DB | 14 days | ~700MB - 7GB |
| Weekly Files | 4 weeks | ~2GB - 20GB |
| Monthly Full | 3 months | ~3GB - 15GB |

**Recommended Google Drive Storage:** 15GB free tier should suffice for small stores. Consider Google One for larger stores.

---

## Contact Information

### Support Resources

- **UpdraftPlus Documentation:** https://updraftplus.com/support/
- **Hostinger Support:** hPanel → Help
- **Google Drive Support:** https://support.google.com/drive

---

## Related Documentation

- [DNS Configuration](./dns-configuration.md)
- [SSL Configuration](./ssl-configuration.md)
- [.htaccess Template](../../src/config/.htaccess.template)

---

*Last Updated: December 2024*
*Author: DevOps Engineer - VIBOTAJ Revamp Project*
