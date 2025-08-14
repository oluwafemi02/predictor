# Flask App Deployment Fixes

## Critical Issues Fixed

### 1. Duplicate Health Route (PRIMARY ISSUE)
**Problem**: AssertionError at line 201 in app.py - duplicate endpoint function 'health'

**Root Cause**: 
- `/health` route defined in BOTH app.py (line 201) AND monitoring.py (line 363)
- When `setup_monitoring(app)` is called, it tries to register the same endpoint again

**Fix Applied**:
- Removed the health route from app.py (lines 201-227)
- Enhanced the health route in monitoring.py to include database checks
- The monitoring.py health route now handles all health check functionality

### 2. Import Errors Fixed

#### SportMonksClient Import Error
**File**: sync_routes.py
**Change**: `from sportmonks_client import SportMonksAPIClient as SportMonksClient`
- The class is actually named `SportMonksAPIClient`, not `SportMonksClient`

#### init_scheduler Import Error  
**File**: app.py
**Change**: 
```python
from scheduler import DataScheduler
scheduler = DataScheduler(app)
```
- There is no `init_scheduler` function, the scheduler class is `DataScheduler`

## Deployment Checklist

Before deploying, ensure:

1. **Commit all changes**:
   ```bash
   git add app.py sync_routes.py monitoring.py
   git commit -m "Fix duplicate health route and import errors"
   git push
   ```

2. **Clear any deployment cache on Render**:
   - Trigger a manual deploy
   - Or clear build cache if the option is available

3. **Environment Variables on Render**:
   - `DATABASE_URL` - PostgreSQL connection
   - `SECRET_KEY` - Flask secret key  
   - `REDIS_URL` - Redis connection (optional, app handles if missing)
   - `FOOTBALL_API_KEY` - API key for football data
   - `SPORTMONKS_API_KEY` - SportMonks API key

4. **Redis Note**: 
   - The app gracefully handles Redis connection failures
   - You'll see warnings but the app will still run

## Health Check Endpoints

After deployment, test:
- `/health` - Basic health check with database status
- `/health/detailed` - Comprehensive system status

## If Issues Persist

The error log shows it's still reading old code (line 201 has `@app.route('/health')`).
This indicates:
1. Changes aren't committed/pushed
2. Render is using cached build
3. Wrong branch is deployed

Verify the deployed code matches your local changes!