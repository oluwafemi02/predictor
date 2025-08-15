#!/bin/bash

# Football Prediction App - Endpoint Testing Script

BACKEND_URL="https://football-prediction-backend-2cvi.onrender.com"
FRONTEND_URL="https://football-prediction-frontend-zx5z.onrender.com"

echo "=== Testing Football Prediction App Endpoints ==="
echo ""

# Test CORS
echo "1. Testing CORS configuration..."
curl -X OPTIONS "$BACKEND_URL/api/sportmonks/test-cors" \
  -H "Origin: $FRONTEND_URL" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v 2>&1 | grep -E "(< HTTP|< Access-Control-)"

echo ""
echo "2. Testing CORS test endpoint..."
curl -X GET "$BACKEND_URL/api/sportmonks/test-cors" \
  -H "Origin: $FRONTEND_URL" \
  -s | jq '.'

echo ""
echo "3. Testing upcoming fixtures endpoint..."
curl -X GET "$BACKEND_URL/api/sportmonks/fixtures/upcoming?days=7&predictions=true" \
  -H "Origin: $FRONTEND_URL" \
  -s | jq '. | {count: .count, is_mock_data: .is_mock_data, fixtures: (.fixtures | length)}'

echo ""
echo "4. Testing squad endpoint..."
curl -X GET "$BACKEND_URL/api/sportmonks/squad/1" \
  -H "Origin: $FRONTEND_URL" \
  -s | jq '. | {team: .team.name, players_count: (.players | length), is_mock_data: .is_mock_data}'

echo ""
echo "5. Testing leagues endpoint..."
curl -X GET "$BACKEND_URL/api/sportmonks/leagues" \
  -H "Origin: $FRONTEND_URL" \
  -s | jq '. | {leagues_count: (.leagues | length)}'

echo ""
echo "6. Testing live fixtures endpoint..."
curl -X GET "$BACKEND_URL/api/sportmonks/fixtures/live" \
  -H "Origin: $FRONTEND_URL" \
  -s | jq '. | {fixtures_count: (.fixtures | length)}'

echo ""
echo "=== Testing Complete ==="
echo ""
echo "Note: If you see 'is_mock_data: true', it means SportMonks API key is not configured."
echo "This is expected behavior and the app will still function with mock data."