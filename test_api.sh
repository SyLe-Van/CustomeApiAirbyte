#!/bin/bash

# Test NetSuite Proxy API

API_URL="http://localhost:8000"
API_KEY="netsuite_proxy_api_key_2026_secure"

echo "🧪 Testing NetSuite Proxy API..."
echo "================================="
echo ""

# Test 1: Health Check
echo "1️⃣ Testing health endpoint..."
HEALTH=$(curl -s "${API_URL}/health")
if echo "$HEALTH" | grep -q "ok"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi
echo ""

# Test 2: Readiness Check
echo "2️⃣ Testing readiness endpoint..."
READY=$(curl -s "${API_URL}/health/ready")
if echo "$READY" | grep -q "ready"; then
    echo "✅ Readiness check passed"
else
    echo "❌ Readiness check failed"
    exit 1
fi
echo ""

# Test 3: API Authentication
echo "3️⃣ Testing API authentication..."
AUTH_FAIL=$(curl -s "${API_URL}/api/netsuite/customer?limit=1" | grep -c "Unauthorized")
if [ "$AUTH_FAIL" -gt 0 ]; then
    echo "✅ Auth protection working"
else
    echo "❌ Auth protection not working"
    exit 1
fi
echo ""

# Test 4: Get Customers
echo "4️⃣ Testing customer endpoint..."
CUSTOMERS=$(curl -s -H "X-API-Key: ${API_KEY}" "${API_URL}/api/netsuite/customer?limit=5")
if echo "$CUSTOMERS" | grep -q "entity"; then
    echo "✅ Customer endpoint working"
    echo "Sample response:"
    echo "$CUSTOMERS" | python3 -m json.tool | head -20
else
    echo "❌ Customer endpoint failed"
    echo "Response: $CUSTOMERS"
    exit 1
fi
echo ""

# Test 5: Cache Check
echo "5️⃣ Testing cache endpoint..."
CACHE=$(curl -s -X DELETE -H "X-API-Key: ${API_KEY}" "${API_URL}/api/netsuite/cache")
if echo "$CACHE" | grep -q "cleared"; then
    echo "✅ Cache endpoint working"
else
    echo "❌ Cache endpoint failed"
fi
echo ""

echo "================================="
echo "🎉 All tests passed!"
echo ""
echo "API Information:"
echo "  URL: ${API_URL}"
echo "  API Key: ${API_KEY}"
echo ""
echo "Next steps:"
echo "  1. Configure Airbyte with these credentials"
echo "  2. Check docs/AIRBYTE_SETUP.md for details"
echo "  3. View API docs at ${API_URL}/docs"
