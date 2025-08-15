# Main Page Predictions API Documentation

## Overview

The Main Page Predictions API provides comprehensive, AI-powered football match predictions by aggregating data from multiple sources including team form, head-to-head history, injuries, standings, and live context.

## Base URL

```
https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions
```

## Endpoints

### 1. Get Comprehensive Prediction for Single Fixture

**Endpoint:** `GET /comprehensive/{fixture_id}`

**Description:** Get detailed AI-powered prediction for a specific fixture with full data aggregation.

**Parameters:**
- `fixture_id` (integer, required): The ID of the fixture

**Response Example:**
```json
{
  "fixture_id": 19427455,
  "home_team": "Liverpool",
  "away_team": "AFC Bournemouth",
  "date": "2025-08-15T19:00:00",
  "win_probability_home": 72.5,
  "win_probability_away": 18.3,
  "draw_probability": 9.2,
  "btts_probability": 58.4,
  "over_25_probability": 67.8,
  "under_25_probability": 32.2,
  "over_35_probability": 45.2,
  "correct_score_predictions": [
    {"score": "2-0", "probability": 12.5},
    {"score": "2-1", "probability": 10.8},
    {"score": "3-0", "probability": 9.2},
    {"score": "1-0", "probability": 8.7},
    {"score": "3-1", "probability": 7.3}
  ],
  "confidence_level": "high",
  "confidence_score": 85.2,
  "prediction_summary": "Liverpool are strong favorites with 72.5% win probability. Liverpool are in excellent form (W5). Expect an entertaining match with over 2.5 goals likely. High confidence prediction based on 89% data availability.",
  "factors_breakdown": {
    "recent_form": {
      "home_advantage": 25,
      "away_advantage": 0,
      "draw_tendency": 5,
      "btts_likelihood": 58.4,
      "over_25_likelihood": 67.8,
      "over_35_likelihood": 45.2
    },
    "head_to_head": {
      "home_historical_advantage": 15.5,
      "away_historical_advantage": -8.2,
      "draw_historical_tendency": -7.3
    },
    "injuries": {
      "home_impact": 8,
      "away_impact": -3
    },
    "home_away": {
      "home_boost": 20,
      "away_penalty": -5
    },
    "motivation": {
      "home_motivation_boost": 5,
      "away_motivation_boost": 0
    }
  },
  "data_completeness": 88.9,
  "value_bets": [
    {
      "type": "Home Win",
      "probability": 72.5,
      "confidence": "high",
      "recommended_stake": 2.5
    },
    {
      "type": "Over 2.5 Goals",
      "probability": 67.8,
      "confidence": "high",
      "recommended_stake": 2.0
    }
  ]
}
```

### 2. Get Batch Predictions

**Endpoint:** `GET /`

**Description:** Get predictions for multiple fixtures with filtering and pagination.

**Query Parameters:**
- `date_from` (string, optional): Start date in YYYY-MM-DD format
- `date_to` (string, optional): End date in YYYY-MM-DD format
- `league_id` (integer, optional): Filter by league ID
- `team_id` (integer, optional): Filter by team ID
- `page` (integer, optional, default: 1): Page number
- `per_page` (integer, optional, default: 10): Results per page

**Response Example:**
```json
{
  "predictions": [
    {
      "fixture_id": 19427455,
      "home_team": "Liverpool",
      "away_team": "AFC Bournemouth",
      "date": "2025-08-15T19:00:00",
      "win_probability_home": 72.5,
      "win_probability_away": 18.3,
      "draw_probability": 9.2,
      "btts_probability": 58.4,
      "over_25_probability": 67.8,
      "under_25_probability": 32.2,
      "over_35_probability": 45.2,
      "confidence_level": "high",
      "confidence_score": 85.2,
      "prediction_summary": "Liverpool are strong favorites...",
      "data_completeness": 88.9,
      "value_bets": [
        {
          "type": "Home Win",
          "probability": 72.5,
          "confidence": "high",
          "recommended_stake": 2.5
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 45,
    "pages": 5
  },
  "date_range": {
    "from": "2025-08-15",
    "to": "2025-08-22"
  },
  "filters": {
    "league_id": 8,
    "team_id": null
  }
}
```

### 3. Get Today's Predictions

**Endpoint:** `GET /today`

**Description:** Get predictions for today's fixtures, optimized for main page display.

**Query Parameters:**
- `league_id` (integer, optional): Filter by league ID
- `limit` (integer, optional, default: 20): Maximum number of predictions

**Response Example:**
```json
{
  "date": "2025-08-15",
  "predictions": [
    {
      "fixture_id": 19427455,
      "home_team": "Liverpool",
      "away_team": "AFC Bournemouth",
      "date": "2025-08-15T19:00:00",
      "main_prediction": "Liverpool",
      "main_probability": 72.5,
      "win_probability_home": 72.5,
      "win_probability_away": 18.3,
      "draw_probability": 9.2,
      "btts_probability": 58.4,
      "over_25_probability": 67.8,
      "confidence_level": "high",
      "prediction_summary": "Liverpool are strong favorites...",
      "top_value_bet": {
        "type": "Home Win",
        "probability": 72.5,
        "confidence": "high",
        "recommended_stake": 2.5
      }
    }
  ],
  "total": 8
}
```

### 4. Get Featured Predictions

**Endpoint:** `GET /featured`

**Description:** Get featured high-confidence predictions for the next few days.

**Query Parameters:**
- `days` (integer, optional, default: 3): Number of days ahead
- `min_confidence` (number, optional, default: 70): Minimum confidence score

**Response Example:**
```json
{
  "featured_predictions": [
    {
      "fixture_id": 19427455,
      "home_team": "Liverpool",
      "away_team": "AFC Bournemouth",
      "date": "2025-08-15T19:00:00",
      "prediction_type": "Home Win",
      "predicted_team": "Liverpool",
      "probability": 72.5,
      "confidence_score": 85.2,
      "confidence_level": "high",
      "prediction_summary": "Liverpool are strong favorites...",
      "value_bets": [
        {
          "type": "Home Win",
          "probability": 72.5,
          "confidence": "high",
          "recommended_stake": 2.5
        },
        {
          "type": "Over 2.5 Goals",
          "probability": 67.8,
          "confidence": "high",
          "recommended_stake": 2.0
        }
      ],
      "data_completeness": 88.9
    }
  ],
  "date_range": {
    "from": "2025-08-15",
    "to": "2025-08-18"
  },
  "min_confidence_filter": 70
}
```

### 5. Get Prediction Statistics

**Endpoint:** `GET /stats`

**Description:** Get historical accuracy and performance statistics.

**Query Parameters:**
- `days` (integer, optional, default: 30): Number of days to look back

**Response Example:**
```json
{
  "stats": {
    "total_predictions": 1250,
    "accuracy": {
      "overall": 72.5,
      "home_wins": 75.3,
      "away_wins": 68.9,
      "draws": 71.2,
      "over_25": 74.8,
      "btts": 73.1
    },
    "confidence_levels": {
      "high": {"count": 380, "accuracy": 85.2},
      "medium": {"count": 620, "accuracy": 71.8},
      "low": {"count": 250, "accuracy": 58.4}
    },
    "roi": {
      "overall": 8.5,
      "value_bets": 12.3,
      "high_confidence": 15.7
    },
    "period": {
      "days": 30,
      "from": "2025-07-16",
      "to": "2025-08-15"
    }
  }
}
```

### 6. Health Check

**Endpoint:** `GET /health`

**Description:** Check the health status of the prediction service.

**Response Example:**
```json
{
  "status": "healthy",
  "service": "main_page_predictions",
  "timestamp": "2025-08-15T10:30:00.000Z",
  "dependencies": {
    "sportmonks_api": "healthy",
    "redis": "connected",
    "prediction_engine": "active"
  }
}
```

## Data Sources

The prediction engine aggregates data from the following sources:

1. **Team Form (40% weight)**
   - Last 10 matches results
   - Home/away specific form
   - Goals scored/conceded
   - Clean sheets and BTTS statistics
   - Current winning/losing streaks

2. **Head-to-Head History (20% weight)**
   - Last 5-10 meetings between teams
   - Historical win/draw/loss percentages
   - Average goals in H2H matches
   - Recent trends in last 3-5 meetings

3. **Injuries & Suspensions (15% weight)**
   - Key players missing
   - Impact on team strength
   - Position-specific absences (GK, defenders, strikers)

4. **Home/Away Advantage (10% weight)**
   - Base home advantage
   - Team-specific home/away performance

5. **Motivation & League Standing (10% weight)**
   - Title race involvement
   - Relegation battle
   - European qualification race
   - Recent manager changes

6. **Other Context (5% weight)**
   - Match day context
   - Simultaneous fixtures affecting motivation
   - Days since last match

## Confidence Levels

- **High**: 70%+ main prediction probability and 80%+ data completeness
- **Medium**: 50-70% main prediction probability and 60%+ data completeness  
- **Low**: Below 50% main prediction probability or limited data

## Value Bet Recommendations

The system identifies value bets based on:
- Probability threshold (usually 55%+ for wins, 70%+ for goals markets)
- Confidence level (medium or high)
- Conservative Kelly Criterion for stake recommendations (0.5-3 units)

## Rate Limiting

- 1000 requests per hour per API key
- Cached responses for 5-30 minutes depending on endpoint

## Error Responses

```json
{
  "error": "Service temporarily unavailable",
  "message": "Unable to fetch predictions from SportMonks API",
  "details": "Connection timeout",
  "predictions": []
}
```

HTTP Status Codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 404: Fixture not found
- 503: Service unavailable