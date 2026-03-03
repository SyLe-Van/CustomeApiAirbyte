#!/bin/bash
# deploy-fly.sh - Script tự động deploy lên Fly.io
# Sử dụng: chmod +x deploy-fly.sh && ./deploy-fly.sh

set -e  # Dừng nếu có lỗi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   NetSuite Proxy API - Fly.io Deploy  ${NC}"
echo -e "${BLUE}======================================${NC}"

# Load .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Found .env file${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}❌ .env file not found! Please create it first.${NC}"
    exit 1
fi

# Check if flyctl is installed
if ! command -v fly &> /dev/null; then
    echo -e "${YELLOW}⚠️  flyctl not found. Installing...${NC}"
    brew install flyctl
fi

echo -e "${GREEN}✅ flyctl found: $(fly version)${NC}"

# Check login status
if ! fly auth whoami &> /dev/null; then
    echo -e "${YELLOW}🔑 Not logged in. Opening browser for login...${NC}"
    fly auth login
fi

echo -e "${GREEN}✅ Logged in as: $(fly auth whoami)${NC}"

# Check if app exists
APP_NAME="netsuite-proxy-api"
if fly apps list | grep -q "$APP_NAME"; then
    echo -e "${GREEN}✅ App '$APP_NAME' already exists. Updating...${NC}"
else
    echo -e "${BLUE}🚀 Creating new app '$APP_NAME' in Singapore region...${NC}"
    fly apps create "$APP_NAME" --machines
fi

# Set secrets (environment variables)
echo -e "${BLUE}🔐 Setting secrets...${NC}"

fly secrets set \
    API_KEY="${API_KEY}" \
    ALLOWED_ORIGINS="${ALLOWED_ORIGINS}" \
    RATE_LIMIT_MAX="${RATE_LIMIT_MAX}" \
    NETSUITE_REALM="${NETSUITE_REALM}" \
    NETSUITE_CONSUMER_KEY="${NETSUITE_CONSUMER_KEY}" \
    NETSUITE_CONSUMER_SECRET="${NETSUITE_CONSUMER_SECRET}" \
    NETSUITE_TOKEN_KEY="${NETSUITE_TOKEN_KEY}" \
    NETSUITE_TOKEN_SECRET="${NETSUITE_TOKEN_SECRET}" \
    --app "$APP_NAME"

echo -e "${GREEN}✅ Secrets set successfully${NC}"

# Deploy
echo -e "${BLUE}🚀 Deploying to Fly.io...${NC}"
fly deploy --app "$APP_NAME" --remote-only

# Get app URL
APP_URL=$(fly status --app "$APP_NAME" | grep "Hostname" | awk '{print $2}')
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}   ✅ Deploy thành công!               ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}🌐 App URL: https://${APP_NAME}.fly.dev${NC}"
echo -e "${GREEN}❤️  Health: https://${APP_NAME}.fly.dev/health${NC}"
echo -e "${GREEN}📖 Docs:   https://${APP_NAME}.fly.dev/docs${NC}"
echo ""
echo -e "${YELLOW}💡 Các lệnh hữu ích:${NC}"
echo -e "   fly logs --app $APP_NAME          # Xem logs"
echo -e "   fly status --app $APP_NAME        # Xem trạng thái"
echo -e "   fly ssh console --app $APP_NAME   # SSH vào máy"
