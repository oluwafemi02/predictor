# Frontend Deployment Fix Guide

## Issue Identified

The frontend at https://football-prediction-frontend-zx5z.onrender.com is not displaying content because it was built with the wrong backend API URL (localhost:5000 instead of the production backend).

## Current Status

- ✅ Backend is working at: https://football-prediction-backend-2cvi.onrender.com
- ✅ Frontend is deployed at: https://football-prediction-frontend-zx5z.onrender.com
- ❌ Frontend is using wrong API URL: http://localhost:5000/api
- ✅ Database has match data (150 finished matches)
- ⚠️ No upcoming matches in database (needs data seeding)

## Solution Steps

### 1. Update Frontend Environment Configuration

Create/update the `.env.production` file in the frontend directory:

```bash
# Production environment variables
REACT_APP_API_URL=https://football-prediction-backend-2cvi.onrender.com
REACT_APP_SPORTMONKS_ENABLED=true
```

### 2. Update Render Deployment Configuration

In your Render dashboard for the frontend service:

1. Go to the frontend service settings
2. Update Environment Variables:
   - `REACT_APP_API_URL` = `https://football-prediction-backend-2cvi.onrender.com`
   - `REACT_APP_SPORTMONKS_ENABLED` = `true`

### 3. Rebuild and Deploy

The frontend has already been rebuilt with the correct environment variables. The build directory contains the updated code.

To deploy on Render:
1. Commit the changes to your repository
2. Push to the branch connected to Render
3. Render will automatically rebuild and deploy

### 4. Manual Deployment Steps (if needed)

```bash
cd football-prediction-app/frontend

# Build with production environment
REACT_APP_API_URL=https://football-prediction-backend-2cvi.onrender.com npm run build

# The build directory is now ready for deployment
```

## Additional Issues to Address

### 1. Database Population

The database currently only has finished matches. To show predictions:

```bash
# SSH into backend or run via Render shell
cd football-prediction-app/backend
python populate_data.py --upcoming-matches
```

### 2. SportMonks Integration

Ensure SportMonks API credentials are set in backend environment variables:
- `SPORTMONKS_API_KEY`
- `SPORTMONKS_FALLBACK_TOKENS` (if using multiple tokens)

### 3. Enable Scheduler

For automatic data updates, enable the scheduler service in Render with:
- `ENABLE_SCHEDULER=true`
- `IS_SCHEDULER_INSTANCE=true`

## Verification Steps

After deployment, verify:

1. **Check API connectivity:**
   ```bash
   curl https://football-prediction-backend-2cvi.onrender.com/api/v1/health
   ```

2. **Check frontend is using correct API:**
   - Open browser DevTools Network tab
   - Look for API calls to the correct backend URL

3. **Test main features:**
   - Dashboard should load match data
   - Predictions page should show upcoming matches (after data seeding)
   - SportMonks integration should work

## Quick Fix Summary

1. ✅ Frontend rebuilt with correct API URL
2. ⏳ Need to push changes to trigger Render deployment
3. ⏳ Need to populate database with upcoming matches
4. ⏳ Verify SportMonks API keys are configured

## Environment Variables Checklist

### Frontend (Render):
- [x] `REACT_APP_API_URL=https://football-prediction-backend-2cvi.onrender.com`
- [x] `REACT_APP_SPORTMONKS_ENABLED=true`

### Backend (Render):
- [ ] `SPORTMONKS_API_KEY` (required for live data)
- [ ] `DATABASE_URL` (auto-configured by Render)
- [ ] `CORS_ORIGINS` (should include frontend URLs)
- [ ] `ENABLE_SCHEDULER=false` (for main API)
- [ ] `TOKEN_ENCRYPTION_PASSWORD` (for secure token storage)
- [ ] `TOKEN_ENCRYPTION_SALT` (for secure token storage)