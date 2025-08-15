# SportMonks API Integration Fix Summary

## Date: August 15, 2025

## Issue Identified
The app was using the wrong SportMonks API endpoint (`/fixtures` with date filters) which wasn't returning any data. The correct endpoint is `/schedules/seasons/{season_id}/teams/{team_id}` which returns all fixtures for a team in a season.

## API Discovery
From the SportMonks API response, we found:
- **Season ID for EPL 2025-26**: 25583
- **Team ID for Liverpool**: 8
- **Today's Match**: Liverpool vs AFC Bournemouth at 19:00:00 UTC

## Changes Made

### 1. SportMonks Client Updates (`sportmonks_client.py`)

Added two new methods:
- `get_season_schedule(season_id, team_id)`: Fetches fixtures from the schedules endpoint
- `get_current_season_id(league_id)`: Gets the current season ID for a league

### 2. Backend Route Updates (`sportmonks_routes.py`)

Updated the `/fixtures/all` endpoint to:
- Use the new schedules API endpoint
- Extract fixtures from nested rounds structure
- Transform fixture data to match our expected format
- Support team-specific fixture queries
- Properly handle the new date format and participant structure

### 3. Data Transformation

The new API returns data in a different structure:
```json
{
  "participants": [
    {
      "id": 8,
      "name": "Liverpool",
      "meta": { "location": "home" }
    },
    {
      "id": 52,
      "name": "AFC Bournemouth", 
      "meta": { "location": "away" }
    }
  ]
}
```

We transform this to our expected format with separate `home_team` and `away_team` objects.

## API Endpoints Updated

| Endpoint | Description |
|----------|-------------|
| `/api/sportmonks/fixtures/all` | Now uses season schedules API |
| `/api/sportmonks/fixtures/upcoming` | Still needs update |
| `/api/sportmonks/fixtures/past` | Still needs update |

## Testing

To test with Liverpool's fixtures:
```bash
curl "https://football-prediction-backend-2cvi.onrender.com/api/sportmonks/fixtures/all?league_id=8&team_id=8"
```

## Expected Results

After deployment:
1. Today's fixture (Liverpool vs AFC Bournemouth) will appear
2. All season fixtures will be available
3. Proper categorization into past/today/upcoming

## Next Steps

1. Update `/fixtures/upcoming` and `/fixtures/past` endpoints to use the same approach
2. Add caching for season IDs
3. Implement predictions fetching for today's matches
4. Update frontend to show team selector for team-specific fixtures

## Environment Variables

Ensure these are set in Render:
- `SPORTMONKS_API_KEY` or `SPORTMONKS_PRIMARY_TOKEN`
- API key must have access to schedules endpoint