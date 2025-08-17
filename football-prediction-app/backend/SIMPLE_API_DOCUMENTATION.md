# Simple Football Prediction API Documentation

## Overview

This is a simplified and improved implementation of the football prediction API using SportMonks v3 API with proper field selection based on the official documentation.

## Key Features

- ✅ **Proper Field Selection**: Uses semicolon-separated includes as per SportMonks documentation
- ✅ **Simple Prediction Engine**: Analyzes team form, head-to-head records, and other factors
- ✅ **Clean API Routes**: Easy-to-use endpoints for fixtures and predictions
- ✅ **Comprehensive Data**: Includes scores, participants, statistics, events, and lineups
- ✅ **Error Handling**: Graceful error handling with meaningful messages

## Setup

### 1. Environment Variables

Set your SportMonks API key:

```bash
export SPORTMONKS_API_KEY="your_api_key_here"
# OR
export SPORTMONKS_PRIMARY_TOKEN="your_api_key_here"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Tests

```bash
cd /workspace/football-prediction-app/backend
python test_simple_api.py
```

## API Endpoints

All endpoints are prefixed with `/api/v2`

### Health Check

```
GET /api/v2/health
```

Response:
```json
{
  "status": "healthy",
  "api_configured": true,
  "timestamp": "2024-01-10T12:00:00"
}
```

### Today's Fixtures

Get all fixtures scheduled for today with predictions.

```
GET /api/v2/fixtures/today
```

Response:
```json
{
  "fixtures": [
    {
      "id": 18535517,
      "name": "Manchester United vs Liverpool",
      "date": "2024-01-10 15:00:00",
      "status": "Not Started",
      "venue": {
        "name": "Old Trafford",
        "city": "Manchester"
      },
      "home_team": {
        "id": 1,
        "name": "Manchester United",
        "logo": "https://..."
      },
      "away_team": {
        "id": 2,
        "name": "Liverpool",
        "logo": "https://..."
      },
      "prediction": {
        "home_win": 35.5,
        "draw": 28.2,
        "away_win": 36.3,
        "predicted_outcome": "away",
        "predicted_score": "1-2",
        "confidence": 0.36,
        "reasoning": [
          "Away team in better form (2.33 vs 1.67 points per match)",
          "Home advantage considered"
        ]
      }
    }
  ],
  "count": 1,
  "date": "2024-01-10"
}
```

### Upcoming Fixtures

Get upcoming fixtures with optional predictions.

```
GET /api/v2/fixtures/upcoming?days=7&predictions=true
```

Parameters:
- `days` (optional): Number of days ahead (default: 7)
- `predictions` (optional): Include predictions (default: true)

### Past Fixtures

Get past fixtures with results.

```
GET /api/v2/fixtures/past?days=7
```

Parameters:
- `days` (optional): Number of days back (default: 7)

### Fixture Details

Get detailed information about a specific fixture.

```
GET /api/v2/fixtures/{fixture_id}
```

Response includes:
- Basic fixture information
- Teams and venue details
- Scores (if available)
- Statistics
- Events (goals, cards, etc.)
- Lineups
- Prediction (if not finished)

### Fixture Prediction

Get prediction for a specific fixture.

```
GET /api/v2/fixtures/{fixture_id}/prediction
```

Response:
```json
{
  "fixture_id": 18535517,
  "probabilities": {
    "home_win": 45.2,
    "draw": 25.3,
    "away_win": 29.5
  },
  "predicted_outcome": "home",
  "predicted_score": {
    "home": 2,
    "away": 1,
    "display": "2-1"
  },
  "confidence": 0.45,
  "reasoning": [
    "Home team in better form (2.00 vs 1.33 points per match)",
    "Home team dominates H2H (4 wins in 6 matches)",
    "Home advantage considered"
  ]
}
```

### Team Fixtures

Get all fixtures for a specific team.

```
GET /api/v2/teams/{team_id}/fixtures?days_back=30&days_forward=30
```

Parameters:
- `days_back` (optional): Days to look back (default: 30)
- `days_forward` (optional): Days to look forward (default: 30)

Response groups fixtures into:
- `past_fixtures`: Completed matches
- `live_fixtures`: Currently playing
- `upcoming_fixtures`: Future matches

### Head-to-Head

Get head-to-head record between two teams.

```
GET /api/v2/head-to-head/{team1_id}/{team2_id}
```

Response:
```json
{
  "team1_id": 1,
  "team2_id": 2,
  "statistics": {
    "total_matches": 20,
    "team1_wins": 8,
    "team2_wins": 7,
    "draws": 5,
    "team1_win_percentage": 40.0,
    "team2_win_percentage": 35.0,
    "draw_percentage": 25.0,
    "average_goals_per_match": 2.85
  },
  "fixtures": [
    // List of H2H fixtures
  ]
}
```

## Prediction Algorithm

The prediction engine considers multiple factors:

### 1. Team Form (40% weight)
- Last 10 matches performance
- Points per match
- Win/draw/loss record

### 2. Goals Analysis (20% weight)
- Goals scored per match
- Goals conceded per match
- Attacking vs defensive strength

### 3. Head-to-Head Record (20% weight)
- Historical performance between teams
- Win percentages in H2H matches

### 4. Home Advantage (20% weight)
- Standard home team advantage applied

### Confidence Score
The confidence score (0-1) indicates how certain the prediction is based on the probability distribution.

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `404`: Resource not found
- `500`: Server error
- `503`: Service unavailable (API not configured)

Error responses include:
```json
{
  "error": "Error message",
  "details": "Additional information"
}
```

## Example Usage

### Python Example

```python
import requests

# Base URL
base_url = "http://localhost:5000/api/v2"

# Get today's fixtures with predictions
response = requests.get(f"{base_url}/fixtures/today")
data = response.json()

for fixture in data['fixtures']:
    print(f"{fixture['name']}")
    if 'prediction' in fixture:
        pred = fixture['prediction']
        print(f"  Prediction: {pred['predicted_outcome']} ({pred['confidence']*100:.0f}% confidence)")
        print(f"  Score: {pred['predicted_score']}")

# Get specific fixture prediction
fixture_id = 18535517
response = requests.get(f"{base_url}/fixtures/{fixture_id}/prediction")
prediction = response.json()

print(f"Home Win: {prediction['probabilities']['home_win']}%")
print(f"Draw: {prediction['probabilities']['draw']}%")
print(f"Away Win: {prediction['probabilities']['away_win']}%")
```

### JavaScript Example

```javascript
// Get upcoming fixtures
fetch('/api/v2/fixtures/upcoming?days=3')
  .then(response => response.json())
  .then(data => {
    data.fixtures.forEach(fixture => {
      console.log(`${fixture.name} - ${fixture.date}`);
      if (fixture.prediction) {
        console.log(`  Predicted: ${fixture.prediction.predicted_score}`);
      }
    });
  });

// Get head-to-head
fetch('/api/v2/head-to-head/1/2')
  .then(response => response.json())
  .then(data => {
    console.log(`Total matches: ${data.statistics.total_matches}`);
    console.log(`Team 1 wins: ${data.statistics.team1_win_percentage}%`);
    console.log(`Team 2 wins: ${data.statistics.team2_win_percentage}%`);
  });
```

## Rate Limiting

The SportMonks API has rate limits based on your subscription plan. The client includes automatic retry logic with exponential backoff for rate-limited requests.

## Caching

Responses are cached in Redis (if available) with appropriate TTLs:
- Live scores: 30 seconds
- Fixture details: 5 minutes
- Team/League data: 1 hour

## Testing

Run the test suite to verify everything is working:

```bash
python test_simple_api.py
```

This will test:
1. API client connectivity
2. Prediction engine functionality
3. Flask routes availability

## Troubleshooting

### No API Key
If you see "API not configured" errors, ensure you've set the `SPORTMONKS_API_KEY` environment variable.

### No Fixtures Found
This might be normal if there are no fixtures scheduled. Try different date ranges or check if your subscription includes the leagues you're looking for.

### Prediction Errors
Predictions require sufficient historical data. New teams or leagues might not have enough data for accurate predictions.

## Future Improvements

- [ ] Add more sophisticated prediction models
- [ ] Include player injuries and suspensions
- [ ] Add weather conditions impact
- [ ] Include betting odds analysis
- [ ] Add team news and sentiment analysis