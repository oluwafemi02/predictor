# SportMonks Live Data Setup Guide

## Current Status

✅ **SportMonks API Key is already configured** in your Render environment
✅ **Backend is deployed and running**
✅ **Frontend is deployed** (pending routing fix in Render dashboard)

## Step 1: Trigger Initial Data Sync

Once your backend is running, trigger the SportMonks data sync:

```bash
# Replace with your actual backend URL
curl -X POST https://your-backend.onrender.com/api/v1/data/sync-sportmonks \
  -H "Content-Type: application/json"
```

This will:
1. Sync Premier League, La Liga, Serie A, Bundesliga, and Ligue 1
2. Import all teams from these leagues
3. Get fixtures for the past 30 days and next 30 days
4. Fetch predictions for upcoming matches

## Step 2: Verify Data is Loaded

Check that SportMonks data is being served:

```bash
# Check fixtures
curl https://your-backend.onrender.com/api/v1/fixtures

# Look for "data_source": "sportmonks" in the response
```

## Step 3: Understanding the Predictions

SportMonks provides comprehensive prediction data:

### Main Predictions Available:
- **Fulltime Result**: Home win %, Draw %, Away win %
- **Both Teams to Score**: Yes/No probability
- **Over/Under 2.5 Goals**: Probability of total goals
- **Correct Score**: Probability for each scoreline
- **Double Chance**: Home/Draw, Away/Draw, Home/Away
- **Half Time Result**: First half outcome probabilities

### How Predictions are Displayed:

In your app, predictions show:
- Win/Draw/Loss percentages
- Most likely score
- Confidence level
- Both teams to score probability

## Step 4: Data Updates

### Manual Update
Run the sync endpoint again anytime:
```bash
curl -X POST https://your-backend.onrender.com/api/v1/data/sync-sportmonks
```

### Automatic Updates (Future)
To enable automatic updates:
1. Set `ENABLE_SCHEDULER=true` in Render environment
2. Or set up a cron job to call the sync endpoint periodically

## Step 5: API Response Examples

### Fixtures Response (with SportMonks data):
```json
{
  "matches": [
    {
      "id": 19427473,
      "date": "2025-08-25T19:00:00",
      "home_team": {
        "id": 20,
        "name": "Newcastle United",
        "logo_url": "https://cdn.sportmonks.com/images/soccer/teams/20/20.png"
      },
      "away_team": {
        "id": 8,
        "name": "Liverpool",
        "logo_url": "https://cdn.sportmonks.com/images/soccer/teams/8/8.png"
      },
      "status": "Not Started",
      "competition": "Premier League",
      "venue": "St. James' Park",
      "has_prediction": true
    }
  ],
  "data_source": "sportmonks"
}
```

### Predictions Response:
```json
{
  "predictions": [
    {
      "match": {
        "home_team": {"name": "Newcastle United"},
        "away_team": {"name": "Liverpool"}
      },
      "prediction": {
        "home_win": 0.36,
        "draw": 0.22,
        "away_win": 0.42,
        "confidence": 0.75,
        "predicted_score": {
          "home": 1,
          "away": 2
        }
      }
    }
  ],
  "data_source": "sportmonks"
}
```

## Troubleshooting

### No SportMonks Data Showing

1. **Check sync response**:
   ```bash
   curl -X POST https://your-backend.onrender.com/api/v1/data/sync-sportmonks
   ```
   Should return: `{"status": "success", "message": "SportMonks data sync completed successfully"}`

2. **Check API key**:
   - Verify `SPORTMONKS_API_KEY` is set in Render
   - Check `/api/health` endpoint for SportMonks status

3. **Check logs**:
   - Look for "Using SportMonks fixture data" in Render logs
   - Check for any API errors

### Rate Limits

SportMonks has rate limits. The sync process:
- Limits to 20 fixtures at a time for predictions
- Uses caching to minimize API calls
- Falls back to local data if API fails

## Benefits of SportMonks Integration

1. **Real Match Data**: Actual fixtures from top leagues
2. **Professional Predictions**: AI-powered predictions with multiple metrics
3. **Live Updates**: Scores update in real-time
4. **Rich Data**: Team logos, venues, referee info, and more
5. **Historical Data**: Past results for analysis

## Next Steps

1. **Monitor the data**: Check that fixtures and predictions are updating
2. **Customize leagues**: Modify `sportmonks_init.py` to add more leagues
3. **Add live scores**: Enable the scheduler for real-time updates
4. **Enhance predictions**: Use more SportMonks prediction types

Your app is now serving real football data with professional predictions! 🚀