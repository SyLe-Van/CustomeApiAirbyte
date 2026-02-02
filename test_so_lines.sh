#!/bin/bash

# Test new salesorder-lines endpoint
BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"

echo "⏳ Waiting 45s for deployment..."
sleep 45

echo ""
echo "=========================================="
echo "🧪 Testing Sales Order Lines Endpoint"
echo "=========================================="
echo ""

echo "📋 Test: Get 2 sales orders (will return multiple line items)"
echo "------------------------------------------"

RESPONSE=$(curl -s "${BASE_URL}/api/reports/salesorder-lines?api_key=${API_KEY}&user_id=8&limit=2")

SUCCESS=$(echo "$RESPONSE" | jq -r '.success' 2>/dev/null)

if [ "$SUCCESS" = "true" ]; then
    echo "✅ SUCCESS!"
    echo ""
    
    COUNT=$(echo "$RESPONSE" | jq -r '.count')
    echo "📊 Total line items returned: $COUNT"
    echo ""
    
    echo "📝 Available fields:"
    echo "$RESPONSE" | jq '.data[0] | keys' 2>/dev/null
    echo ""
    
    echo "🔍 Sample record (first line item):"
    echo "$RESPONSE" | jq '.data[0]' 2>/dev/null
    echo ""
    
    echo "📊 Summary of fields with data:"
    echo "$RESPONSE" | jq '.data[0] | to_entries | map(select(.value != "")) | from_entries | keys' 2>/dev/null
    
else
    echo "❌ FAILED"
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
fi

echo ""
echo "=========================================="
echo ""
echo "🔗 Full URL for testing:"
echo "${BASE_URL}/api/reports/salesorder-lines?api_key=${API_KEY}&user_id=8&limit=5"
echo ""
echo "📚 API Docs:"
echo "${BASE_URL}/docs"
echo ""
