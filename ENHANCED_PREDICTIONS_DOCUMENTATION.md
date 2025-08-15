# Enhanced AI-Powered Football Prediction System

## Overview

The Enhanced Prediction System is a comprehensive AI-powered solution that aggregates data from multiple sources to generate highly accurate football match predictions. It combines team form, head-to-head history, injury reports, league standings, and SportMonks predictions using weighted algorithms.

## Features

### 1. Multi-Source Data Aggregation
- **Recent Team Form**: Analyzes last 5-10 matches for both teams
- **Head-to-Head History**: Reviews past meetings between teams
- **Injury Reports**: Tracks key player absences and their impact
- **League Standings & Motivation**: Considers title races, relegation battles, and European qualification
- **SportMonks Predictions**: Incorporates native SportMonks ML predictions
- **Live Form & Statistics**: Real-time updates on team performance

### 2. Weighted Prediction Algorithm

The system uses the following weights:
- **40%** - Recent team form & goals scored/conceded
- **20%** - Head-to-head history
- **15%** - Injuries and suspensions impact
- **10%** - Home/away advantage
- **10%** - League standing & motivation
- **5%** - Other factors (SportMonks base predictions, weather, etc.)

### 3. Comprehensive Output

Each prediction includes:
- **Match Result Probabilities**: Home win, draw, away win percentages
- **Expected Goals**: Predicted goals for each team
- **BTTS Probability**: Both teams to score likelihood
- **Over/Under 2.5 Goals**: Goal totals prediction
- **Confidence Score**: 0-100% rating of prediction reliability
- **AI Summary**: Human-readable analysis of key factors
- **Recommended Bets**: Best value betting opportunities

## API Endpoints

### 1. Single Fixture Prediction
```
GET /api/v1/predictions/enhanced/{fixture_id}
```

**Response Example:**
```json
{
  "fixture_id": 19427455,
  "fixture": {
    "home_team": "Liverpool",
    "away_team": "AFC Bournemouth",
    "date": "2025-08-15 19:00:00"
  },
  "prediction": {
    "match_result": {
      "home_win": 72.5,
      "draw": 18.3,
      "away_win": 9.2
    },
    "goals": {
      "predicted_home": 2.3,
      "predicted_away": 0.8,
      "total_expected": 3.1
    },
    "btts": 45.2,
    "over_25": 68.7
  },
  "confidence_score": 78.5,
  "summary": "Predicted outcome: Liverpool to win (72.5% probability). Liverpool in excellent form. H2H favors Liverpool.",
  "data_quality": {
    "form_matches": 5,
    "h2h_matches": 10,
    "has_injury_data": true,
    "has_motivation_data": true
  }
}
```

### 2. Upcoming Predictions
```
GET /api/v1/predictions/enhanced/upcoming
```

**Query Parameters:**
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)
- `league_id`: Filter by league (optional)
- `team_id`: Filter by team (optional)
- `min_confidence`: Minimum confidence score (0-100)

### 3. Batch Predictions
```
POST /api/v1/predictions/enhanced/batch
```

**Request Body:**
```json
{
  "fixture_ids": [19427455, 19427473, 19427500]
}
```

### 4. Health Check
```
GET /api/v1/predictions/health
```

## Frontend Integration

The system includes a React component (`EnhancedPredictionsView`) that provides:

- **Interactive Filters**: Date range, league, confidence level
- **Visual Predictions**: Progress bars and outcome boxes
- **Tabbed View**: All predictions, high confidence, and value bets
- **Responsive Design**: Mobile-friendly interface

## Technical Architecture

### Backend Components

1. **enhanced_prediction_engine.py**
   - Core prediction logic
   - Data aggregation from multiple sources
   - Weighted algorithm implementation

2. **enhanced_predictions_routes.py**
   - Flask API endpoints
   - Request handling and caching
   - Response formatting

3. **sportmonks_client.py** (Extended)
   - New methods for H2H, injuries, standings
   - Parallel data fetching
   - Caching support

### Frontend Components

1. **EnhancedPredictionsView.tsx**
   - Main UI component
   - Real-time prediction display
   - Filter controls

2. **EnhancedPredictionsView.css**
   - Responsive styling
   - Visual indicators
   - Mobile optimization

## Performance Optimizations

1. **Parallel Data Fetching**: Uses ThreadPoolExecutor for concurrent API calls
2. **Redis Caching**: 30-minute cache for predictions, 10-minute for upcoming fixtures
3. **Batch Processing**: Limits to 20 fixtures per request to prevent timeouts
4. **Smart Data Loading**: Only fetches missing data from API

## Configuration

### Environment Variables
```bash
SPORTMONKS_API_KEY=your_api_key
SPORTMONKS_PRIMARY_TOKEN=your_primary_token
SPORTMONKS_FALLBACK_TOKENS=token1,token2
REDIS_URL=redis://localhost:6379/0
```

### Required SportMonks API Endpoints
- `/fixtures/{id}` with includes: participants, league, venue, state, scores, predictions.type
- `/fixtures/between/{start}/{end}/{team_id}`
- `/fixtures/head-to-head/{team1}/{team2}`
- `/injuries/teams/{team_id}`
- `/standings/seasons/{season_id}`

## Testing

Run the test script to verify the system:

```bash
python test_enhanced_predictions.py
```

This will test:
1. Health check endpoint
2. Single fixture prediction
3. Upcoming predictions
4. Batch predictions

## Deployment

1. **Backend**: Deploy to Render or similar platform
2. **Frontend**: Build and deploy React app
3. **Database**: Ensure PostgreSQL is configured
4. **Redis**: Set up Redis for caching

## Future Enhancements

1. **Machine Learning Integration**: Train custom models on historical data
2. **Real-time Updates**: WebSocket support for live predictions
3. **Advanced Statistics**: xG models, player-specific analysis
4. **Weather Integration**: Consider weather conditions
5. **Betting Odds Comparison**: Compare predictions with bookmaker odds

## Troubleshooting

### Common Issues

1. **No predictions returned**
   - Check SportMonks API key configuration
   - Verify fixture IDs are valid
   - Ensure date range includes fixtures

2. **Low confidence scores**
   - Limited historical data available
   - Missing injury or H2H information
   - Recent team form unavailable

3. **Slow response times**
   - Enable Redis caching
   - Reduce batch size
   - Check API rate limits