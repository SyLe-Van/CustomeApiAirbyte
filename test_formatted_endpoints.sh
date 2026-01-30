#!/bin/bash

# Test script for formatted endpoints
# Usage: ./test_formatted_endpoints.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL=${1:-"https://customeapiairbyte-production.up.railway.app"}
API_KEY=${2:-"your_api_key_here"}

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Testing NetSuite Formatted API Endpoints${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}Base URL:${NC} $BASE_URL"
echo -e "${YELLOW}API Key:${NC} ${API_KEY:0:10}..."
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_structure=$3
    
    echo -e "${GREEN}Testing: $name${NC}"
    echo -e "URL: $url"
    echo ""
    
    response=$(curl -s -w "\n%{http_code}" "$url")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    echo "HTTP Code: $http_code"
    echo ""
    echo "Response (first 500 chars):"
    echo "$body" | head -c 500
    echo ""
    echo -e "${BLUE}---${NC}"
    echo ""
}

# Test 1: Original endpoint
echo -e "${YELLOW}[1/5] Testing Original Endpoint${NC}"
test_endpoint \
    "Original (with all metadata)" \
    "$BASE_URL/api/netsuite/customer?api_key=$API_KEY&limit=2" \
    "Should have: entity, count, items[], hasMore, cached, timestamp"

# Test 2: Database endpoint
echo -e "${YELLOW}[2/5] Testing Database Endpoint${NC}"
test_endpoint \
    "Database Format (array only)" \
    "$BASE_URL/api/netsuite/customer/database?api_key=$API_KEY&limit=2" \
    "Should be an array: [{...}, {...}]"

# Test 3: Airbyte endpoint
echo -e "${YELLOW}[3/5] Testing Airbyte Endpoint${NC}"
test_endpoint \
    "Airbyte Format" \
    "$BASE_URL/api/netsuite/customer/airbyte?api_key=$API_KEY&limit=2" \
    "Should have: records[], pagination{}"

# Test 4: Formatted endpoint - database format
echo -e "${YELLOW}[4/5] Testing Formatted Endpoint (database)${NC}"
test_endpoint \
    "Formatted - Database Type" \
    "$BASE_URL/api/netsuite/customer/formatted?format_type=database&api_key=$API_KEY&limit=2" \
    "Should be an array: [{...}, {...}]"

# Test 5: Formatted endpoint - flat format
echo -e "${YELLOW}[5/5] Testing Formatted Endpoint (flat)${NC}"
test_endpoint \
    "Formatted - Flat Type" \
    "$BASE_URL/api/netsuite/customer/formatted?format_type=flat&api_key=$API_KEY&limit=2" \
    "Should have: entity, count, data[]"

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Testing Complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "- Original endpoint: Full metadata (entity, count, items, cached, etc.)"
echo "- Database endpoint: Clean array only [{...}]"
echo "- Airbyte endpoint: {records[], pagination{}}"
echo "- Formatted endpoint: Flexible format based on format_type parameter"
echo ""
echo -e "${YELLOW}Recommendations:${NC}"
echo "✅ For database insertion: Use /database endpoint"
echo "✅ For Airbyte: Use /airbyte endpoint"
echo "✅ For flexibility: Use /formatted endpoint with format_type parameter"
echo ""
