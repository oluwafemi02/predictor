#!/bin/bash

# Test CORS fixes for football prediction app

BACKEND_URL="https://football-prediction-backend-2cvi.onrender.com"
FRONTEND_ORIGIN="https://football-prediction-frontend-zx5z.onrender.com"

echo "Testing CORS Configuration"
echo "=========================="
echo ""

# Test 1: OPTIONS preflight request
echo "1. Testing OPTIONS preflight request..."
echo "--------------------------------------"
curl -X OPTIONS \
  "$BACKEND_URL/api/sportmonks/fixtures/upcoming" \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v 2>&1 | grep -E "(< HTTP|< Access-Control-)"

echo ""
echo ""

# Test 2: Test CORS endpoint
echo "2. Testing dedicated CORS test endpoint..."
echo "-----------------------------------------"
curl -X GET \
  "$BACKEND_URL/api/test-cors" \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Accept: application/json" \
  -w "\nResponse Time: %{time_total}s\n" \
  -s | jq '.'

echo ""
echo ""

# Test 3: Test actual API endpoint without predictions
echo "3. Testing fixtures endpoint (without predictions)..."
echo "----------------------------------------------------"
START_TIME=$(date +%s)
curl -X GET \
  "$BACKEND_URL/api/sportmonks/fixtures/upcoming?days=7&predictions=false" \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n" \
  -s -o /tmp/fixtures_response.json
END_TIME=$(date +%s)
echo "Total Time: $((END_TIME - START_TIME))s"
echo "Response preview:"
cat /tmp/fixtures_response.json | jq '.fixtures[0] // .error // .' 2>/dev/null || cat /tmp/fixtures_response.json | head -n 5

echo ""
echo ""

# Test 4: Test SportMonks test-cors endpoint
echo "4. Testing SportMonks test-cors endpoint..."
echo "------------------------------------------"
curl -X GET \
  "$BACKEND_URL/api/sportmonks/test-cors" \
  -H "Origin: $FRONTEND_ORIGIN" \
  -H "Accept: application/json" \
  -w "\nResponse Time: %{time_total}s\n" \
  -s | jq '.'

echo ""
echo "CORS Test Complete!"