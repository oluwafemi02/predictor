# CORS and Upcoming Matches Fix Deployment Guide

## Overview
This guide documents the fixes implemented to resolve:
1. CORS policy errors blocking API requests from the frontend
2. Upcoming matches not displaying
3. Predictions tab error handling
4. Squad data display issues

## Root Causes Identified

### 1. CORS Configuration Issue
- The backend CORS configuration was not handling preflight requests properly
- Production environment variable for CORS_ORIGINS might not be set

### 2. API Endpoint Mismatch
- Frontend was calling non-existent endpoints (`/api/v1/upcoming-matches`)
- Should be using SportMonks endpoints (`/api/sportmonks/fixtures/upcoming`)

### 3. Missing Error Handling
- Poor error messages made debugging difficult
- No handling for empty data responses

## Changes Made

### Backend Changes

#### 1. Enhanced CORS Configuration (`app.py`)
```python
# Added explicit preflight request handler
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        origin = request.headers.get('Origin')
        if origin in app.config['CORS_ORIGINS']:
            response.headers.add("Access-Control-Allow-Origin", origin)
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,X-API-Key")
            response.headers.add('Access-Control-Allow-Methods', "GET,POST,PUT,DELETE,OPTIONS")
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '3600')
        return response
```

#### 2. Updated Production CORS Origins (`config.py`)
```python
CORS_ORIGINS = [
    'https://football-prediction-frontend.onrender.com',
    'https://football-prediction-frontend-2cvi.onrender.com',
    'https://football-prediction-frontend-zx5z.onrender.com',
    'https://football-prediction-backend-2cvi.onrender.com'
]
```

### Frontend Changes

#### 1. Fixed API Service Functions (`services/api.ts`)
- Updated `getUpcomingMatches()` to use SportMonks endpoint
- Updated `getUpcomingPredictions()` to use SportMonks endpoint with predictions
- Added proper data transformation to match expected formats

#### 2. Enhanced Error Handling (`components/PredictionsView.tsx`)
- Added detailed error messages based on error type
- Improved error state handling
- Added null checks for response data

#### 3. Improved Squad Display (`components/SquadView.tsx`)
- Added logging for debugging
- Better error messages
- Handling for empty squad data
- Detection of mock data

## Deployment Steps

### 1. Backend Deployment

1. **Update Environment Variables on Render**
   ```bash
   # Add or update these environment variables:
   CORS_ORIGINS=https://football-prediction-frontend-zx5z.onrender.com,https://football-prediction-frontend-2cvi.onrender.com,https://football-prediction-backend-2cvi.onrender.com
   FLASK_ENV=production
   ```

2. **Deploy Backend**
   - Push changes to repository
   - Render should auto-deploy or manually trigger deployment
   - Wait for deployment to complete

### 2. Frontend Deployment

1. **Update Environment Variables on Render**
   ```bash
   # Add or update:
   REACT_APP_API_URL=https://football-prediction-backend-2cvi.onrender.com
   ```

2. **Deploy Frontend**
   - Push changes to repository
   - Render should auto-deploy or manually trigger deployment

### 3. Verification Steps

1. **Test CORS**
   - Open browser console
   - Navigate to Predictions tab
   - Should see no CORS errors

2. **Test Upcoming Matches**
   - Check Dashboard for upcoming matches
   - Verify matches are displaying

3. **Test Predictions**
   - Navigate to Predictions tab
   - Should see fixtures with predictions
   - Try different filters (time range, leagues)

4. **Test Squad Display**
   - Go to Squad view
   - Select a league and team
   - Should see squad data or appropriate message

## Troubleshooting

### If CORS errors persist:
1. Check backend logs for CORS configuration output
2. Verify environment variables are set correctly
3. Clear browser cache and cookies
4. Try incognito/private browsing mode

### If data doesn't display:
1. Check browser console for API errors
2. Verify SportMonks API key is configured
3. Check backend logs for API errors
4. Ensure database is properly connected

### Debug Endpoints:
- Health check: `https://football-prediction-backend-2cvi.onrender.com/api/sportmonks/health`
- Debug config: `https://football-prediction-backend-2cvi.onrender.com/api/sportmonks/debug/config`

## Summary

The main issues were:
1. CORS configuration not handling preflight requests
2. Frontend calling wrong API endpoints
3. Poor error handling masking the real issues

All issues have been addressed with proper fixes that:
- Handle CORS correctly in production
- Use the correct SportMonks API endpoints
- Provide clear error messages for debugging
- Handle empty/missing data gracefully