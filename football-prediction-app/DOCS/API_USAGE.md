# API Usage Guide

This guide provides detailed information about using the Football Prediction API.

## Base URL

- Local: `http://localhost:5000`
- Production: `https://your-backend.onrender.com`

## Authentication

Currently, the API is open. Future versions will require API keys:

```bash
# Future authentication header
X-API-Key: your-api-key
```

## Common Headers

```bash
Content-Type: application/json
Accept: application/json
```

## Response Format

All responses follow this format:

### Success Response
```json
{
  "status": "success",
  "data": {...},
  "message": "Optional success message"
}
```

### Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  },
  "status_code": 400
}
```

### Paginated Response
```json
{
  "data": [...],
  "page": 1,
  "page_size": 20,
  "total": 100,
  "total_pages": 5
}
```

## Endpoints

### Health & Status

#### GET /healthz
Simple health check for monitoring.

```bash
curl http://localhost:5000/healthz
```

Response:
```json
{
  "status": "ok"
}
```

#### GET /api/health
Detailed health check with service status.

```bash
curl http://localhost:5000/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "services": {
    "database": {
      "status": "connected",
      "type": "PostgreSQL"
    },
    "redis": {
      "status": "connected"
    },
    "sportmonks": {
      "status": "configured",
      "has_primary_token": true
    }
  }
}
```

#### GET /api/version
Get application version and feature flags.

```bash
curl http://localhost:5000/api/version
```

Response:
```json
{
  "version": "1.0.0",
  "git_commit": "abc123f",
  "deployment_time": "2025-01-01T12:00:00Z",
  "environment": "production",
  "python_version": "3.11.0",
  "features": {
    "sportmonks": true,
    "rapidapi": true,
    "redis": true,
    "celery": true,
    "scheduler": false
  }
}
```

### Fixtures

#### GET /api/v1/fixtures
Get upcoming or past fixtures with filtering options.

Query Parameters:
- `date_from` (string): Start date in YYYY-MM-DD format
- `date_to` (string): End date in YYYY-MM-DD format
- `league_id` (integer): Filter by league
- `team_id` (integer): Filter by team
- `status` (string): Filter by status (scheduled, finished, in_play)
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20, max: 100)

```bash
# Get fixtures for next 7 days
curl "http://localhost:5000/api/v1/fixtures?date_from=2025-01-01&date_to=2025-01-07"

# Get fixtures for specific team
curl "http://localhost:5000/api/v1/fixtures?team_id=123&page=1&page_size=10"
```

Response:
```json
{
  "data": [
    {
      "id": 12345,
      "home_team": {
        "id": 1,
        "name": "Manchester United",
        "code": "MUN",
        "logo_url": "https://..."
      },
      "away_team": {
        "id": 2,
        "name": "Liverpool",
        "code": "LIV",
        "logo_url": "https://..."
      },
      "match_date": "2025-01-15T15:00:00Z",
      "venue": "Old Trafford",
      "competition": "Premier League",
      "season": "2024/2025",
      "round": "Round 20",
      "status": "scheduled",
      "home_score": null,
      "away_score": null
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 45,
  "total_pages": 3
}
```

### Predictions

#### GET /api/v1/predictions
Get match predictions with ML confidence scores.

Query Parameters:
- `date_from` (string): Start date
- `date_to` (string): End date
- `match_id` (integer): Specific match
- `team_id` (integer): Filter by team
- `min_confidence` (number): Minimum confidence threshold (0-100)
- `page` (integer): Page number
- `page_size` (integer): Items per page

```bash
# Get predictions for date range
curl "http://localhost:5000/api/v1/predictions?date_from=2025-01-01&date_to=2025-01-07"

# Get high-confidence predictions
curl "http://localhost:5000/api/v1/predictions?min_confidence=80"
```

Response:
```json
{
  "data": [
    {
      "id": 1,
      "match_id": 12345,
      "match": {
        "home_team": {...},
        "away_team": {...},
        "match_date": "2025-01-15T15:00:00Z"
      },
      "prediction_type": "unified_engine",
      "predicted_outcome": "Home Win",
      "home_win_probability": 0.65,
      "draw_probability": 0.25,
      "away_win_probability": 0.10,
      "confidence": 85.5,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 15,
  "total_pages": 1
}
```

#### POST /api/v1/predictions/{match_id}
Generate a new prediction for a specific match.

```bash
curl -X POST http://localhost:5000/api/v1/predictions/12345 \
  -H "Content-Type: application/json" \
  -d '{
    "force_refresh": true,
    "engine": "unified"
  }'
```

Response:
```json
{
  "status": "success",
  "data": {
    "prediction": {...},
    "cached": false,
    "generation_time": 2.5
  }
}
```

### Teams

#### GET /api/v1/teams
Get list of teams with search and pagination.

Query Parameters:
- `search` (string): Search by team name
- `league_id` (integer): Filter by league
- `page` (integer): Page number
- `page_size` (integer): Items per page

```bash
# Search for teams
curl "http://localhost:5000/api/v1/teams?search=manchester"

# Get teams by league
curl "http://localhost:5000/api/v1/teams?league_id=39"
```

Response:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Manchester United",
      "code": "MUN",
      "logo_url": "https://...",
      "stadium": "Old Trafford",
      "founded": 1878
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2,
  "total_pages": 1
}
```

#### GET /api/v1/teams/{id}/squad
Get squad information for a specific team.

```bash
curl http://localhost:5000/api/v1/teams/1/squad
```

Response:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Marcus Rashford",
      "position": "Forward",
      "jersey_number": 10,
      "age": 27,
      "nationality": "England",
      "photo_url": "https://..."
    }
  ]
}
```

### Matches

#### GET /api/v1/matches/{id}
Get detailed information about a specific match.

```bash
curl http://localhost:5000/api/v1/matches/12345
```

Response:
```json
{
  "status": "success",
  "data": {
    "id": 12345,
    "home_team": {...},
    "away_team": {...},
    "match_date": "2025-01-15T15:00:00Z",
    "venue": "Old Trafford",
    "competition": "Premier League",
    "season": "2024/2025",
    "round": "Round 20",
    "status": "finished",
    "home_score": 2,
    "away_score": 1,
    "home_score_halftime": 1,
    "away_score_halftime": 0,
    "referee": "Michael Oliver",
    "attendance": 74879
  }
}
```

### Odds (if RapidAPI configured)

#### GET /api/v1/odds/match/{match_id}
Get betting odds for a specific match.

```bash
curl http://localhost:5000/api/v1/odds/match/12345
```

Response:
```json
{
  "status": "success",
  "data": {
    "match_id": 12345,
    "bookmakers": [
      {
        "name": "Bet365",
        "odds": {
          "home_win": 2.10,
          "draw": 3.40,
          "away_win": 3.50
        }
      }
    ],
    "last_updated": "2025-01-01T12:00:00Z"
  }
}
```

## Filtering & Pagination

### Date Filtering
Dates should be in ISO format (YYYY-MM-DD):
```bash
?date_from=2025-01-01&date_to=2025-01-31
```

### Pagination
All list endpoints support pagination:
```bash
?page=2&page_size=50
```

Maximum page_size is 100.

### Sorting
Some endpoints support sorting:
```bash
?sort=date&order=desc
```

## Error Handling

### Common Error Codes

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid API key |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - External API down |

### Error Response Example
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "field": "date_from",
    "hint": "Date should be in YYYY-MM-DD format"
  },
  "status_code": 422
}
```

## Rate Limiting

API rate limits (when enabled):
- 200 requests per hour per IP
- 50 requests per minute per IP

Rate limit headers:
```
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 150
X-RateLimit-Reset: 1640995200
```

## Best Practices

1. **Use Caching**
   - Predictions are cached for 30 minutes
   - Team/player data cached for 24 hours
   - Use ETags when available

2. **Batch Requests**
   - Use date ranges instead of individual dates
   - Request full page sizes when possible

3. **Handle Errors Gracefully**
   - Implement exponential backoff for retries
   - Respect rate limit headers

4. **Optimize Queries**
   - Only request fields you need
   - Use appropriate page sizes
   - Filter by date ranges when possible

## Code Examples

### Python
```python
import requests

BASE_URL = "http://localhost:5000"

# Get fixtures
response = requests.get(
    f"{BASE_URL}/api/v1/fixtures",
    params={
        "date_from": "2025-01-01",
        "date_to": "2025-01-07",
        "page_size": 50
    }
)
fixtures = response.json()

# Get predictions
response = requests.get(
    f"{BASE_URL}/api/v1/predictions",
    params={"min_confidence": 80}
)
predictions = response.json()
```

### JavaScript/TypeScript
```typescript
const BASE_URL = "http://localhost:5000";

// Get fixtures
async function getFixtures(dateFrom: string, dateTo: string) {
  const params = new URLSearchParams({
    date_from: dateFrom,
    date_to: dateTo,
    page_size: "50"
  });
  
  const response = await fetch(`${BASE_URL}/api/v1/fixtures?${params}`);
  return response.json();
}

// Get predictions
async function getPredictions(minConfidence: number) {
  const response = await fetch(
    `${BASE_URL}/api/v1/predictions?min_confidence=${minConfidence}`
  );
  return response.json();
}
```

### cURL
```bash
# Get fixtures with auth (future)
curl -H "X-API-Key: your-api-key" \
     "http://localhost:5000/api/v1/fixtures?date_from=2025-01-01"

# Post prediction request
curl -X POST http://localhost:5000/api/v1/predictions/12345 \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{"force_refresh": true}'
```

## Webhooks (Future)

Future versions will support webhooks for:
- Match status changes
- New predictions available
- Odds updates

## Support

For API issues:
1. Check the health endpoint
2. Review error messages
3. Check API documentation
4. Contact support with request ID