#!/bin/bash

# Monitor and wait for deployment
BASE_URL="https://customeapiairbyte-production.up.railway.app"
API_KEY="netsuite_proxy_api_key_2026_secure"

echo "⏳ Monitoring Railway deployment..."
echo ""

MAX_RETRIES=20  # 20 * 15s = 5 minutes
for i in $(seq 1 $MAX_RETRIES); do
    echo "[$i/$MAX_RETRIES] Checking deployment status..."
    
    # Try the new custom endpoint
    RESPONSE=$(curl -s "${BASE_URL}/api/netsuite/salesorder/custom?api_key=${API_KEY}&user_id=8&limit=2" 2>/dev/null)
    ERROR=$(echo "$RESPONSE" | jq -r '.error' 2>/dev/null)
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success' 2>/dev/null)
    
    if [ "$SUCCESS" = "true" ]; then
        echo ""
        echo "✅ Deployment successful! New endpoint is live!"
        echo ""
        echo "📊 Response:"
        echo "$RESPONSE" | jq '.' 2>/dev/null
        echo ""
        echo "🎉 Endpoint URL:"
        echo "${BASE_URL}/api/netsuite/salesorder/custom?api_key=${API_KEY}&user_id=8"
        echo ""
        exit 0
    elif [ "$ERROR" != "Not Found" ] && [ "$ERROR" != "null" ] && [ -n "$ERROR" ]; then
        echo "⚠️  Endpoint available but returned error: $ERROR"
        echo "$RESPONSE" | jq '.'
        exit 0
    fi
    
    echo "   Still deploying... waiting 15s"
    sleep 15
done

echo ""
echo "⏰ Deployment taking longer than expected (5+ minutes)"
echo "Please check Railway dashboard: https://railway.app"
echo ""
echo "Manual test URL:"
echo "${BASE_URL}/api/netsuite/salesorder/custom?api_key=${API_KEY}&user_id=8&limit=10"
