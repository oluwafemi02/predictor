# INTERNAL_API_KEYS Configuration Guide

## Purpose

The `INTERNAL_API_KEYS` environment variable is used to secure internal endpoints that should only be accessible by your own services, not external users. This includes:

- Manual data synchronization endpoints (`/api/sync/*`)
- Administrative functions
- Inter-service communication between the scheduler and API

## How It Works

1. **Authentication**: Endpoints decorated with `@require_api_key` check for an `X-API-Key` header
2. **Validation**: The provided key is checked against the comma-separated list in `INTERNAL_API_KEYS`
3. **Access**: Only requests with valid keys can access protected endpoints

## Generating Secure API Keys

### Option 1: Use Python (Recommended)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Option 2: Use OpenSSL
```bash
openssl rand -base64 32
```

### Option 3: Use UUID
```bash
python -c "import uuid; print(str(uuid.uuid4()))"
```

## Setting INTERNAL_API_KEYS on Render

### For Development/Testing
You can use a simple key like:
```
INTERNAL_API_KEYS=dev-key-12345
```

### For Production (Recommended)
Generate multiple keys for different services:
```
INTERNAL_API_KEYS=scheduler-key-abc123def456,admin-key-789xyz,monitoring-key-qrs456
```

### Steps to Configure on Render:

1. **Generate your keys**:
   ```bash
   # Generate 3 different keys
   KEY1=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   KEY2=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   KEY3=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   
   echo "INTERNAL_API_KEYS=$KEY1,$KEY2,$KEY3"
   ```

2. **Add to Render Dashboard**:
   - Go to your backend service on Render
   - Navigate to "Environment" tab
   - Add new environment variable:
     - Key: `INTERNAL_API_KEYS`
     - Value: Your generated keys (comma-separated)
   
3. **Add to Scheduler Worker**:
   - The scheduler worker needs the same keys
   - You can either:
     - Set the same value manually
     - Use Render's environment group feature
     - The scheduler will auto-generate one if not set (see below)

## Auto-Generation Feature

The updated scheduler (`run_scheduler.py`) will automatically generate a secure API key if `INTERNAL_API_KEYS` is not set. This ensures the scheduler can always sync data, even if you forget to configure it.

## Using the API Keys

### In Code (Python)
```python
import requests

headers = {
    'X-API-Key': 'your-api-key-here',
    'Content-Type': 'application/json'
}

response = requests.post(
    'https://your-backend.onrender.com/api/sync/football-data/all',
    headers=headers
)
```

### Using cURL
```bash
curl -X POST https://your-backend.onrender.com/api/sync/status \
  -H "X-API-Key: your-api-key-here"
```

### In the Test Script
```bash
API_URL=https://your-backend.onrender.com \
TEST_API_KEY=your-api-key-here \
python test_fixes.py
```

## Protected Endpoints

The following endpoints require API key authentication:

- `POST /api/sync/football-data/all` - Sync all football data
- `POST /api/sync/sportmonks/fixtures` - Sync SportMonks fixtures
- `POST /api/sync/sportmonks/predictions` - Sync SportMonks predictions
- `POST /api/sync/force-all` - Force sync from all sources

## Security Best Practices

1. **Use Different Keys**: Generate different keys for different purposes
2. **Rotate Regularly**: Change keys periodically (monthly/quarterly)
3. **Limit Access**: Only give keys to services that need them
4. **Monitor Usage**: Check logs for unauthorized access attempts
5. **Use HTTPS**: Always use HTTPS in production to protect keys in transit

## Example Configuration

Here's a complete example for production:

```bash
# Generate three secure keys
SCHEDULER_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ADMIN_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
MONITORING_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Set in Render
INTERNAL_API_KEYS=$SCHEDULER_KEY,$ADMIN_KEY,$MONITORING_KEY

# Example output (DO NOT USE THESE - GENERATE YOUR OWN):
# INTERNAL_API_KEYS=KJ8n9mN2xPQr5sT7uVwX3yZ1aBcDeFgH,MnO4pQrS6tUvW8xYz2AbC3dEfGhJ5kL,YzA1bC2dE3fG4hJ5kL6mN7oPqR8sT9uV
```

## Troubleshooting

### "API key required" Error
- Ensure you're sending the `X-API-Key` header
- Check that the header name is exactly `X-API-Key` (case-sensitive)

### "Invalid API key" Error
- Verify your key matches one in `INTERNAL_API_KEYS`
- Check for extra spaces or quotes in the environment variable
- Ensure no trailing commas in the key list

### Scheduler Can't Sync
- Check scheduler logs for the auto-generated key
- Ensure the scheduler service has the environment variable set
- Verify database connectivity

## Summary

The `INTERNAL_API_KEYS` system provides a simple but effective way to secure internal endpoints while allowing your services to communicate. The scheduler can auto-generate a key if needed, ensuring automatic data sync works out of the box.