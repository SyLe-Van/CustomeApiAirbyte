#!/bin/bash

# Quick test - wait and check immediately
BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"
ENDPOINT="/api/reports/salesorder-detail"

echo "⏳ Waiting 30s for deployment..."
sleep 30

echo ""
echo "🧪 Testing Sales Order Report..."
echo "=================================="
echo ""

curl -s "${BASE_URL}${ENDPOINT}?api_key=${API_KEY}&user_id=8&limit=3" | jq '.'
