#!/bin/bash

# Test Saved Search RESTlet endpoint
BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"

echo "⏳ Waiting 45s for deployment..."
sleep 45

echo ""
echo "=========================================="
echo "🧪 Testing Saved Search RESTlet Endpoint"
echo "=========================================="
echo ""

echo "📋 Test: Call Saved Search RESTlet (limit 3)"
echo "------------------------------------------"

RESPONSE=$(curl -s "${BASE_URL}/api/reports/saved-search?api_key=${API_KEY}&user_id=8&limit=3")

SUCCESS=$(echo "$RESPONSE" | jq -r '.success' 2>/dev/null)

if [ "$SUCCESS" = "true" ]; then
    echo "✅ SUCCESS!"
    echo ""
    
    COUNT=$(echo "$RESPONSE" | jq -r '.count')
    echo "📊 Total records: $COUNT"
    echo ""
    
    echo "📝 Available fields (first record):"
    echo "$RESPONSE" | jq '.data[0] | keys' 2>/dev/null | head -30
    echo ""
    
    echo "🔍 Sample record:"
    echo "$RESPONSE" | jq '.data[0]' 2>/dev/null
    echo ""
    
else
    echo "❌ FAILED or still deploying..."
    echo ""
    echo "Response:"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
fi

echo ""
echo "=========================================="
echo ""
echo "🔗 Endpoint URL:"
echo "${BASE_URL}/api/reports/saved-search?api_key=${API_KEY}&user_id=8&limit=10"
echo ""
echo "📚 API Docs:"
echo "${BASE_URL}/docs"
echo ""
echo "=========================================="
echo ""
echo "💡 Tips:"
echo "- RESTlet URL is configurable via 'restlet_url' parameter"
echo "- Supports limit and offset for pagination"
echo "- Returns all fields from your Saved Search"
echo "- Includes custom fields automatically"
echo ""
