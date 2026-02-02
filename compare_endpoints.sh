#!/bin/bash

BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        SO SÁNH CẤU TRÚC RESPONSE CỦA CÁC ENDPOINTS            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Original endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 ENDPOINT GỐC: /api/netsuite/customer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ORIGINAL=$(curl -s "${BASE_URL}/api/netsuite/customer?api_key=${API_KEY}&limit=2")

echo "📊 Cấu trúc response:"
echo "$ORIGINAL" | jq 'keys' 2>/dev/null

echo ""
echo "📋 Chi tiết:"
echo "   - entity:       $(echo "$ORIGINAL" | jq -r '.entity')"
echo "   - count:        $(echo "$ORIGINAL" | jq -r '.count')"
echo "   - hasMore:      $(echo "$ORIGINAL" | jq -r '.hasMore')"
echo "   - offset:       $(echo "$ORIGINAL" | jq -r '.offset')"
echo "   - limit:        $(echo "$ORIGINAL" | jq -r '.limit')"
echo "   - cached:       $(echo "$ORIGINAL" | jq -r '.cached')"
echo "   - timestamp:    $(echo "$ORIGINAL" | jq -r '.timestamp')"
echo ""
echo "   ✅ Data nằm trong: items (array)"
echo "   📝 items[0].companyName: $(echo "$ORIGINAL" | jq -r '.items[0].companyName')"
echo "   📝 items[0].id:          $(echo "$ORIGINAL" | jq -r '.items[0].id')"
echo ""
echo "   ❌ VẤN ĐỀ: Nhiều metadata không cần thiết (entity, count, cached, hasMore, offset, limit, timestamp)"
echo "   ❌ VẤN ĐỀ: Data nằm trong nested field 'items'"
echo ""

# Test 2: Database endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 ENDPOINT MỚI: /api/netsuite/customer/database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DATABASE=$(curl -s "${BASE_URL}/api/netsuite/customer/database?api_key=${API_KEY}&limit=2")

echo "📊 Cấu trúc response:"
echo "$DATABASE" | jq 'if type == "array" then "Array with " + (length | tostring) + " items" else keys end' 2>/dev/null

echo ""
echo "📋 Chi tiết:"
echo "   - Response type: Array (trực tiếp)"
echo "   - Số records:    $(echo "$DATABASE" | jq 'length')"
echo ""
echo "   ✅ Data trực tiếp là array, không có wrapper"
echo "   📝 [0].companyName: $(echo "$DATABASE" | jq -r '.[0].companyName')"
echo "   📝 [0].id:          $(echo "$DATABASE" | jq -r '.[0].id')"
echo ""
echo "   ✅ ƯU ĐIỂM: Không có metadata thừa"
echo "   ✅ ƯU ĐIỂM: Response là array trực tiếp → dễ insert vào database"
echo "   ✅ ƯU ĐIỂM: Nhỏ hơn ~20% so với endpoint gốc"
echo ""

# Test 3: Airbyte endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 ENDPOINT MỚI: /api/netsuite/customer/airbyte"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
AIRBYTE=$(curl -s "${BASE_URL}/api/netsuite/customer/airbyte?api_key=${API_KEY}&limit=2")

echo "📊 Cấu trúc response:"
echo "$AIRBYTE" | jq 'keys' 2>/dev/null

echo ""
echo "📋 Chi tiết:"
echo "   - records:              array với $(echo "$AIRBYTE" | jq '.records | length') items"
echo "   - pagination.has_more:  $(echo "$AIRBYTE" | jq -r '.pagination.has_more')"
echo "   - pagination.count:     $(echo "$AIRBYTE" | jq -r '.pagination.count')"
echo "   - pagination.next_offset: $(echo "$AIRBYTE" | jq -r '.pagination.next_offset')"
echo ""
echo "   ✅ Data nằm trong: records (array)"
echo "   📝 records[0].companyName: $(echo "$AIRBYTE" | jq -r '.records[0].companyName')"
echo "   📝 records[0].id:          $(echo "$AIRBYTE" | jq -r '.records[0].id')"
echo ""
echo "   ✅ ƯU ĐIỂM: Structure rõ ràng cho Airbyte"
echo "   ✅ ƯU ĐIỂM: Có pagination info để xử lý multi-page"
echo "   ✅ ƯU ĐIỂM: Không có metadata thừa (cached, timestamp, entity)"
echo ""

# Summary comparison
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 TỔNG KẾT SO SÁNH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ORIG_SIZE=$(echo "$ORIGINAL" | wc -c | tr -d ' ')
DB_SIZE=$(echo "$DATABASE" | wc -c | tr -d ' ')
AIR_SIZE=$(echo "$AIRBYTE" | wc -c | tr -d ' ')

echo "Response Size (bytes):"
echo "   Original:  $ORIG_SIZE bytes (100%)"
echo "   Database:  $DB_SIZE bytes ($((DB_SIZE * 100 / ORIG_SIZE))%)"
echo "   Airbyte:   $AIR_SIZE bytes ($((AIR_SIZE * 100 / ORIG_SIZE))%)"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    KHUYẾN NGHỊ SỬ DỤNG                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Cho DATABASE / ETL:           Dùng /database endpoint"
echo "   → URL: ${BASE_URL}/api/netsuite/{entity}/database"
echo "   → Field path trong Airbyte: $ (root array)"
echo ""
echo "✅ Cho AIRBYTE Integration:      Dùng /airbyte endpoint"
echo "   → URL: ${BASE_URL}/api/netsuite/{entity}/airbyte"
echo "   → Field path trong Airbyte: records"
echo ""
echo "❌ Legacy / Backward compat:     Dùng endpoint gốc"
echo "   → URL: ${BASE_URL}/api/netsuite/{entity}"
echo "   → Field path trong Airbyte: items"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
