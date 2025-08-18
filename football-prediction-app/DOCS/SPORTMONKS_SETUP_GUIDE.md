# SportMonks Integration Setup Guide

## Overview

The application now automatically uses SportMonks data when available. The v1 API endpoints (`/api/v1/fixtures`, `/api/v1/teams`, `/api/v1/predictions`) will automatically serve SportMonks data if it exists in the database.

## Setup Steps

### 1. Set Environment Variable

Add your SportMonks API key to Render:

1. Go to your backend service in Render
2. Navigate to "Environment" tab
3. Add:
   - Key: `SPORTMONKS_API_KEY`
   - Value: `your_sportmonks_api_key_here`
4. Save and let the service redeploy

### 2. Initial Data Sync

Once deployed with the API key, the application will automatically sync data on the first request. You can also manually trigger a sync:

```bash
# Manual sync via API endpoint
curl -X POST https://your-backend.onrender.com/api/v1/data/sync-sportmonks \
  -H "Content-Type: application/json"
```

### 3. Verify Data

Check if SportMonks data is being used:

```bash
# Check fixtures - should show "data_source": "sportmonks"
curl https://your-backend.onrender.com/api/v1/fixtures

# Check teams
curl https://your-backend.onrender.com/api/v1/teams

# Check predictions
curl https://your-backend.onrender.com/api/v1/predictions
```

## How It Works

### Automatic Fallback System

The v1 API endpoints now implement a smart fallback system:

1. **First Priority**: SportMonks data (if available)
2. **Fallback**: Local database data (if no SportMonks data)

This ensures the app always returns data, even without SportMonks.

### Data Synced

On initialization, the system syncs:
- **Leagues**: Premier League, La Liga, Serie A, Bundesliga, Ligue 1
- **Teams**: All teams from these leagues
- **Fixtures**: Past 30 days and next 30 days
- **Predictions**: For all upcoming fixtures

### Response Format

Endpoints now include a `data_source` field:

```json
{
  "matches": [...],
  "pagination": {...},
  "data_source": "sportmonks"  // or "local"
}
```

## Frontend Integration

**No frontend changes required!** The frontend continues to use the same endpoints:
- `/api/v1/fixtures` → Now serves SportMonks fixtures
- `/api/v1/teams` → Now serves SportMonks teams  
- `/api/v1/predictions` → Now serves SportMonks predictions

## Monitoring

### Check SportMonks Status

```bash
curl https://your-backend.onrender.com/api/health
```

Look for:
```json
{
  "services": {
    "sportmonks": {
      "status": "configured"
    }
  }
}
```

### Check Data Source

All v1 endpoints now return a `data_source` field indicating whether data comes from SportMonks or local database.

## Troubleshooting

### No SportMonks Data Showing

1. **Check API Key**: Ensure `SPORTMONKS_API_KEY` is set in Render
2. **Manual Sync**: Run the sync endpoint
3. **Check Logs**: Look for "Using SportMonks data" in logs

### API Limits

SportMonks has rate limits. The system caches data to minimize API calls:
- Fixtures are cached and only updated periodically
- Use the scheduler for automatic updates

### Performance

First request after deployment may be slow as data syncs. Subsequent requests use cached database data.

## Advanced Configuration

### Automatic Updates

To enable automatic updates, set:
```
ENABLE_SCHEDULER=true
```

This will periodically sync new fixtures and update scores.

### Custom Sync Intervals

Modify `sportmonks_scheduler.py` to adjust sync frequencies.

## Benefits

1. **Real Data**: Live football data instead of sample data
2. **Predictions**: Professional predictions from SportMonks
3. **Auto Updates**: Scores and fixtures update automatically
4. **No Frontend Changes**: Works with existing frontend code
5. **Fallback Support**: Still works without SportMonks