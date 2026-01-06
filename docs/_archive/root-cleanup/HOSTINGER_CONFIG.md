# Hostinger API Configuration for VIBOTAJ Website Revamp

## Hostinger API Token

**API Token:** `<REDACTED - See .secrets/hostinger.env>`

⚠️ **IMPORTANT:** Keep this token secure and never commit it to public repositories!
💡 **Real token stored in:** `.secrets/hostinger.env` (git-ignored)

---

## Connect Claude Code with Hostinger MCP

Copy this JSON configuration and add it to your Claude Code configuration:

```json
{
  "inputs": [
    {
      "id": "api_token",
      "type": "promptString",
      "description": "Enter your Hostinger API token (required)"
    }
  ],
  "servers": {
    "hostinger-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "hostinger-api-mcp@latest"
      ],
      "env": {
        "API_TOKEN": "${HOSTINGER_API_TOKEN}"
      }
    }
  }
}
```

---

## Test Hostinger API Connection

Run this command to verify your API token works:

```bash
curl -X GET "https://developers.hostinger.com/api/vps/v1/virtual-machines" \
  -H "Authorization: Bearer $HOSTINGER_API_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Available Hostinger API Endpoints

### 1. Virtual Machines (VPS)
```bash
# List all VPS instances
GET https://developers.hostinger.com/api/vps/v1/virtual-machines
```

### 2. Website Management
```bash
# List websites
GET https://developers.hostinger.com/api/hosting/v1/websites

# Get website details
GET https://developers.hostinger.com/api/hosting/v1/websites/{website_id}
```

### 3. DNS Management
```bash
# List DNS zones
GET https://developers.hostinger.com/api/dns/v1/zones

# Update DNS records (for fixing www subdomain)
POST https://developers.hostinger.com/api/dns/v1/zones/{zone_id}/records
```

### 4. SSL Certificates
```bash
# List SSL certificates
GET https://developers.hostinger.com/api/ssl/v1/certificates

# Install SSL certificate
POST https://developers.hostinger.com/api/ssl/v1/certificates
```

---

## Hostinger Account Details

**Website:** vibotaj.com  
**Hosting Provider:** Hostinger  
**Server Type:** Shared Hosting / VPS (to be confirmed)  
**Control Panel:** hPanel  
**Access:** https://hpanel.hostinger.com

---

## DNS Configuration for www Subdomain Fix

Using Hostinger API to add www subdomain CNAME record:

```bash
# Get zone ID for vibotaj.com
curl -X GET "https://developers.hostinger.com/api/dns/v1/zones" \
  -H "Authorization: Bearer $HOSTINGER_API_TOKEN" \
  -H "Content-Type: application/json"

# Add CNAME record for www subdomain
curl -X POST "https://developers.hostinger.com/api/dns/v1/zones/{zone_id}/records" \
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

## Automated Deployment via Hostinger API

### Deploy Code to Hostinger

```bash
# Example: Deploy via FTP (to be automated in GitHub Actions)
curl -X POST "https://developers.hostinger.com/api/deployment/v1/deploy" \
  -H "Authorization: Bearer $HOSTINGER_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "{website_id}",
    "branch": "main",
    "deploy_path": "/public_html"
  }'
```

---

## Security Best Practices

1. **Never commit API tokens to Git**
   - Use `.env` files (already in `.gitignore`)
   - Use GitHub Secrets for CI/CD

2. **Store API token securely**
   - Add to GitHub Secrets: `HOSTINGER_API_TOKEN`
   - Add to local `.env` file

3. **Rotate API tokens regularly**
   - Generate new token every 90 days
   - Update in all environments

4. **Monitor API usage**
   - Check Hostinger API dashboard
   - Set up alerts for unusual activity

---

## Adding to GitHub Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `HOSTINGER_API_TOKEN`
5. Value: `<Your Hostinger API Token from .secrets/hostinger.env>`
6. Click "Add secret"

---

## Environment Variables Setup

Add to your `.env` file (local development):

```bash
# Hostinger API
HOSTINGER_API_TOKEN=<Your token from .secrets/hostinger.env>
HOSTINGER_API_URL=https://developers.hostinger.com/api

# FTP Credentials (for deployment)
FTP_HOST=your-server.hostinger.com
FTP_USERNAME=your-ftp-username
FTP_PASSWORD=your-ftp-password
FTP_PORT=21

# Website Details
WEBSITE_URL=https://vibotaj.com
WEBSITE_ID=your-website-id
```

---

## Troubleshooting

### API Token Not Working
```bash
# Test token validity
curl -X GET "https://developers.hostinger.com/api/vps/v1/virtual-machines" \
  -H "Authorization: Bearer $HOSTINGER_API_TOKEN" \
  -v
```

### Common Error Codes
- `401 Unauthorized` - Invalid API token
- `403 Forbidden` - Token doesn't have required permissions
- `404 Not Found` - Resource doesn't exist
- `429 Too Many Requests` - Rate limit exceeded

---

## Useful Resources

- **Hostinger API Documentation:** https://developers.hostinger.com/docs
- **hPanel Access:** https://hpanel.hostinger.com
- **Hostinger Support:** https://support.hostinger.com

---

**Configuration Created:** December 27, 2025  
**Last Updated:** December 27, 2025  
**Maintained By:** Infrastructure Agent
