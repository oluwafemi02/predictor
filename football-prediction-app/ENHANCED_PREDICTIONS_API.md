# Enhanced Predictions API Documentation

## Overview

The Enhanced Predictions API provides AI-powered football match predictions by aggregating multiple data sources and applying weighted algorithms to generate accurate predictions.

## Base URL

```
https://football-prediction-backend-2cvi.onrender.com/api/v1/predictions
```

## Endpoints

### 1. Get Enhanced Predictions

Get comprehensive predictions for upcoming fixtures with detailed analysis.

**Endpoint:** `GET /enhanced`

**Query Parameters:**
- `date_from` (optional): Start date in YYYY-MM-DD format (default: today)
- `date_to` (optional): End date in YYYY-MM-DD format (default: today + 7 days)
- `league_id` (optional): Filter by league ID (e.g., 8 for Premier League)
- `team_id` (optional): Filter by team ID
- `min_confidence` (optional): Minimum confidence level - "low", "medium", or "high" (default: "low")

**Example Request:**
```
GET /api/v1/predictions/enhanced?date_from=2025-08-15&date_to=2025-08-22&league_id=8&min_confidence=medium
```

**Example Response:**
```json
{
  "predictions": [
    {
      "fixture_id": 19427455,
      "home_team": "Liverpool",
      "away_team": "AFC Bournemouth",
      "date": "2025-08-15 19:00:00",
      "win_probability_home": 68.5,
      "win_probability_away": 18.3,
      "draw_probability": 13.2,
      "confidence_level": "high",
      "prediction_factors": {
        "form_impact": 3.2,
        "h2h_pattern": "H5-D2-A1",
        "injury_impact": -1.5,
        "motivation": "H:european_spots, A:mid_table"
      },
      "prediction_summary": "Liverpool is predicted to win with 68.5% probability. Liverpool is in significantly better form. Recent form: Liverpool (WWL) vs AFC Bournemouth (LDL). Liverpool has dominated recent H2H meetings (5 wins in 8 games).",
      "recommended_bets": [
        {
          "type": "Match Result",
          "selection": "Home Win",
          "probability": 68.5,
          "confidence": "high",
          "reasoning": "Strong home advantage and form"
        },
        {
          "type": "Double Chance",
          "selection": "Home or Draw",
          "probability": 81.7,
          "confidence": "high",
          "reasoning": "Low risk option with high probability"
        }
      ],
      "expected_goals": {
        "home": 2.4,
        "away": 0.8
      },
      "btts_probability": 42.3,
      "over_25_probability": 65.8,
      "league": "Premier League"
    }
  ],
  "count": 15,
  "date_range": {
    "from": "2025-08-15",
    "to": "2025-08-22"
  },
  "filters": {
    "league_id": 8,
    "team_id": null,
    "min_confidence": "medium"
  },
  "generated_at": "2025-08-15T10:30:00Z"
}
```

### 2. Get Single Fixture Prediction

Get enhanced prediction for a specific fixture.

**Endpoint:** `GET /enhanced/{fixture_id}`

**Path Parameters:**
- `fixture_id`: The SportMonks fixture ID

**Example Request:**
```
GET /api/v1/predictions/enhanced/19427455
```

**Example Response:**
```json
{
  "fixture_id": 19427455,
  "home_team": "Liverpool",
  "away_team": "AFC Bournemouth",
  "date": "2025-08-15 19:00:00",
  "win_probability_home": 68.5,
  "win_probability_away": 18.3,
  "draw_probability": 13.2,
  "confidence_level": "high",
  "prediction_factors": {
    "form_impact": 3.2,
    "h2h_pattern": "H5-D2-A1",
    "injury_impact": -1.5,
    "motivation": "H:european_spots, A:mid_table"
  },
  "prediction_summary": "Liverpool is predicted to win with 68.5% probability...",
  "recommended_bets": [...],
  "expected_goals": {
    "home": 2.4,
    "away": 0.8
  },
  "btts_probability": 42.3,
  "over_25_probability": 65.8,
  "generated_at": "2025-08-15T10:30:00Z"
}
```

### 3. Get Value Bets

Get high-confidence predictions suitable for value betting.

**Endpoint:** `GET /value-bets`

**Query Parameters:**
- `date_from` (optional): Start date in YYYY-MM-DD format (default: today)
- `date_to` (optional): End date in YYYY-MM-DD format (default: today + 3 days)
- `min_probability` (optional): Minimum probability threshold (default: 60)
- `league_id` (optional): Filter by league ID

**Example Request:**
```
GET /api/v1/predictions/value-bets?min_probability=65&league_id=8
```

**Example Response:**
```json
{
  "value_bets": [
    {
      "fixture_id": 19427455,
      "home_team": "Liverpool",
      "away_team": "AFC Bournemouth",
      "date": "2025-08-15 19:00:00",
      "bet_type": "Home Win",
      "team": "Liverpool",
      "probability": 68.5,
      "confidence_level": "high",
      "expected_goals": {
        "home": 2.4,
        "away": 0.8
      },
      "summary": "Liverpool is predicted to win with 68.5% probability...",
      "league": "Premier League"
    },
    {
      "fixture_id": 19427456,
      "home_team": "Manchester City",
      "away_team": "Chelsea",
      "date": "2025-08-16 15:00:00",
      "bet_type": "Over 2.5 Goals",
      "probability": 72.3,
      "confidence_level": "high",
      "expected_goals": {
        "home": 2.1,
        "away": 1.4
      },
      "league": "Premier League"
    }
  ],
  "count": 8,
  "filters": {
    "date_from": "2025-08-15",
    "date_to": "2025-08-18",
    "min_probability": 65,
    "league_id": 8
  },
  "generated_at": "2025-08-15T10:30:00Z"
}
```

### 4. Health Check

Check the status of the enhanced predictions service.

**Endpoint:** `GET /health`

**Example Response:**
```json
{
  "status": "healthy",
  "api_status": "healthy",
  "cache_status": "healthy",
  "timestamp": "2025-08-15T10:30:00Z"
}
```

## Data Sources & Weighting

The enhanced prediction system uses the following data sources with their respective weights:

1. **Recent Form (40%):**
   - Last 5 matches for each team
   - Home/away specific performance
   - Goals scored and conceded
   - Clean sheets and BTTS statistics

2. **Head-to-Head History (20%):**
   - Last 10 meetings between teams
   - Historical goal patterns
   - Home/away advantage in H2H

3. **Injuries & Suspensions (15%):**
   - Key player availability
   - Impact rating based on missing players
   - Position-specific impact assessment

4. **Home Advantage (10%):**
   - General home team advantage
   - Venue-specific factors

5. **League Standings & Motivation (10%):**
   - Current league position
   - Title race, European spots, or relegation battle
   - Points from top/bottom

6. **Other Factors (5%):**
   - Base SportMonks predictions
   - Additional contextual data

## Confidence Levels

- **High:** Maximum probability > 55% with strong supporting factors
- **Medium:** Maximum probability > 45% with moderate supporting factors
- **Low:** Lower probabilities or conflicting factors

## Rate Limiting

- Cached responses for 30 minutes (predictions) to 1 hour (single fixtures)
- Maximum 20 fixtures per request for bulk predictions
- Redis caching enabled for improved performance

## Error Responses

```json
{
  "error": "Failed to generate enhanced predictions",
  "message": "Detailed error message",
  "fixture_id": 12345 // If applicable
}
```

## League IDs

Common league IDs for filtering:
- Premier League: 8
- La Liga: 564
- Bundesliga: 82
- Serie A: 384
- Ligue 1: 301