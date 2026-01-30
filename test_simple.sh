#!/bin/bash

# Simple test script for API endpoints
BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"

echo "======================================"
echo "Testing NetSuite API Endpoints"
echo "======================================"
echo ""

echo "1. Testing ORIGINAL endpoint: /api/netsuite/customer"
echo "--------------------------------------"
curl -s "${BASE_URL}/api/netsuite/customer?api_key=${API_KEY}&limit=2" | jq '.' | head -50
echo ""
echo ""

echo "2. Testing NEW /database endpoint: /api/netsuite/customer/database"
echo "--------------------------------------"
curl -s "${BASE_URL}/api/netsuite/customer/database?api_key=${API_KEY}&limit=2" | jq '.' | head -50
echo ""
echo ""

echo "3. Testing NEW /airbyte endpoint: /api/netsuite/customer/airbyte"
echo "--------------------------------------"
curl -s "${BASE_URL}/api/netsuite/customer/airbyte?api_key=${API_KEY}&limit=2" | jq '.' | head -50
echo ""
echo ""

echo "======================================"
echo "Test Complete!"
echo "======================================"
