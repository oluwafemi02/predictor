# Automatic Data Synchronization Configuration

## Overview

This document explains how automatic data synchronization has been configured for the Football Prediction App on Render. After implementing these changes, your database will be automatically populated without manual intervention.

## 1. INTERNAL_API_KEYS Configuration

### Purpose
The `INTERNAL_API_KEYS` environment variable secures internal endpoints while allowing automated services (like the scheduler) to sync data.

### How to Set It

#### Option A: Let Scheduler Auto-Generate (Easiest)
The scheduler will automatically generate a secure key if `INTERNAL_API_KEYS` is not set. This is the simplest option for getting started.

#### Option B: Manual Configuration (Recommended for Production)

1. **Generate secure keys**:
   ```bash
   # Generate a single key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Or generate multiple keys
   python -c "import secrets; print(','.join([secrets.token_urlsafe(32) for _ in range(3)]))"
   ```

2. **Add to Render Dashboard**:
   - Navigate to your backend service
   - Go to "Environment" tab
   - Add: `INTERNAL_API_KEYS=your-generated-key-here`

3. **Example values**:
   ```
   # Single key (simple)
   INTERNAL_API_KEYS=Rk9L3mN7pQ2sT5uX8yA1bD4fG6hJ0kM_nP3qS6tV9wZ2

   # Multiple keys (advanced)
   INTERNAL_API_KEYS=key1_abc123,key2_def456,key3_ghi789
   ```

## 2. Automatic Sync Implementation

### What Was Changed

1. **Updated `run_scheduler.py`**:
   - Now properly starts BOTH schedulers (Football Data + SportMonks)
   - Auto-generates API key if needed
   - Performs initial sync if database is empty
   - Monitors scheduler health with auto-restart
   - Logs all scheduled jobs for transparency

2. **Scheduler Jobs Running Automatically**:

   **Football Data Scheduler**:
   - Historical data: Weekly
   - Upcoming matches: Twice daily (9 AM & 6 PM)
   - Match results: Every hour
   - Model training: Weekly (Sunday 11 PM)
   - Initial fetch: 60 seconds after startup

   **SportMonks Scheduler**:
   - Live scores: Every 30 seconds
   - Upcoming fixtures: Every 30 minutes
   - Predictions: Every 2 hours
   - Standings: Twice daily (2 AM & 2 PM)
   - Value bets: Every hour

### Deployment Steps

1. **Commit and push changes**:
   ```bash
   git add -A
   git commit -m "feat: configure automatic data synchronization"
   git push origin main
   ```

2. **Monitor deployment on Render**:
   - Watch the scheduler worker logs
   - Look for "Scheduler service is running"
   - Check for "Initial data sync completed"

3. **Verify it's working**:
   - Check database has data after ~5 minutes
   - Monitor scheduler logs for periodic job execution

## 3. Verification Methods

### Method 1: Check Sync Status
```bash
curl https://your-backend.onrender.com/api/sync/status
```

Expected response shows data counts:
```json
{
  "status": "success",
  "stats": {
    "database": {
      "teams": 20,
      "matches": 380,
      "sportmonks_fixtures": 150,
      "sportmonks_predictions": 75
    }
  }
}
```

### Method 2: Monitor Sync Progress
```bash
# Run monitoring script
API_URL=https://your-backend.onrender.com python monitor_sync.py

# Or check once
API_URL=https://your-backend.onrender.com python monitor_sync.py --once
```

### Method 3: Check Scheduler Logs
In Render dashboard:
1. Go to scheduler worker service
2. View logs
3. Look for:
   - "Scheduled Jobs" list
   - "Running job: [job name]"
   - "Initial data sync completed"

### Method 4: Database Query
If you have database access:
```sql
-- Check data counts
SELECT 
  (SELECT COUNT(*) FROM teams) as teams,
  (SELECT COUNT(*) FROM matches) as matches,
  (SELECT COUNT(*) FROM sportmonks_fixtures) as fixtures,
  (SELECT COUNT(*) FROM sportmonks_predictions) as predictions;
```

## 4. Troubleshooting

### No Data After Deployment

1. **Check scheduler is running**:
   - View scheduler worker logs
   - Should see "Scheduler service is running"

2. **Check API keys are configured**:
   - Football Data API: `FOOTBALL_API_KEY`
   - SportMonks API: `SPORTMONKS_API_KEY`
   - RapidAPI: `RAPIDAPI_KEY`

3. **Check database connection**:
   ```bash
   curl https://your-backend.onrender.com/api/sync/test-database
   ```

4. **Force manual sync** (if needed):
   ```bash
   curl -X POST https://your-backend.onrender.com/api/sync/force-all \
     -H "X-API-Key: your-internal-api-key"
   ```

### Scheduler Crashes

The updated scheduler has auto-restart capability. It checks health every hour and restarts failed schedulers.

### API Rate Limits

Both schedulers respect API rate limits. If you hit limits:
- SportMonks: Check `SPORTMONKS_FALLBACK_TOKENS`
- Adjust job frequencies in scheduler configuration

## 5. Summary of Changes

### Files Modified
- `run_scheduler.py` - Enhanced with auto-start, health monitoring
- `INTERNAL_API_KEYS_GUIDE.md` - Documentation for API keys
- `monitor_sync.py` - Tool to verify automatic sync
- This file - Complete automation guide

### Key Features
1. ✅ Automatic scheduler startup
2. ✅ Self-healing with auto-restart
3. ✅ Initial data population
4. ✅ Continuous data updates
5. ✅ No manual intervention required
6. ✅ Secure internal API access

### Schedule Summary
- **Live data**: Every 30 seconds
- **Fixtures**: Every 30 minutes  
- **Results**: Every hour
- **Predictions**: Every 2 hours
- **Standings**: Twice daily
- **Full sync**: Weekly

## 6. Production Checklist

- [ ] Generate and set `INTERNAL_API_KEYS`
- [ ] Verify all external API keys are set
- [ ] Deploy changes to Render
- [ ] Monitor scheduler startup logs
- [ ] Verify initial data sync completes
- [ ] Check sync status after 10 minutes
- [ ] Confirm scheduled jobs are running
- [ ] Test frontend still works correctly

## Result

After implementing these changes, your system will:
- ✅ Have properly configured `INTERNAL_API_KEYS`
- ✅ Automatically populate the database on startup
- ✅ Continuously sync new data without manual intervention
- ✅ Self-heal if schedulers fail
- ✅ Maintain frontend routing functionality

The system is now fully automated and production-ready! 🎉