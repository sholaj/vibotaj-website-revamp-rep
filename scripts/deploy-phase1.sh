#!/bin/bash
# =============================================================================
# VIBOTAJ.COM Phase 1 Deployment Script
# =============================================================================
# This script helps deploy configuration files to Hostinger via SFTP
# 
# Prerequisites:
# 1. DNS CNAME record for www must be configured first
# 2. FTP credentials must be set in .secrets/ftp.env
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root (scripts is one level down from project root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "========================================"
echo "VIBOTAJ Phase 1 Deployment"
echo "========================================"

# Load FTP credentials
if [ -f "$PROJECT_ROOT/.secrets/ftp.env" ]; then
    source "$PROJECT_ROOT/.secrets/ftp.env"
else
    echo -e "${RED}Error: FTP credentials not found at .secrets/ftp.env${NC}"
    echo ""
    echo "Create the file with:"
    echo "  FTP_HOST=your-server.hostinger.com"
    echo "  FTP_USER=your-ftp-username"
    echo "  FTP_PASS=your-ftp-password"
    echo "  FTP_PATH=/home/u162482009/domains/vibotaj.com/public_html"
    exit 1
fi

# Verify DNS before proceeding
echo ""
echo "Step 1: Verifying DNS configuration..."
WWW_CNAME=$(dig www.vibotaj.com CNAME +short 2>/dev/null)

if [ -z "$WWW_CNAME" ]; then
    echo -e "${YELLOW}Warning: www.vibotaj.com CNAME record not found${NC}"
    echo ""
    echo "Please configure DNS first:"
    echo "  1. Go to https://hpanel.hostinger.com"
    echo "  2. Add CNAME record: www → vibotaj.com"
    echo ""
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ www.vibotaj.com CNAME: $WWW_CNAME${NC}"
fi

# Check main domain resolves
MAIN_IP=$(dig vibotaj.com A +short 2>/dev/null)
echo -e "${GREEN}✓ vibotaj.com A record: $MAIN_IP${NC}"

# Step 2: Backup current .htaccess
echo ""
echo "Step 2: Creating backup of current .htaccess..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$PROJECT_ROOT/backups/.htaccess.backup.$BACKUP_DATE"

mkdir -p "$PROJECT_ROOT/backups"

# Download current .htaccess via SFTP
sftp -o StrictHostKeyChecking=no "$FTP_USER@$FTP_HOST" <<EOF
cd $FTP_PATH
get .htaccess $BACKUP_FILE
bye
EOF

if [ -f "$BACKUP_FILE" ]; then
    echo -e "${GREEN}✓ Backup saved to: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}Warning: Could not backup .htaccess (may not exist)${NC}"
fi

# Step 3: Deploy new .htaccess
echo ""
echo "Step 3: Deploying new .htaccess..."

HTACCESS_TEMPLATE="$PROJECT_ROOT/src/config/.htaccess.template"

if [ ! -f "$HTACCESS_TEMPLATE" ]; then
    echo -e "${RED}Error: .htaccess template not found at $HTACCESS_TEMPLATE${NC}"
    exit 1
fi

sftp -o StrictHostKeyChecking=no "$FTP_USER@$FTP_HOST" <<EOF
cd $FTP_PATH
put $HTACCESS_TEMPLATE .htaccess
bye
EOF

echo -e "${GREEN}✓ .htaccess deployed successfully${NC}"

# Step 4: Verify redirects
echo ""
echo "Step 4: Verifying redirects..."
sleep 2

# Test HTTPS redirect
HTTP_RESPONSE=$(curl -sI http://vibotaj.com 2>&1 | head -1)
echo "http://vibotaj.com → $HTTP_RESPONSE"

# Test www redirect (if DNS is ready)
if [ -n "$WWW_CNAME" ]; then
    WWW_RESPONSE=$(curl -sI https://www.vibotaj.com 2>&1 | head -1)
    echo "https://www.vibotaj.com → $WWW_RESPONSE"
fi

echo ""
echo "========================================"
echo -e "${GREEN}Deployment Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Test all URL variations in browser"
echo "  2. Check SSL certificate includes www subdomain"
echo "  3. Run SSL Labs test: https://www.ssllabs.com/ssltest/"
echo ""
