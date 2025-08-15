"""
Advanced Predictions Routes
Provides AI-powered predictions with multi-source data aggregation for the main page
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from prediction_engine import AdvancedPredictionEngine
from sportmonks_client import SportMonksAPIClient
import logging
from flask_cors import cross_origin
from functools import wraps
import time
import redis
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Create Blueprint
advanced_predictions_bp = Blueprint('advanced_predictions', __name__, url_prefix='/api/v1/predictions/advanced')

# Initialize clients
sportmonks_client = SportMonksAPIClient()
prediction_engine = AdvancedPredictionEngine(sportmonks_client)

# Cache decorator
def cache_response(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = f"advanced_predictions:{f.__name__}"
            
            # Add request args to cache key
            if request.args:
                sorted_args = sorted(request.args.items())
                args_str = "&".join([f"{k}={v}" for k, v in sorted_args])
                cache_key = f"{cache_key}:{args_str}"
            
            # Add request body to cache key if POST
            if request.method == 'POST' and request.json:
                body_str = json.dumps(request.json, sort_keys=True)
                cache_key = f"{cache_key}:{body_str}"
            
            # Try to get from cache
            try:
                redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
                r = redis.from_url(redis_url, decode_responses=True)
                
                cached_data = r.get(cache_key)
                if cached_data:
                    logger.info(f"Cache hit for {cache_key}")
                    return json.loads(cached_data), 200
            except Exception as e:
                logger.warning(f"Cache error: {e}, proceeding without cache")
            
            # Call the actual function
            result = f(*args, **kwargs)
            
            # Cache the result if successful
            if isinstance(result, tuple) and len(result) == 2 and result[1] == 200:
                try:
                    response_data = result[0].get_json() if hasattr(result[0], 'get_json') else result[0]
                    r.setex(cache_key, timeout, json.dumps(response_data))
                    logger.info(f"Cached response for {cache_key} with timeout {timeout}s")
                except Exception as e:
                    logger.warning(f"Failed to cache response: {e}")
            
            return result
        return decorated_function
    return decorator

@advanced_predictions_bp.route('/', methods=['GET'])
@cross_origin()
@cache_response(timeout=600)
def get_advanced_predictions():
    """
    Get advanced AI-powered predictions for fixtures
    
    Query parameters:
    - date_from: Start date (default: today)
    - date_to: End date (default: 7 days from today)
    - league_id: Filter by league (optional)
    - team_id: Filter by team (optional)
    - min_confidence: Minimum confidence score (0-100, default: 0)
    - include_live: Include live matches (default: false)
    - page: Page number for pagination (default: 1)
    - per_page: Results per page (default: 10, max: 50)
    
    Returns comprehensive predictions with:
    - Match result probabilities
    - Goal predictions
    - BTTS and over/under markets
    - Confidence scores
    - Value bet recommendations
    - Human-readable summaries
    """
    try:
        # Parse query parameters
        date_from = request.args.get('date_from', datetime.utcnow().strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d'))
        league_id = request.args.get('league_id', type=int)
        team_id = request.args.get('team_id', type=int)
        min_confidence = request.args.get('min_confidence', 0, type=float)
        include_live = request.args.get('include_live', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # Get fixtures for the date range
        fixtures_data = sportmonks_client.get_fixtures_between_dates(
            start_date=date_from,
            end_date=date_to,
            include=['participants', 'league', 'state', 'venue']
        )
        
        if not fixtures_data or 'data' not in fixtures_data:
            return jsonify({
                'predictions': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0
                },
                'message': 'No fixtures found for the specified criteria'
            }), 200
        
        fixtures = fixtures_data['data']
        
        # Filter fixtures
        filtered_fixtures = []
        for fixture in fixtures:
            # Skip finished matches unless explicitly requested
            if not include_live and fixture.get('state_id') in [5, 31, 32]:  # Finished states
                continue
            
            # Apply league filter
            if league_id and fixture.get('league_id') != league_id:
                continue
            
            # Apply team filter
            if team_id:
                participants = fixture.get('participants', [])
                team_ids = [p['id'] for p in participants]
                if team_id not in team_ids:
                    continue
            
            filtered_fixtures.append(fixture)
        
        # Pagination
        total_fixtures = len(filtered_fixtures)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_fixtures = filtered_fixtures[start_idx:end_idx]
        
        # Generate predictions in parallel
        predictions = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_fixture = {
                executor.submit(prediction_engine.generate_prediction, fixture['id']): fixture
                for fixture in paginated_fixtures
            }
            
            for future in as_completed(future_to_fixture):
                fixture = future_to_fixture[future]
                try:
                    prediction = future.result()
                    if prediction and prediction.confidence_score >= min_confidence:
                        # Format prediction for response
                        formatted_prediction = {
                            'fixture_id': prediction.fixture_id,
                            'fixture': {
                                'home_team': prediction.home_team,
                                'away_team': prediction.away_team,
                                'date': prediction.date,
                                'league': fixture.get('league', {}).get('name', 'Unknown'),
                                'venue': fixture.get('venue', {}).get('name', 'Unknown')
                            },
                            'probabilities': {
                                'home_win': prediction.win_probability_home,
                                'draw': prediction.draw_probability,
                                'away_win': prediction.win_probability_away
                            },
                            'goals': {
                                'predicted_home': prediction.predicted_goals_home,
                                'predicted_away': prediction.predicted_goals_away,
                                'total_expected': round(prediction.predicted_goals_home + prediction.predicted_goals_away, 1)
                            },
                            'markets': {
                                'btts': {
                                    'yes': prediction.btts_probability,
                                    'no': round(100 - prediction.btts_probability, 1)
                                },
                                'over_under': {
                                    'over_25': prediction.over_25_probability,
                                    'under_25': prediction.under_25_probability,
                                    'over_35': prediction.over_35_probability,
                                    'under_35': round(100 - prediction.over_35_probability, 1)
                                }
                            },
                            'confidence_score': prediction.confidence_score,
                            'prediction_summary': prediction.prediction_summary,
                            'value_bets': prediction.value_bets,
                            'factors_breakdown': prediction.factors_breakdown
                        }
                        predictions.append(formatted_prediction)
                except Exception as e:
                    logger.warning(f"Failed to generate prediction for fixture {fixture.get('id')}: {str(e)}")
                    continue
        
        # Sort by confidence score
        predictions.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return jsonify({
            'predictions': predictions,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_fixtures,
                'total_pages': (total_fixtures + per_page - 1) // per_page
            },
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'league_id': league_id,
                'team_id': team_id,
                'min_confidence': min_confidence,
                'include_live': include_live
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting advanced predictions: {str(e)}")
        return jsonify({
            'error': 'Failed to generate predictions',
            'message': str(e)
        }), 500

@advanced_predictions_bp.route('/fixture/<int:fixture_id>', methods=['GET'])
@cross_origin()
@cache_response(timeout=1800)
def get_single_fixture_prediction(fixture_id):
    """
    Get detailed advanced prediction for a single fixture
    
    Returns comprehensive prediction data including:
    - All probability calculations
    - Detailed data sources used
    - Factor breakdowns
    - Historical context
    """
    try:
        prediction = prediction_engine.generate_prediction(fixture_id)
        
        if not prediction:
            return jsonify({
                'error': 'Unable to generate prediction',
                'message': 'Fixture not found or insufficient data available'
            }), 404
        
        # Format detailed response
        response = {
            'fixture_id': prediction.fixture_id,
            'fixture': {
                'home_team': prediction.home_team,
                'away_team': prediction.away_team,
                'date': prediction.date
            },
            'probabilities': {
                'match_result': {
                    'home_win': prediction.win_probability_home,
                    'draw': prediction.draw_probability,
                    'away_win': prediction.win_probability_away
                },
                'double_chance': {
                    'home_or_draw': round(prediction.win_probability_home + prediction.draw_probability, 1),
                    'away_or_draw': round(prediction.win_probability_away + prediction.draw_probability, 1),
                    'home_or_away': round(prediction.win_probability_home + prediction.win_probability_away, 1)
                }
            },
            'goals': {
                'predicted': {
                    'home': prediction.predicted_goals_home,
                    'away': prediction.predicted_goals_away,
                    'total': round(prediction.predicted_goals_home + prediction.predicted_goals_away, 1)
                },
                'markets': {
                    'over_05': round(100 - prediction_engine._calculate_poisson_probability(
                        prediction.predicted_goals_home + prediction.predicted_goals_away, 0.5, over=False), 1),
                    'over_15': round(100 - prediction_engine._calculate_poisson_probability(
                        prediction.predicted_goals_home + prediction.predicted_goals_away, 1.5, over=False), 1),
                    'over_25': prediction.over_25_probability,
                    'over_35': prediction.over_35_probability,
                    'under_25': prediction.under_25_probability,
                    'under_35': round(100 - prediction.over_35_probability, 1)
                }
            },
            'btts': {
                'yes': prediction.btts_probability,
                'no': round(100 - prediction.btts_probability, 1)
            },
            'confidence_score': prediction.confidence_score,
            'prediction_summary': prediction.prediction_summary,
            'value_bets': prediction.value_bets,
            'data_sources': {
                'form': prediction.data_sources.get('form', {}),
                'head_to_head': prediction.data_sources.get('h2h', {}),
                'injuries': prediction.data_sources.get('injuries', {}),
                'motivation': prediction.data_sources.get('motivation', {}),
                'base_prediction': prediction.data_sources.get('base_prediction', {})
            },
            'factors_breakdown': prediction.factors_breakdown,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error generating single fixture prediction: {str(e)}")
        return jsonify({
            'error': 'Failed to generate prediction',
            'message': str(e)
        }), 500

@advanced_predictions_bp.route('/batch', methods=['POST'])
@cross_origin()
def get_batch_predictions():
    """
    Get predictions for multiple specific fixtures
    
    Request body:
    {
        "fixture_ids": [123, 456, 789],
        "include_details": false  // Set to true for full prediction details
    }
    """
    try:
        data = request.get_json()
        fixture_ids = data.get('fixture_ids', [])
        include_details = data.get('include_details', False)
        
        if not fixture_ids:
            return jsonify({
                'error': 'No fixture IDs provided',
                'message': 'Please provide a list of fixture_ids in the request body'
            }), 400
        
        if len(fixture_ids) > 20:
            return jsonify({
                'error': 'Too many fixtures requested',
                'message': 'Maximum 20 fixtures can be requested at once'
            }), 400
        
        predictions = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_id = {
                executor.submit(prediction_engine.generate_prediction, fixture_id): fixture_id
                for fixture_id in fixture_ids
            }
            
            for future in as_completed(future_to_id):
                fixture_id = future_to_id[future]
                try:
                    prediction = future.result()
                    if prediction:
                        if include_details:
                            # Include full details
                            predictions.append({
                                'fixture_id': prediction.fixture_id,
                                'home_team': prediction.home_team,
                                'away_team': prediction.away_team,
                                'date': prediction.date,
                                'probabilities': {
                                    'home_win': prediction.win_probability_home,
                                    'draw': prediction.draw_probability,
                                    'away_win': prediction.win_probability_away
                                },
                                'goals': {
                                    'home': prediction.predicted_goals_home,
                                    'away': prediction.predicted_goals_away
                                },
                                'btts': prediction.btts_probability,
                                'over_25': prediction.over_25_probability,
                                'confidence': prediction.confidence_score,
                                'summary': prediction.prediction_summary,
                                'value_bets': prediction.value_bets
                            })
                        else:
                            # Basic prediction only
                            predictions.append({
                                'fixture_id': prediction.fixture_id,
                                'home_team': prediction.home_team,
                                'away_team': prediction.away_team,
                                'prediction': {
                                    'result': 'home' if prediction.win_probability_home > max(prediction.draw_probability, prediction.win_probability_away) 
                                            else 'away' if prediction.win_probability_away > prediction.draw_probability 
                                            else 'draw',
                                    'confidence': prediction.confidence_score
                                },
                                'recommended_bet': prediction.value_bets[0] if prediction.value_bets else None
                            })
                    else:
                        errors.append({
                            'fixture_id': fixture_id,
                            'error': 'Unable to generate prediction'
                        })
                except Exception as e:
                    logger.error(f"Error for fixture {fixture_id}: {str(e)}")
                    errors.append({
                        'fixture_id': fixture_id,
                        'error': str(e)
                    })
        
        return jsonify({
            'predictions': predictions,
            'errors': errors,
            'requested': len(fixture_ids),
            'successful': len(predictions),
            'failed': len(errors)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch predictions: {str(e)}")
        return jsonify({
            'error': 'Failed to process batch request',
            'message': str(e)
        }), 500

@advanced_predictions_bp.route('/value-bets', methods=['GET'])
@cross_origin()
@cache_response(timeout=600)
def get_value_bets():
    """
    Get fixtures with high-value betting opportunities
    
    Query parameters:
    - date_from: Start date (default: today)
    - date_to: End date (default: 3 days from today)
    - min_probability: Minimum probability for value bets (default: 65)
    - bet_types: Comma-separated bet types to include (default: all)
    """
    try:
        # Parse parameters
        date_from = request.args.get('date_from', datetime.utcnow().strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', (datetime.utcnow() + timedelta(days=3)).strftime('%Y-%m-%d'))
        min_probability = request.args.get('min_probability', 65, type=float)
        bet_types = request.args.get('bet_types', '').split(',') if request.args.get('bet_types') else None
        
        # Get fixtures
        fixtures_data = sportmonks_client.get_fixtures_between_dates(
            start_date=date_from,
            end_date=date_to,
            include=['participants', 'league']
        )
        
        if not fixtures_data or 'data' not in fixtures_data:
            return jsonify({'value_bets': []}), 200
        
        value_bets = []
        fixtures = [f for f in fixtures_data['data'] if f.get('state_id') not in [5, 31, 32]][:30]  # Limit to 30 fixtures
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_fixture = {
                executor.submit(prediction_engine.generate_prediction, fixture['id']): fixture
                for fixture in fixtures
            }
            
            for future in as_completed(future_to_fixture):
                fixture = future_to_fixture[future]
                try:
                    prediction = future.result()
                    if prediction and prediction.value_bets:
                        for bet in prediction.value_bets:
                            if bet['probability'] >= min_probability:
                                if not bet_types or bet['type'] in bet_types:
                                    value_bets.append({
                                        'fixture_id': prediction.fixture_id,
                                        'fixture': {
                                            'home_team': prediction.home_team,
                                            'away_team': prediction.away_team,
                                            'date': prediction.date,
                                            'league': fixture.get('league', {}).get('name', 'Unknown')
                                        },
                                        'bet': bet,
                                        'confidence_score': prediction.confidence_score
                                    })
                except Exception as e:
                    logger.warning(f"Failed to process fixture {fixture.get('id')}: {str(e)}")
                    continue
        
        # Sort by probability
        value_bets.sort(key=lambda x: x['bet']['probability'], reverse=True)
        
        return jsonify({
            'value_bets': value_bets[:50],  # Limit to top 50
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'min_probability': min_probability,
                'bet_types': bet_types
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting value bets: {str(e)}")
        return jsonify({
            'error': 'Failed to get value bets',
            'message': str(e)
        }), 500

@advanced_predictions_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint for advanced predictions service"""
    try:
        # Test SportMonks client
        api_health = sportmonks_client.health_check()
        
        return jsonify({
            'status': 'healthy',
            'service': 'advanced_predictions',
            'version': '2.0',
            'api_status': api_health.get('api_status', 'unknown'),
            'cache_enabled': api_health.get('cache_enabled', False),
            'features': [
                'multi-source-aggregation',
                'weighted-predictions',
                'value-bet-identification',
                'batch-processing',
                'real-time-updates'
            ],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'advanced_predictions',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503