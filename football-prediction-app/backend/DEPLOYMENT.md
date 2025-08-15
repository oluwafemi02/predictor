# Backend Deployment Guide for Render

## Critical Issues Fixed

1. **CORS Configuration**: Updated to properly allow the frontend domain
2. **SportMonks Endpoints**: All required endpoints exist and are properly configured
3. **Error Handling**: Improved to prevent 502 errors
4. **Performance**: Optimized API calls to reduce timeouts

## Environment Variables Required

Set these environment variables in your Render service:

### Required Variables

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-secure-secret-key>

# Database (Usually auto-configured by Render)
DATABASE_URL=<your-postgres-url>

# SportMonks API (At least one required)
SPORTMONKS_API_KEY=<your-sportmonks-api-key>
# OR
SPORTMONKS_PRIMARY_TOKEN=<your-primary-token>
SPORTMONKS_FALLBACK_TOKENS=<comma-separated-backup-tokens>

# CORS Configuration (CRITICAL)
CORS_ORIGINS=https://football-prediction-frontend-zx5z.onrender.com

# Token Encryption (Required in production)
TOKEN_ENCRYPTION_PASSWORD=<generate-strong-password>
TOKEN_ENCRYPTION_SALT=<generate-salt>
```

### Optional but Recommended

```bash
# Redis for caching (reduces API calls)
REDIS_URL=<your-redis-url>

# RapidAPI for odds data
RAPIDAPI_KEY=<your-rapidapi-key>

# Enable scheduler
ENABLE_SCHEDULER=true
```

## Generating Secure Values

### Generate SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Generate Encryption Password and Salt
```bash
python -c "import secrets; print(f'PASSWORD: {secrets.token_urlsafe(32)}\nSALT: {secrets.token_urlsafe(32)}')"
```

## Deployment Steps

1. **Update Environment Variables in Render Dashboard**
   - Go to your backend service on Render
   - Navigate to Environment settings
   - Add all required variables listed above

2. **Verify CORS Configuration**
   - Ensure `CORS_ORIGINS` includes your exact frontend URL
   - Multiple origins can be comma-separated

3. **Check API Configuration**
   - At least one SportMonks token must be configured
   - If no token is set, endpoints will return mock data

4. **Test the Deployment**
   - Visit: `https://football-prediction-backend-2cvi.onrender.com/api/health`
   - Check that all services show as "connected" or "configured"

5. **Monitor for Errors**
   - Check Render logs for any startup errors
   - Look for "SportMonks routes registered successfully" message

## Troubleshooting

### 502 Bad Gateway Errors
- Usually caused by missing environment variables
- Check that SportMonks API key is set
- Verify Redis connection if using caching

### CORS Errors
- Ensure frontend URL is in CORS_ORIGINS
- Check for trailing slashes in URLs
- Verify the exact domain matches

### Slow Response Times
- Consider adding Redis for caching
- Check if SportMonks API rate limits are being hit
- Monitor the `/api/health` endpoint

## API Endpoints Now Available

All SportMonks endpoints are properly configured:
- `/api/sportmonks/fixtures/upcoming`
- `/api/sportmonks/schedules/teams/{team_id}`
- `/api/sportmonks/schedules/seasons/{season_id}/teams/{team_id}`
- `/api/sportmonks/fixtures/between/{start_date}/{end_date}/{team_id}`

## Performance Optimizations Made

1. Reduced API timeout from 30s to 15s
2. Optimized date range queries to use single API call
3. Added graceful error handling to return 200 status with error info
4. Implemented caching support with Redis

## Next Steps

1. Deploy these changes to Render
2. Set all required environment variables
3. Test the health endpoint
4. Monitor logs for any issues