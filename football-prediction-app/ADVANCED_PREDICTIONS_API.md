# Advanced Predictions API Documentation

## Overview
The Advanced Predictions API provides AI-powered football match predictions by aggregating data from multiple sources including team form, head-to-head history, injuries, league standings, and more. It uses weighted factors to generate highly accurate predictions with confidence scores.

## Base URL
```
https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions/advanced
```

## Endpoints

### 1. Get Advanced Predictions
Get AI-powered predictions for multiple fixtures with comprehensive analysis.

**Endpoint:** `GET /api/v1/predictions/advanced`

**Query Parameters:**
- `date_from` (string, optional): Start date in YYYY-MM-DD format. Default: today
- `date_to` (string, optional): End date in YYYY-MM-DD format. Default: 7 days from today
- `league_id` (integer, optional): Filter by specific league ID
- `team_id` (integer, optional): Filter by specific team ID
- `min_confidence` (float, optional): Minimum confidence score (0-100). Default: 0
- `include_live` (boolean, optional): Include live matches. Default: false
- `page` (integer, optional): Page number for pagination. Default: 1
- `per_page` (integer, optional): Results per page (max 50). Default: 10

**Example Request:**
```bash
curl "https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions/advanced?date_from=2025-08-15&date_to=2025-08-22&league_id=8&min_confidence=60"
```

**Example Response:**
```json
{
  "predictions": [
    {
      "fixture_id": 19427455,
      "fixture": {
        "home_team": "Liverpool",
        "away_team": "AFC Bournemouth",
        "date": "2025-08-15T19:00:00",
        "league": "Premier League",
        "venue": "Anfield"
      },
      "probabilities": {
        "home_win": 72.5,
        "draw": 18.2,
        "away_win": 9.3
      },
      "goals": {
        "predicted_home": 2.4,
        "predicted_away": 0.8,
        "total_expected": 3.2
      },
      "markets": {
        "btts": {
          "yes": 48.5,
          "no": 51.5
        },
        "over_under": {
          "over_25": 68.3,
          "under_25": 31.7,
          "over_35": 42.1,
          "under_35": 57.9
        }
      },
      "confidence_score": 85.7,
      "prediction_summary": "Liverpool are favorites to win with high confidence. Liverpool are in significantly better form. Liverpool have dominated recent meetings.",
      "value_bets": [
        {
          "type": "Match Result",
          "selection": "Home Win",
          "probability": 72.5,
          "confidence": "high"
        },
        {
          "type": "Total Goals",
          "selection": "Over 2.5",
          "probability": 68.3,
          "confidence": "high"
        }
      ],
      "factors_breakdown": {
        "form": {
          "home": 0.8,
          "away": 0.4,
          "weight": 0.4
        },
        "h2h": {
          "home": 0.7,
          "away": 0.3,
          "weight": 0.2
        },
        "injuries": {
          "home": 0.9,
          "away": 0.7,
          "weight": 0.15
        },
        "home_advantage": {
          "home": 0.6,
          "away": 0.4,
          "weight": 0.1
        },
        "motivation": {
          "home": 0.85,
          "away": 0.6,
          "weight": 0.1
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "total_pages": 3
  },
  "filters": {
    "date_from": "2025-08-15",
    "date_to": "2025-08-22",
    "league_id": 8,
    "team_id": null,
    "min_confidence": 60,
    "include_live": false
  },
  "timestamp": "2025-08-15T10:30:00Z"
}
```

### 2. Get Single Fixture Prediction
Get detailed advanced prediction for a specific fixture.

**Endpoint:** `GET /api/v1/predictions/advanced/fixture/{fixture_id}`

**Path Parameters:**
- `fixture_id` (integer, required): The fixture ID to get prediction for

**Example Request:**
```bash
curl "https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions/advanced/fixture/19427455"
```

**Example Response:**
```json
{
  "fixture_id": 19427455,
  "fixture": {
    "home_team": "Liverpool",
    "away_team": "AFC Bournemouth",
    "date": "2025-08-15T19:00:00"
  },
  "probabilities": {
    "match_result": {
      "home_win": 72.5,
      "draw": 18.2,
      "away_win": 9.3
    },
    "double_chance": {
      "home_or_draw": 90.7,
      "away_or_draw": 27.5,
      "home_or_away": 81.8
    }
  },
  "goals": {
    "predicted": {
      "home": 2.4,
      "away": 0.8,
      "total": 3.2
    },
    "markets": {
      "over_05": 97.2,
      "over_15": 84.5,
      "over_25": 68.3,
      "over_35": 42.1,
      "under_25": 31.7,
      "under_35": 57.9
    }
  },
  "btts": {
    "yes": 48.5,
    "no": 51.5
  },
  "confidence_score": 85.7,
  "prediction_summary": "Liverpool are favorites to win with high confidence. Liverpool are in significantly better form. Liverpool have dominated recent meetings.",
  "value_bets": [
    {
      "type": "Match Result",
      "selection": "Home Win",
      "probability": 72.5,
      "confidence": "high"
    }
  ],
  "data_sources": {
    "form": {
      "home": {
        "last_5_results": ["W", "W", "D", "W", "W"],
        "goals_scored": 12,
        "goals_conceded": 3,
        "form_rating": 8.7
      },
      "away": {
        "last_5_results": ["L", "D", "L", "W", "L"],
        "goals_scored": 5,
        "goals_conceded": 11,
        "form_rating": 3.3
      }
    },
    "head_to_head": {
      "total_matches": 8,
      "home_wins": 6,
      "away_wins": 1,
      "draws": 1,
      "recent_meetings": [
        {
          "date": "2024-01-21",
          "home_team": "Liverpool",
          "away_team": "AFC Bournemouth",
          "score": "4-0",
          "venue": "Anfield"
        }
      ]
    },
    "injuries": {
      "home": {
        "total_injuries": 2,
        "key_players_out": [],
        "impact_rating": 1.5
      },
      "away": {
        "total_injuries": 4,
        "key_players_out": [
          {
            "name": "Player Name",
            "position": "Forward",
            "injury_type": "Hamstring"
          }
        ],
        "impact_rating": 4.5
      }
    }
  },
  "timestamp": "2025-08-15T10:30:00Z"
}
```

### 3. Batch Predictions
Get predictions for multiple specific fixtures at once.

**Endpoint:** `POST /api/v1/predictions/advanced/batch`

**Request Body:**
```json
{
  "fixture_ids": [19427455, 19427456, 19427457],
  "include_details": false
}
```

**Example Response:**
```json
{
  "predictions": [
    {
      "fixture_id": 19427455,
      "home_team": "Liverpool",
      "away_team": "AFC Bournemouth",
      "prediction": {
        "result": "home",
        "confidence": 85.7
      },
      "recommended_bet": {
        "type": "Match Result",
        "selection": "Home Win",
        "probability": 72.5,
        "confidence": "high"
      }
    }
  ],
  "errors": [],
  "requested": 3,
  "successful": 3,
  "failed": 0
}
```

### 4. Value Bets
Get fixtures with high-value betting opportunities.

**Endpoint:** `GET /api/v1/predictions/advanced/value-bets`

**Query Parameters:**
- `date_from` (string, optional): Start date. Default: today
- `date_to` (string, optional): End date. Default: 3 days from today
- `min_probability` (float, optional): Minimum probability for value bets. Default: 65
- `bet_types` (string, optional): Comma-separated bet types to include

**Example Request:**
```bash
curl "https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions/advanced/value-bets?min_probability=70&bet_types=Match%20Result,Total%20Goals"
```

**Example Response:**
```json
{
  "value_bets": [
    {
      "fixture_id": 19427455,
      "fixture": {
        "home_team": "Liverpool",
        "away_team": "AFC Bournemouth",
        "date": "2025-08-15T19:00:00",
        "league": "Premier League"
      },
      "bet": {
        "type": "Match Result",
        "selection": "Home Win",
        "probability": 72.5,
        "confidence": "high"
      },
      "confidence_score": 85.7
    }
  ],
  "filters": {
    "date_from": "2025-08-15",
    "date_to": "2025-08-18",
    "min_probability": 70,
    "bet_types": ["Match Result", "Total Goals"]
  },
  "timestamp": "2025-08-15T10:30:00Z"
}
```

### 5. Health Check
Check the status of the advanced predictions service.

**Endpoint:** `GET /api/v1/predictions/advanced/health`

**Example Response:**
```json
{
  "status": "healthy",
  "service": "advanced_predictions",
  "version": "2.0",
  "api_status": "healthy",
  "cache_enabled": true,
  "features": [
    "multi-source-aggregation",
    "weighted-predictions",
    "value-bet-identification",
    "batch-processing",
    "real-time-updates"
  ],
  "timestamp": "2025-08-15T10:30:00Z"
}
```

## Prediction Factors

The AI prediction engine uses the following weighted factors:

1. **Recent Form (40%)**
   - Last 5 match results
   - Goals scored and conceded
   - Home/away specific performance
   - Clean sheets and BTTS frequency

2. **Head-to-Head History (20%)**
   - Historical match results between teams
   - Average goals in H2H meetings
   - Recent trends in matchups

3. **Injuries & Suspensions (15%)**
   - Key player absences
   - Impact on team strength
   - Goalkeeper and defender availability

4. **Home/Away Advantage (10%)**
   - Historical home performance
   - Travel and venue factors

5. **League Standing & Motivation (10%)**
   - Title race involvement
   - Relegation battle
   - European qualification race
   - End-of-season dynamics

6. **Other Factors (5%)**
   - Weather conditions
   - Recent manager changes
   - Fixture congestion

## Confidence Scores

Predictions include confidence scores (0-100) based on:
- Data availability and quality
- Historical accuracy for similar fixtures
- Consistency across different prediction factors
- Recent form reliability

Higher confidence scores indicate more reliable predictions.

## Rate Limiting

- Default rate limit: 1000 requests per hour
- Batch endpoints count as single requests
- Cached responses don't count against rate limits

## Error Responses

All endpoints may return these error responses:

**400 Bad Request**
```json
{
  "error": "Invalid parameters",
  "message": "date_from must be in YYYY-MM-DD format"
}
```

**404 Not Found**
```json
{
  "error": "Fixture not found",
  "message": "No fixture found with ID: 12345"
}
```

**500 Internal Server Error**
```json
{
  "error": "Service error",
  "message": "Failed to generate predictions"
}
```

## Best Practices

1. **Use Caching**: Results are cached for 10-30 minutes. Repeated requests return cached data.

2. **Batch Requests**: Use the batch endpoint for multiple fixtures to reduce API calls.

3. **Filter by Confidence**: Focus on predictions with confidence scores above 70% for best results.

4. **Date Ranges**: Keep date ranges reasonable (7-14 days) for optimal performance.

5. **Value Bets**: Use the value-bets endpoint to find the best betting opportunities.

## Examples

### Get EPL predictions for the weekend
```bash
curl "https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions/advanced?date_from=2025-08-16&date_to=2025-08-18&league_id=8&min_confidence=60"
```

### Get predictions for a specific team
```bash
curl "https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions/advanced?team_id=8&date_from=2025-08-15&date_to=2025-08-31"
```

### Find high-confidence value bets
```bash
curl "https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions/advanced/value-bets?min_probability=75&bet_types=Match%20Result"
```