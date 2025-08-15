# CORS and Performance Fix Guide

## Issues Fixed

### 1. CORS Policy Errors
- **Problem**: Frontend at `https://football-prediction-frontend-zx5z.onrender.com` was being blocked by CORS policy
- **Root Cause**: Security headers were overriding Flask-CORS configuration
- **Solution**: 
  - Modified `security.py` to dynamically read allowed origins from app config
  - Enhanced preflight request handling in `app.py` with better logging
  - Ensured CORS headers are not overwritten by security middleware

### 2. Performance Issues
- **Problem**: API endpoints taking too long to respond
- **Solution**:
  - Added response time logging to all endpoints
  - Implemented batch prediction fetching instead of individual API calls
  - Added database caching for predictions (6-hour TTL)
  - Limited concurrent API calls to prevent timeouts

## Changes Made

### 1. `/workspace/football-prediction-app/backend/security.py`
```python
# Now reads CORS origins from app config instead of hardcoded list
from flask import current_app
allowed_origins = current_app.config.get('CORS_ORIGINS', [])
```

### 2. `/workspace/football-prediction-app/backend/app.py`
```python
# Enhanced preflight handling with logging
logger.info(f"OPTIONS request from origin: {origin}")
if origin and origin in app.config['CORS_ORIGINS']:
    # Set CORS headers
    logger.info(f"CORS headers set for origin: {origin}")
else:
    logger.warning(f"Origin {origin} not in allowed origins")
```

### 3. `/workspace/football-prediction-app/backend/sportmonks_routes.py`
```python
# Added response time logging
def handle_errors(f):
    start_time = time.time()
    # ... function execution ...
    response_time = end_time - start_time
    logger.info(f"{f.__name__} completed in {response_time:.2f}s")

# Optimized prediction fetching
# - First check database for recent predictions
# - Batch fetch missing predictions from API
# - Limit to 10 concurrent API calls to prevent timeout
```

## Deployment Steps

1. **Update Backend Code**
   ```bash
   git add .
   git commit -m "Fix CORS issues and optimize API performance"
   git push origin main
   ```

2. **Verify Environment Variables in Render Dashboard**
   - Ensure `CORS_ORIGINS` includes all frontend domains:
     ```
     https://football-prediction-frontend.onrender.com,https://football-prediction-frontend-zx5z.onrender.com,https://football-prediction-frontend-2cvi.onrender.com
     ```

3. **Monitor Logs**
   - Check Render logs for CORS debugging messages
   - Look for response time logs to identify slow endpoints

4. **Clear Browser Cache**
   - Clear browser cache and cookies
   - Try incognito/private browsing mode

## Testing

### Test CORS
```bash
curl -X OPTIONS \
  https://football-prediction-backend-2cvi.onrender.com/api/sportmonks/fixtures/upcoming \
  -H "Origin: https://football-prediction-frontend-zx5z.onrender.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

### Test Performance
```bash
time curl -X GET \
  "https://football-prediction-backend-2cvi.onrender.com/api/sportmonks/fixtures/upcoming?days=7&predictions=true" \
  -H "Origin: https://football-prediction-frontend-zx5z.onrender.com"
```

## Expected Response Times

- `/api/sportmonks/test-cors`: < 0.5s
- `/api/sportmonks/fixtures/upcoming` (without predictions): < 2s
- `/api/sportmonks/fixtures/upcoming` (with predictions, cached): < 1s
- `/api/sportmonks/fixtures/upcoming` (with predictions, fresh): < 5s

## Troubleshooting

1. **CORS Still Failing**
   - Check if frontend origin is in CORS_ORIGINS env var
   - Verify no proxy/CDN is stripping CORS headers
   - Check browser console for specific error messages

2. **Slow Response Times**
   - Check Redis connection (caching)
   - Monitor SportMonks API rate limits
   - Increase worker timeout in gunicorn if needed

3. **Database Performance**
   - Ensure indexes on fixture_id in predictions table
   - Consider upgrading database plan if needed

## Additional Optimizations

1. **Enable Redis Caching**
   - Verify Redis is connected and working
   - Cache timeout is set to 600s (10 minutes) for fixtures

2. **Database Indexing**
   ```sql
   CREATE INDEX idx_predictions_fixture_id ON sportmonks_predictions(fixture_id);
   CREATE INDEX idx_predictions_updated_at ON sportmonks_predictions(updated_at);
   ```

3. **Frontend Optimization**
   - Implement request debouncing
   - Add loading states with skeleton screens
   - Cache API responses in localStorage with TTL