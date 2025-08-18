# Frontend Environment Setup for Render

## Problem
The frontend needs to know the backend API URL. In local development, it defaults to `http://localhost:5000`, but in production it needs to point to your deployed backend.

## Solution

### Option 1: Set Environment Variable in Render (Recommended)

1. Go to your frontend static site service in Render dashboard
2. Navigate to "Environment" tab
3. Add a new environment variable:
   - Key: `VITE_API_BASE_URL`
   - Value: `https://your-backend-service.onrender.com` (replace with your actual backend URL)
4. Trigger a manual deploy or push a commit to rebuild

### Option 2: Use a Proxy (If frontend and backend are on same domain)

If you're using a reverse proxy or serving both frontend and backend from the same domain, the frontend will automatically use relative URLs in production.

### Option 3: Hardcode for Quick Fix

As a temporary solution, you can modify `frontend/src/lib/api.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.PROD ? 'https://your-backend.onrender.com' : 'http://localhost:5000');
```

## Verification

After setting up, your frontend should:
1. Make API calls to the correct backend URL
2. Show data in Fixtures, Predictions, and Teams pages
3. Not show any "Connection Refused" errors in the console

## Troubleshooting

If you still see localhost:5000 errors:
1. Ensure you've set the environment variable in Render
2. Trigger a rebuild of your frontend service
3. Clear your browser cache
4. Check the Network tab in browser DevTools to verify the API URL being used