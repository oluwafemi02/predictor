from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import logging
from flask_cors import cross_origin
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from sportmonks_client import SportMonksAPIClient
from enhanced_prediction_engine import EnhancedPredictionEngine
import hashlib
import redis
import os

logger = logging.getLogger(__name__)

# Create Blueprint
enhanced_predictions_bp = Blueprint('enhanced_predictions', __name__, url_prefix='/api/v1/predictions')

# Initialize SportMonks client and prediction engine
sportmonks_client = SportMonksAPIClient()
prediction_engine = EnhancedPredictionEngine(sportmonks_client)

# Redis client for caching
try:
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    cache_enabled = True
    logger.info("Redis cache connected for enhanced predictions")
except Exception as e:
    logger.warning(f"Redis cache not available for enhanced predictions: {str(e)}")
    redis_client = None
    cache_enabled = False

def get_cache_key(endpoint: str, params: dict) -> str:
    """Generate a unique cache key"""
    param_str = json.dumps(params, sort_keys=True)
    key_data = f"{endpoint}:{param_str}"
    return f"enhanced_pred:{hashlib.md5(key_data.encode()).hexdigest()}"

def get_from_cache(cache_key: str):
    """Get data from cache"""
    if not cache_enabled:
        return None
    
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.error(f"Cache retrieval error: {str(e)}")
    
    return None

def set_cache(cache_key: str, data: dict, ttl: int = 1800):
    """Set data in cache with TTL"""
    if not cache_enabled:
        return
    
    try:
        redis_client.setex(cache_key, ttl, json.dumps(data))
    except Exception as e:
        logger.error(f"Cache storage error: {str(e)}")

@enhanced_predictions_bp.route('/enhanced', methods=['GET'])
@cross_origin()
def get_enhanced_predictions():
    """
    Get enhanced predictions for fixtures within a date range
    Query params:
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    - league_id: Filter by league (optional)
    - team_id: Filter by team (optional)
    - min_confidence: Minimum confidence level (optional)
    """
    try:
        # Get query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        league_id = request.args.get('league_id', type=int)
        team_id = request.args.get('team_id', type=int)
        min_confidence = request.args.get('min_confidence', 'low')
        
        # Default date range if not provided
        if not date_from:
            date_from = datetime.utcnow().strftime('%Y-%m-%d')
        if not date_to:
            date_to = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Check cache
        cache_params = {
            'date_from': date_from,
            'date_to': date_to,
            'league_id': league_id,
            'team_id': team_id,
            'min_confidence': min_confidence
        }
        cache_key = get_cache_key('enhanced_predictions', cache_params)
        cached_result = get_from_cache(cache_key)
        
        if cached_result:
            logger.info(f"Returning cached enhanced predictions")
            return jsonify(cached_result), 200
        
        # Get fixtures for date range
        fixtures = sportmonks_client.get_fixtures_by_date_range(
            start_date=date_from,
            end_date=date_to,
            league_ids=[league_id] if league_id else None,
            team_id=team_id,
            include=['participants', 'league', 'state']
        )
        
        # Filter for upcoming fixtures only
        upcoming_fixtures = [f for f in fixtures if f.get('state_id') == 1]  # 1 = NS (Not Started)
        
        logger.info(f"Found {len(upcoming_fixtures)} upcoming fixtures")
        
        # Process fixtures in parallel for better performance
        predictions = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit prediction tasks
            future_to_fixture = {
                executor.submit(prediction_engine.get_enhanced_prediction, fixture['id']): fixture
                for fixture in upcoming_fixtures[:20]  # Limit to 20 fixtures to avoid timeout
            }
            
            # Collect results
            for future in as_completed(future_to_fixture):
                fixture = future_to_fixture[future]
                try:
                    prediction = future.result()
                    if prediction:
                        # Filter by confidence if specified
                        confidence_levels = {'low': 1, 'medium': 2, 'high': 3}
                        min_level = confidence_levels.get(min_confidence, 1)
                        pred_level = confidence_levels.get(prediction.confidence_level, 1)
                        
                        if pred_level >= min_level:
                            # Convert dataclass to dict
                            pred_dict = {
                                'fixture_id': prediction.fixture_id,
                                'home_team': prediction.home_team,
                                'away_team': prediction.away_team,
                                'date': prediction.date,
                                'win_probability_home': prediction.win_probability_home,
                                'win_probability_away': prediction.win_probability_away,
                                'draw_probability': prediction.draw_probability,
                                'confidence_level': prediction.confidence_level,
                                'prediction_factors': prediction.prediction_factors,
                                'prediction_summary': prediction.prediction_summary,
                                'recommended_bets': prediction.recommended_bets,
                                'expected_goals': prediction.expected_goals,
                                'btts_probability': prediction.btts_probability,
                                'over_25_probability': prediction.over_25_probability,
                                'league': fixture.get('league', {}).get('name', 'Unknown')
                            }
                            predictions.append(pred_dict)
                except Exception as e:
                    logger.error(f"Error getting prediction for fixture {fixture['id']}: {str(e)}")
        
        # Sort by date and confidence
        predictions.sort(key=lambda x: (x['date'], x['confidence_level'] == 'high'), reverse=False)
        
        result = {
            'predictions': predictions,
            'count': len(predictions),
            'date_range': {
                'from': date_from,
                'to': date_to
            },
            'filters': {
                'league_id': league_id,
                'team_id': team_id,
                'min_confidence': min_confidence
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache the result
        set_cache(cache_key, result, ttl=1800)  # 30 minutes cache
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in get_enhanced_predictions: {str(e)}")
        return jsonify({
            'error': 'Failed to generate enhanced predictions',
            'message': str(e)
        }), 500

@enhanced_predictions_bp.route('/enhanced/<int:fixture_id>', methods=['GET'])
@cross_origin()
def get_single_enhanced_prediction(fixture_id):
    """Get enhanced prediction for a single fixture"""
    try:
        # Check cache
        cache_key = get_cache_key(f'enhanced_prediction_{fixture_id}', {})
        cached_result = get_from_cache(cache_key)
        
        if cached_result:
            logger.info(f"Returning cached prediction for fixture {fixture_id}")
            return jsonify(cached_result), 200
        
        # Generate prediction
        prediction = prediction_engine.get_enhanced_prediction(fixture_id)
        
        if not prediction:
            return jsonify({
                'error': 'Could not generate prediction',
                'fixture_id': fixture_id
            }), 404
        
        # Convert to dict
        result = {
            'fixture_id': prediction.fixture_id,
            'home_team': prediction.home_team,
            'away_team': prediction.away_team,
            'date': prediction.date,
            'win_probability_home': prediction.win_probability_home,
            'win_probability_away': prediction.win_probability_away,
            'draw_probability': prediction.draw_probability,
            'confidence_level': prediction.confidence_level,
            'prediction_factors': prediction.prediction_factors,
            'prediction_summary': prediction.prediction_summary,
            'recommended_bets': prediction.recommended_bets,
            'expected_goals': prediction.expected_goals,
            'btts_probability': prediction.btts_probability,
            'over_25_probability': prediction.over_25_probability,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache the result
        set_cache(cache_key, result, ttl=3600)  # 1 hour cache
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting prediction for fixture {fixture_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to generate prediction',
            'message': str(e),
            'fixture_id': fixture_id
        }), 500

@enhanced_predictions_bp.route('/value-bets', methods=['GET'])
@cross_origin()
def get_value_bet_predictions():
    """Get predictions with high confidence for value betting"""
    try:
        # Get query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        min_probability = request.args.get('min_probability', 60, type=float)
        league_id = request.args.get('league_id', type=int)
        
        # Default date range
        if not date_from:
            date_from = datetime.utcnow().strftime('%Y-%m-%d')
        if not date_to:
            date_to = (datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Check cache
        cache_params = {
            'date_from': date_from,
            'date_to': date_to,
            'min_probability': min_probability,
            'league_id': league_id
        }
        cache_key = get_cache_key('value_bets', cache_params)
        cached_result = get_from_cache(cache_key)
        
        if cached_result:
            return jsonify(cached_result), 200
        
        # Get fixtures
        fixtures = sportmonks_client.get_fixtures_by_date_range(
            start_date=date_from,
            end_date=date_to,
            league_ids=[league_id] if league_id else None,
            include=['participants', 'league', 'state']
        )
        
        # Filter upcoming fixtures
        upcoming_fixtures = [f for f in fixtures if f.get('state_id') == 1]
        
        value_bets = []
        
        # Process fixtures
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_fixture = {
                executor.submit(prediction_engine.get_enhanced_prediction, fixture['id']): fixture
                for fixture in upcoming_fixtures[:15]
            }
            
            for future in as_completed(future_to_fixture):
                fixture = future_to_fixture[future]
                try:
                    prediction = future.result()
                    if prediction and prediction.confidence_level in ['high', 'medium']:
                        # Check for high probability bets
                        max_prob = max(
                            prediction.win_probability_home,
                            prediction.win_probability_away,
                            prediction.draw_probability
                        )
                        
                        if max_prob >= min_probability:
                            # Determine bet type
                            if prediction.win_probability_home == max_prob:
                                bet_type = 'Home Win'
                                team = prediction.home_team
                            elif prediction.win_probability_away == max_prob:
                                bet_type = 'Away Win'
                                team = prediction.away_team
                            else:
                                bet_type = 'Draw'
                                team = 'Draw'
                            
                            value_bet = {
                                'fixture_id': prediction.fixture_id,
                                'home_team': prediction.home_team,
                                'away_team': prediction.away_team,
                                'date': prediction.date,
                                'bet_type': bet_type,
                                'team': team,
                                'probability': max_prob,
                                'confidence_level': prediction.confidence_level,
                                'expected_goals': prediction.expected_goals,
                                'recommended_bets': prediction.recommended_bets[:2],
                                'summary': prediction.prediction_summary,
                                'league': fixture.get('league', {}).get('name', 'Unknown')
                            }
                            value_bets.append(value_bet)
                        
                        # Also check for high probability goal markets
                        if prediction.over_25_probability >= min_probability:
                            value_bets.append({
                                'fixture_id': prediction.fixture_id,
                                'home_team': prediction.home_team,
                                'away_team': prediction.away_team,
                                'date': prediction.date,
                                'bet_type': 'Over 2.5 Goals',
                                'probability': prediction.over_25_probability,
                                'confidence_level': prediction.confidence_level,
                                'expected_goals': prediction.expected_goals,
                                'league': fixture.get('league', {}).get('name', 'Unknown')
                            })
                        elif (100 - prediction.over_25_probability) >= min_probability:
                            value_bets.append({
                                'fixture_id': prediction.fixture_id,
                                'home_team': prediction.home_team,
                                'away_team': prediction.away_team,
                                'date': prediction.date,
                                'bet_type': 'Under 2.5 Goals',
                                'probability': 100 - prediction.over_25_probability,
                                'confidence_level': prediction.confidence_level,
                                'expected_goals': prediction.expected_goals,
                                'league': fixture.get('league', {}).get('name', 'Unknown')
                            })
                        
                except Exception as e:
                    logger.error(f"Error processing fixture {fixture['id']}: {str(e)}")
        
        # Sort by probability
        value_bets.sort(key=lambda x: x['probability'], reverse=True)
        
        result = {
            'value_bets': value_bets[:20],  # Top 20 value bets
            'count': len(value_bets),
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'min_probability': min_probability,
                'league_id': league_id
            },
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache result
        set_cache(cache_key, result, ttl=1800)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting value bets: {str(e)}")
        return jsonify({
            'error': 'Failed to generate value bets',
            'message': str(e)
        }), 500

@enhanced_predictions_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check for enhanced predictions service"""
    try:
        # Test SportMonks client
        api_health = sportmonks_client.health_check()
        
        # Test cache
        cache_status = 'healthy' if cache_enabled else 'disabled'
        
        return jsonify({
            'status': 'healthy',
            'api_status': api_health.get('api_status', 'unknown'),
            'cache_status': cache_status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500