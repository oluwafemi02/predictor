#!/bin/bash

echo "🚀 Football API Token Test"
echo ""

# Load the API key from .env file
if [ -f .env ]; then
    export $(cat .env | grep FOOTBALL_API_KEY | xargs)
else
    echo "❌ Error: .env file not found"
    exit 1
fi

if [ -z "$FOOTBALL_API_KEY" ]; then
    echo "❌ Error: FOOTBALL_API_KEY not found in .env"
    exit 1
fi

echo "✅ API Key found: ${FOOTBALL_API_KEY:0:8}...${FOOTBALL_API_KEY: -4}"
echo ""
echo "🔍 Testing API connection to football-data.org..."
echo ""

# Test the API
response=$(curl -s -w "\n%{http_code}" -H "X-Auth-Token: $FOOTBALL_API_KEY" "https://api.football-data.org/v4/competitions")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

echo "📡 Status Code: $http_code"
echo ""

if [ "$http_code" = "200" ]; then
    echo "✅ API connection successful!"
    echo ""
    echo "📊 Response preview:"
    echo "$body" | head -c 500
    echo "..."
    
    # Count competitions if jq is available
    if command -v jq &> /dev/null; then
        count=$(echo "$body" | jq '.count')
        echo ""
        echo "📋 Total competitions: $count"
        echo ""
        echo "Sample competitions:"
        echo "$body" | jq -r '.competitions[:5] | .[] | "  - \(.name) (\(.code))"'
    fi
    
elif [ "$http_code" = "403" ]; then
    echo "❌ Error: Invalid API key or insufficient permissions"
    echo "Response: $body"
elif [ "$http_code" = "429" ]; then
    echo "⚠️  Rate limit exceeded. Please wait before trying again."
else
    echo "❌ Error: Unexpected status code $http_code"
    echo "Response: $body"
fi

echo ""
echo "🔍 Testing Flask application..."
echo ""

# Test Flask health endpoint
flask_response=$(curl -s -w "\n%{http_code}" "http://localhost:5000/api/health" 2>/dev/null)
flask_code=$(echo "$flask_response" | tail -n1)

if [ "$flask_code" = "200" ]; then
    echo "✅ Flask app is running"
else
    echo "❌ Flask app is not running"
    echo "💡 Start the app with: python3 app.py"
fi