#!/bin/bash

# Test custom Vietnamese format endpoint
BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"

echo "🚀 Waiting for Railway deployment..."
sleep 30

echo ""
echo "======================================"
echo "Testing Custom Vietnamese Format API"
echo "======================================"
echo ""

# Test với salesorder (giống hình bạn gửi)
echo "📦 Testing: /api/netsuite/salesorder/custom"
echo "--------------------------------------"
echo ""

RESPONSE=$(curl -s "${BASE_URL}/api/netsuite/salesorder/custom?api_key=${API_KEY}&user_id=8&limit=5")

# Check if successful
SUCCESS=$(echo "$RESPONSE" | jq -r '.success' 2>/dev/null)

if [ "$SUCCESS" = "true" ]; then
    echo "✅ Success!"
    echo ""
    echo "📊 Response structure:"
    echo "$RESPONSE" | jq '{success, user, count, data: (.data | if length > 0 then [.[0]] else [] end)}' 2>/dev/null
    echo ""
    
    # Show first record details
    echo "📝 First record fields:"
    echo "$RESPONSE" | jq '.data[0] | keys' 2>/dev/null
    echo ""
    
    echo "📋 Sample data:"
    echo "$RESPONSE" | jq '.data[0]' 2>/dev/null | head -30
    
else
    echo "❌ Failed or still deploying..."
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
fi

echo ""
echo "======================================"
echo ""
echo "🔗 Full URL để test:"
echo "${BASE_URL}/api/netsuite/salesorder/custom?api_key=${API_KEY}&user_id=8&limit=100"
echo ""
echo "📚 API Docs:"
echo "${BASE_URL}/docs"
echo ""
