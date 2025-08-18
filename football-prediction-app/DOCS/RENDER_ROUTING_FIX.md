# Fix for "Not Found" Error on Page Refresh

## Problem
When refreshing any page other than the home page (e.g., /fixtures, /predictions), Render returns a "Not Found" error. This is because Render is looking for actual files at those paths, but React Router handles routing client-side.

## Solution

### For Render Static Sites

1. **Check Build Settings** in Render Dashboard:
   - Build Command: `npm install && npm run build`
   - Publish Directory: `build`

2. **Add Redirect Rules** in Render Dashboard:
   - Go to your static site service
   - Navigate to "Redirects/Rewrites" tab
   - Add this rule:
     ```
     Source: /*
     Destination: /index.html
     Type: Rewrite
     Status: 200
     ```

3. **Alternative: Use Headers**
   - In the "Headers" tab, you can add:
     ```
     /*
     Cache-Control: no-cache
     ```

### Files Already in Place

The following files have been added to handle routing:
- `/frontend/public/_redirects` - Netlify-style redirects (Render supports this)
- `/frontend/public/404.html` - Fallback for 404 errors
- `/render.yaml` - Render configuration with routing rules

### Manual Configuration

If the automatic configuration doesn't work, manually configure in Render:

1. Go to your Frontend Static Site in Render
2. Click "Settings"
3. Scroll to "Redirect and Rewrite Rules"
4. Add:
   - Source path: `/*`
   - Destination path: `/index.html`
   - Type: `Rewrite`
   - Status code: `200`

### Testing

After deployment:
1. Navigate to `/fixtures`
2. Refresh the page
3. It should load correctly without "Not Found"

### Why This Happens

Single Page Applications (SPAs) like React handle routing on the client side. When you navigate to `/fixtures`, React Router updates the URL without making a server request. But when you refresh, the browser asks the server for `/fixtures`, which doesn't exist as a physical file. The rewrite rule tells the server to always serve `index.html`, allowing React Router to take over.