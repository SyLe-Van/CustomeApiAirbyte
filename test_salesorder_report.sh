#!/bin/bash

# Test Sales Order Detail Report endpoint
BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"
ENDPOINT="/api/reports/salesorder-detail"

echo "🚀 Waiting for Railway deployment..."
sleep 45

echo ""
echo "=========================================="
echo "Testing Sales Order Detail Report"
echo "=========================================="
echo ""

# Test 1: Basic query (limit 2 để test nhanh)
echo "📋 Test 1: Basic query (2 records)"
echo "------------------------------------------"
RESPONSE=$(curl -s "${BASE_URL}${ENDPOINT}?api_key=${API_KEY}&user_id=8&limit=2")

SUCCESS=$(echo "$RESPONSE" | jq -r '.success' 2>/dev/null)

if [ "$SUCCESS" = "true" ]; then
    echo "✅ SUCCESS!"
    echo ""
    
    COUNT=$(echo "$RESPONSE" | jq -r '.count')
    echo "📊 Record count: $COUNT"
    echo ""
    
    echo "📝 First record fields:"
    echo "$RESPONSE" | jq '.data[0] | keys' 2>/dev/null
    echo ""
    
    echo "🔍 Sample data (first record):"
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

# Test 2: With date filter
echo "📅 Test 2: With date filter (January 2026)"
echo "------------------------------------------"
RESPONSE2=$(curl -s "${BASE_URL}${ENDPOINT}?api_key=${API_KEY}&user_id=8&start_date=2026-01-01&end_date=2026-01-31&limit=5")

SUCCESS2=$(echo "$RESPONSE2" | jq -r '.success' 2>/dev/null)

if [ "$SUCCESS2" = "true" ]; then
    COUNT2=$(echo "$RESPONSE2" | jq -r '.count')
    echo "✅ SUCCESS! Found $COUNT2 records in January 2026"
    echo ""
    
    # Show sample fields
    echo "🔍 Vietnamese field names:"
    echo "$RESPONSE2" | jq '.data[0] | keys' 2>/dev/null | head -20
    
else
    echo "⚠️  Query still processing or error"
fi

echo ""
echo "=========================================="
echo ""

echo "🔗 Full URLs for testing:"
echo ""
echo "1. Basic query (10 records):"
echo "${BASE_URL}${ENDPOINT}?api_key=${API_KEY}&user_id=8&limit=10"
echo ""
echo "2. With date filter:"
echo "${BASE_URL}${ENDPOINT}?api_key=${API_KEY}&user_id=8&start_date=2026-01-01&end_date=2026-01-31&limit=100"
echo ""
echo "3. All data (default 10000 limit):"
echo "${BASE_URL}${ENDPOINT}?api_key=${API_KEY}&user_id=8"
echo ""
echo "=========================================="
echo ""
echo "📚 API Documentation:"
echo "${BASE_URL}/docs"
echo ""
