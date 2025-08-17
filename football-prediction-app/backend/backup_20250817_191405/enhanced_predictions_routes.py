"""
Enhanced Predictions Routes
Provides AI-powered predictions with multi-source data aggregation
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from enhanced_prediction_engine import EnhancedPredictionEngine
from sportmonks_client import SportMonksAPIClient
import logging
from flask_cors import cross_origin
from functools import wraps
import time
import redis
import json
import os

logger = logging.getLogger(__name__)

# Create Blueprint
enhanced_predictions_bp = Blueprint('enhanced_predictions', __name__, url_prefix='/api/v1/predictions')

# Initialize clients
sportmonks_client = SportMonksAPIClient()
prediction_engine = EnhancedPredictionEngine(sportmonks_client)

# Cache decorator
def cache_response(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = f"enhanced_predictions:{f.__name__}"
            
            # Add request args to cache key
            if request.args:
                sorted_args = sorted(request.args.items())
                args_str = "&".join([f"{k}={v}" for k, v in sorted_args])
                cache_key = f"{cache_key}:{args_str}"
            
            # Add fixture_id from route if present
            if 'fixture_id' in kwargs:
                cache_key = f"{cache_key}:fixture_{kwargs['fixture_id']}"
            
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

# Error handler decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            end_time = time.time()
            response_time = end_time - start_time
            logger.info(f"{f.__name__} completed in {response_time:.2f}s")
            return result
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            logger.error(f"Error in {f.__name__}: {str(e)} (after {response_time:.2f}s)", exc_info=True)
            
            return jsonify({
                'error': 'Service temporarily unavailable',
                'message': 'Unable to generate enhanced predictions',
                'details': str(e)
            }), 500
    return decorated_function

@enhanced_predictions_bp.route('/enhanced/<int:fixture_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=1800)  # Cache for 30 minutes
def get_enhanced_prediction(fixture_id):
    """
    Get enhanced AI-powered prediction for a specific fixture
    
    This endpoint aggregates data from multiple sources:
    - Recent team form (last 5-10 matches)
    - Head-to-head history
    - Injury reports
    - League standings and motivation
    - SportMonks base predictions
    - Live form and statistics
    
    Returns a comprehensive prediction with confidence scores
    """
    try:
        logger.info(f"Generating enhanced prediction for fixture {fixture_id}")
        
        # Generate prediction using the engine
        prediction = prediction_engine.generate_prediction(fixture_id)
        
        if not prediction:
            return jsonify({
                'error': 'Unable to generate prediction',
                'message': 'Fixture not found or insufficient data available'
            }), 404
        
        # Convert dataclass to dict and format response
        response = {
            'fixture_id': prediction.fixture_id,
            'fixture': {
                'home_team': prediction.home_team,
                'away_team': prediction.away_team,
                'date': prediction.date
            },
            'prediction': {
                'match_result': {
                    'home_win': prediction.win_probability_home,
                    'draw': prediction.draw_probability,
                    'away_win': prediction.win_probability_away
                },
                'goals': {
                    'predicted_home': prediction.predicted_goals_home,
                    'predicted_away': prediction.predicted_goals_away,
                    'total_expected': round(prediction.predicted_goals_home + prediction.predicted_goals_away, 1)
                },
                'btts': prediction.btts_probability,
                'over_25': prediction.over_25_probability
            },
            'confidence_score': prediction.confidence_score,
            'summary': prediction.prediction_summary,
            'data_quality': {
                'form_matches': len(prediction.data_sources.get('form', {}).get('home', {}).get('last_5_results', [])),
                'h2h_matches': prediction.data_sources.get('h2h', {}).get('total_matches', 0),
                'has_injury_data': bool(prediction.data_sources.get('injuries')),
                'has_motivation_data': bool(prediction.data_sources.get('motivation'))
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error generating enhanced prediction: {str(e)}")
        raise

@enhanced_predictions_bp.route('/enhanced/batch', methods=['POST'])
@cross_origin()
@handle_errors
def get_batch_enhanced_predictions():
    """
    Get enhanced predictions for multiple fixtures
    
    Request body should contain:
    {
        "fixture_ids": [123, 456, 789]
    }
    
    Returns predictions for all requested fixtures
    """
    try:
        data = request.get_json()
        fixture_ids = data.get('fixture_ids', [])
        
        if not fixture_ids:
            return jsonify({
                'error': 'No fixture IDs provided',
                'message': 'Please provide a list of fixture_ids in the request body'
            }), 400
        
        if len(fixture_ids) > 10:
            return jsonify({
                'error': 'Too many fixtures requested',
                'message': 'Maximum 10 fixtures can be requested at once'
            }), 400
        
        predictions = []
        errors = []
        
        for fixture_id in fixture_ids:
            try:
                prediction = prediction_engine.generate_prediction(fixture_id)
                if prediction:
                    predictions.append({
                        'fixture_id': prediction.fixture_id,
                        'home_team': prediction.home_team,
                        'away_team': prediction.away_team,
                        'date': prediction.date,
                        'prediction': {
                            'home_win': prediction.win_probability_home,
                            'draw': prediction.draw_probability,
                            'away_win': prediction.win_probability_away,
                            'btts': prediction.btts_probability,
                            'over_25': prediction.over_25_probability
                        },
                        'confidence': prediction.confidence_score,
                        'summary': prediction.prediction_summary
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
        raise

@enhanced_predictions_bp.route('/enhanced/upcoming', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=600)  # Cache for 10 minutes
def get_upcoming_enhanced_predictions():
    """
    Get enhanced predictions for upcoming fixtures
    
    Query parameters:
    - date_from: Start date (default: today)
    - date_to: End date (default: 7 days from today)
    - league_id: Filter by league (optional)
    - team_id: Filter by team (optional)
    - min_confidence: Minimum confidence score (0-100, default: 0)
    """
    try:
        # Parse query parameters
        date_from = request.args.get('date_from', datetime.utcnow().strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d'))
        league_id = request.args.get('league_id', type=int)
        team_id = request.args.get('team_id', type=int)
        min_confidence = request.args.get('min_confidence', 0, type=float)
        
        # Get fixtures for the date range
        fixtures = sportmonks_client.get_fixtures_by_date_range(
            start_date=date_from,
            end_date=date_to,
            league_ids=[league_id] if league_id else None,
            team_id=team_id,
            include=['participants', 'league']
        )
        
        if not fixtures:
            return jsonify({
                'predictions': [],
                'message': 'No fixtures found for the specified criteria'
            }), 200
        
        # Generate predictions for each fixture
        predictions = []
        
        for fixture in fixtures[:20]:  # Limit to 20 fixtures to avoid timeout
            try:
                # Skip finished matches
                if fixture.get('state_id') in [5, 31, 32]:  # Finished states
                    continue
                
                prediction = prediction_engine.generate_prediction(fixture['id'])
                
                if prediction and prediction.confidence_score >= min_confidence:
                    # Extract participants
                    participants = fixture.get('participants', [])
                    home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
                    away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
                    
                    predictions.append({
                        'fixture_id': fixture['id'],
                        'fixture': {
                            'home_team': home_team.get('name', 'Unknown'),
                            'away_team': away_team.get('name', 'Unknown'),
                            'date': fixture.get('starting_at'),
                            'league': fixture.get('league', {}).get('name', 'Unknown')
                        },
                        'prediction': {
                            'match_result': {
                                'home_win': prediction.win_probability_home,
                                'draw': prediction.draw_probability,
                                'away_win': prediction.win_probability_away
                            },
                            'goals': {
                                'home': prediction.predicted_goals_home,
                                'away': prediction.predicted_goals_away,
                                'total': round(prediction.predicted_goals_home + prediction.predicted_goals_away, 1)
                            },
                            'btts': prediction.btts_probability,
                            'over_25': prediction.over_25_probability
                        },
                        'confidence': prediction.confidence_score,
                        'summary': prediction.prediction_summary,
                        'recommended_bet': _get_recommended_bet(prediction)
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to generate prediction for fixture {fixture.get('id')}: {str(e)}")
                continue
        
        # Sort by confidence score
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return jsonify({
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
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting upcoming predictions: {str(e)}")
        raise

def _get_recommended_bet(prediction):
    """Determine the best betting recommendation based on prediction data"""
    recommendations = []
    
    # Match result
    max_prob = max(prediction.win_probability_home, prediction.draw_probability, prediction.win_probability_away)
    if max_prob > 60:
        if prediction.win_probability_home == max_prob:
            recommendations.append({
                'type': 'Match Result',
                'selection': 'Home Win',
                'probability': prediction.win_probability_home
            })
        elif prediction.win_probability_away == max_prob:
            recommendations.append({
                'type': 'Match Result',
                'selection': 'Away Win',
                'probability': prediction.win_probability_away
            })
        else:
            recommendations.append({
                'type': 'Match Result',
                'selection': 'Draw',
                'probability': prediction.draw_probability
            })
    
    # Double chance
    home_or_draw = prediction.win_probability_home + prediction.draw_probability
    away_or_draw = prediction.win_probability_away + prediction.draw_probability
    
    if home_or_draw > 70:
        recommendations.append({
            'type': 'Double Chance',
            'selection': 'Home or Draw',
            'probability': home_or_draw
        })
    elif away_or_draw > 70:
        recommendations.append({
            'type': 'Double Chance',
            'selection': 'Away or Draw',
            'probability': away_or_draw
        })
    
    # Goals markets
    if prediction.over_25_probability > 65:
        recommendations.append({
            'type': 'Total Goals',
            'selection': 'Over 2.5',
            'probability': prediction.over_25_probability
        })
    elif prediction.over_25_probability < 35:
        recommendations.append({
            'type': 'Total Goals',
            'selection': 'Under 2.5',
            'probability': 100 - prediction.over_25_probability
        })
    
    # BTTS
    if prediction.btts_probability > 65:
        recommendations.append({
            'type': 'BTTS',
            'selection': 'Yes',
            'probability': prediction.btts_probability
        })
    elif prediction.btts_probability < 35:
        recommendations.append({
            'type': 'BTTS',
            'selection': 'No',
            'probability': 100 - prediction.btts_probability
        })
    
    # Return the best recommendation
    if recommendations:
        return max(recommendations, key=lambda x: x['probability'])
    
    return None

@enhanced_predictions_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint for enhanced predictions service"""
    try:
        # Test SportMonks client
        api_health = sportmonks_client.health_check()
        
        return jsonify({
            'status': 'healthy',
            'service': 'enhanced_predictions',
            'api_status': api_health.get('api_status', 'unknown'),
            'cache_enabled': api_health.get('cache_enabled', False),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'enhanced_predictions',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503