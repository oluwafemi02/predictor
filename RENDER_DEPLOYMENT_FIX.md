# Render Deployment Fix Guide

## Issue: TOKEN_ENCRYPTION_PASSWORD Error

The backend deployment is failing with:
```
ValueError: TOKEN_ENCRYPTION_PASSWORD must be set in production!
```

## Root Cause

The `render.yaml` was configured to use `generateValue: true` for TOKEN_ENCRYPTION_PASSWORD and TOKEN_ENCRYPTION_SALT, but these need to be specific values suitable for cryptographic operations, not just random UUIDs.

## Solution

### Step 1: Generate Secure Values

Run this command locally to generate secure values:

```bash
python -c "import secrets; print(f'TOKEN_ENCRYPTION_PASSWORD={secrets.token_urlsafe(32)}\nTOKEN_ENCRYPTION_SALT={secrets.token_urlsafe(32)}')"
```

This will output something like:
```
TOKEN_ENCRYPTION_PASSWORD=J8K9L0M1N2O3P4Q5R6S7T8U9V0W1X2Y3
TOKEN_ENCRYPTION_SALT=A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6
```

### Step 2: Add to Render Dashboard

1. Go to your Render dashboard
2. Navigate to your `football-prediction-backend` service
3. Click on "Environment" tab
4. Add or update these environment variables:
   - `TOKEN_ENCRYPTION_PASSWORD`: (paste the generated password)
   - `TOKEN_ENCRYPTION_SALT`: (paste the generated salt)

### Step 3: Update Other Required Variables

While you're there, ensure these are also set:
- `SECRET_KEY`: (if not already set, generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `INTERNAL_API_KEYS`: (can leave the generated value or create your own)
- `SPORTMONKS_API_KEY`: Your SportMonks API key
- `RAPIDAPI_KEY`: Your RapidAPI key (if using odds feature)

### Step 4: Redeploy

1. Click "Manual Deploy" > "Deploy latest commit"
2. Monitor the deployment logs

## Alternative: Update via Render CLI

If you have the Render CLI installed:

```bash
# Set environment variables
render env:set TOKEN_ENCRYPTION_PASSWORD=your_generated_password
render env:set TOKEN_ENCRYPTION_SALT=your_generated_salt

# Trigger deployment
render deploy
```

## Verification

After successful deployment:
1. Check the service logs for startup messages
2. Visit `/api/health` endpoint to verify the service is running
3. Test the authentication endpoints

## Prevention

The `render.yaml` has been updated to use `sync: false` for these variables, requiring manual configuration but ensuring proper values are used.

## Additional Security Notes

1. **Never commit these values to git**
2. **Use different values for staging and production**
3. **Rotate these values periodically** (requires re-encrypting stored tokens)
4. **Keep a secure backup** of these values

## Related Environment Variables

For a complete list of required environment variables, see `/backend/.env.example`