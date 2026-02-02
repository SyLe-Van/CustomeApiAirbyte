#!/bin/bash

# Test current deployed API to see actual error
BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"

echo "=========================================="
echo "🧪 Testing Current Deployed API"
echo "=========================================="
echo ""

echo "1️⃣  Testing Sales Order Report Endpoint"
echo "------------------------------------------"
curl -s "${BASE_URL}/api/reports/salesorder-detail?api_key=${API_KEY}&user_id=8&limit=2" | jq '.'
echo ""

echo ""
echo "2️⃣  Testing Basic SalesOrder Endpoint (for comparison)"
echo "------------------------------------------"
curl -s "${BASE_URL}/api/netsuite/salesorder/custom?api_key=${API_KEY}&user_id=8&limit=2" | jq '.data[0] | keys' 2>/dev/null | head -15
echo ""

echo ""
echo "3️⃣  Testing API Health"
echo "------------------------------------------"
curl -s "${BASE_URL}/health" | jq '.'
echo ""

echo ""
echo "4️⃣  Available endpoints (check docs)"
echo "------------------------------------------"
echo "📚 Open this in browser:"
echo "${BASE_URL}/docs"
echo ""
echo "=========================================="
