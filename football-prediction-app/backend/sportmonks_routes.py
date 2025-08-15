from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sportmonks_client import SportMonksAPIClient
from sportmonks_models import (
    db, SportMonksLeague, SportMonksTeam, SportMonksFixture,
    SportMonksPrediction, SportMonksValueBet, SportMonksOdds,
    SportMonksLiveData, SportMonksPlayer, SportMonksStanding
)
from sqlalchemy import and_, or_, desc
import logging
from flask_cors import cross_origin
from functools import wraps
import time
from typing import List, Dict

logger = logging.getLogger(__name__)

# Create Blueprint
sportmonks_bp = Blueprint('sportmonks', __name__, url_prefix='/api/sportmonks')

# Initialize SportMonks client
sportmonks_client = SportMonksAPIClient()

# Cache decorator with Redis support
def cache_response(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"sportmonks:{f.__name__}"
            
            # Add request args to cache key
            if request.args:
                sorted_args = sorted(request.args.items())
                args_str = "&".join([f"{k}={v}" for k, v in sorted_args])
                cache_key = f"{cache_key}:{args_str}"
            
            # Try to get from cache
            try:
                import redis
                import json
                import os
                
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
                    # Cache only successful responses
                    response_data = result[0].get_json() if hasattr(result[0], 'get_json') else result[0]
                    r.setex(cache_key, timeout, json.dumps(response_data))
                    logger.info(f"Cached response for {cache_key} with timeout {timeout}s")
                except Exception as e:
                    logger.warning(f"Failed to cache response: {e}")
            
            return result
        return decorated_function
    return decorator

# Error handler decorator with response time logging
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            end_time = time.time()
            response_time = end_time - start_time
            logger.info(f"{f.__name__} completed in {response_time:.2f}s")
            
            # Add response time header
            if isinstance(result, tuple) and len(result) == 2:
                response, status_code = result
                if hasattr(response, 'headers'):
                    response.headers['X-Response-Time'] = f"{response_time:.3f}"
            
            return result
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            logger.error(f"Error in {f.__name__}: {str(e)} (after {response_time:.2f}s)", exc_info=True)
            
            # Check if API key is missing
            import os
            if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
                return jsonify({
                    'error': 'SportMonks API not configured',
                    'message': 'API key is missing. Returning mock data.',
                    'is_mock_data': True,
                    'fixtures': [],
                    'data': []
                }), 200
            
            # Return a more graceful error response
            return jsonify({
                'error': 'Service temporarily unavailable',
                'message': 'Unable to fetch data from SportMonks API',
                'details': str(e),
                'fixtures': [],
                'data': []
            }), 200  # Return 200 to avoid CORS issues
    return decorated_function

# Add CORS test endpoint
@sportmonks_bp.route('/test-cors', methods=['GET', 'OPTIONS'])
@cross_origin()
def test_cors():
    """Test endpoint to verify CORS is working"""
    return jsonify({
        'status': 'success',
        'message': 'CORS is working correctly',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Routes

@sportmonks_bp.route('/health', methods=['GET'])
@cross_origin()
@handle_errors
def health_check():
    """Check SportMonks API health and configuration"""
    health_status = sportmonks_client.health_check()
    return jsonify(health_status), 200

@sportmonks_bp.route('/debug/config', methods=['GET'])
@cross_origin()
@handle_errors
def debug_config():
    """Debug endpoint to check configuration (remove in production)"""
    import os
    config_status = {
        'sportmonks_api_key_set': bool(os.environ.get('SPORTMONKS_API_KEY')),
        'sportmonks_primary_token_set': bool(os.environ.get('SPORTMONKS_PRIMARY_TOKEN')),
        'sportmonks_fallback_tokens_set': bool(os.environ.get('SPORTMONKS_FALLBACK_TOKENS')),
        'flask_env': os.environ.get('FLASK_ENV', 'not_set'),
        'cors_origins': current_app.config.get('CORS_ORIGINS', []),
        'frontend_url_in_cors': 'https://football-prediction-frontend-zx5z.onrender.com' in current_app.config.get('CORS_ORIGINS', [])
    }
    return jsonify(config_status), 200

@sportmonks_bp.route('/fixtures/live', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=30)  # Short cache for live data
def get_live_fixtures():
    """Get all currently live fixtures with scores and stats"""
    include_params = request.args.get('include', 'localTeam,visitorTeam,league,stats,events').split(',')
    
    # Get live fixtures from API
    response = sportmonks_client.get_live_scores(include=include_params)
    
    if not response or 'data' not in response:
        return jsonify({'fixtures': [], 'message': 'No live fixtures found'}), 200
    
    # Process and return live fixtures
    fixtures = []
    for fixture_data in response['data']:
        fixture = {
            'id': fixture_data['id'],
            'league': {
                'id': fixture_data.get('league', {}).get('id'),
                'name': fixture_data.get('league', {}).get('name'),
                'logo': fixture_data.get('league', {}).get('logo_path')
            },
            'home_team': {
                'id': fixture_data.get('localTeam', {}).get('id'),
                'name': fixture_data.get('localTeam', {}).get('name'),
                'logo': fixture_data.get('localTeam', {}).get('logo_path')
            },
            'away_team': {
                'id': fixture_data.get('visitorTeam', {}).get('id'),
                'name': fixture_data.get('visitorTeam', {}).get('name'),
                'logo': fixture_data.get('visitorTeam', {}).get('logo_path')
            },
            'scores': {
                'home': fixture_data.get('scores', {}).get('localteam_score'),
                'away': fixture_data.get('scores', {}).get('visitorteam_score')
            },
            'time': {
                'status': fixture_data.get('time', {}).get('status'),
                'minute': fixture_data.get('time', {}).get('minute'),
                'added_time': fixture_data.get('time', {}).get('added_time')
            },
            'stats': fixture_data.get('stats', {}).get('data', []),
            'events': fixture_data.get('events', {}).get('data', [])
        }
        fixtures.append(fixture)
    
    return jsonify({
        'fixtures': fixtures,
        'count': len(fixtures),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@sportmonks_bp.route('/fixtures/upcoming', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=600)
def get_upcoming_fixtures():
    """Get upcoming fixtures with predictions"""
    try:
        days_ahead = int(request.args.get('days', 7))
        league_id = request.args.get('league_id')
        include_predictions = request.args.get('predictions', 'true').lower() == 'true'
        
        # Start from beginning of today instead of current time to include today's matches
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = today.strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching upcoming fixtures from {start_date} to {end_date}")
        
        # Check if API key is configured
        import os
        if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
            logger.warning("No SportMonks API key configured, returning mock data")
            # Return mock data for testing
            mock_fixtures = [
                {
                    'id': 1,
                    'date': (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    'league': {
                        'id': 8,
                        'name': 'Premier League',
                        'logo': 'https://via.placeholder.com/50'
                    },
                    'home_team': {
                        'id': 1,
                        'name': 'Manchester United',
                        'logo': 'https://via.placeholder.com/50'
                    },
                    'away_team': {
                        'id': 2,
                        'name': 'Liverpool',
                        'logo': 'https://via.placeholder.com/50'
                    },
                    'venue': {'name': 'Old Trafford', 'city': 'Manchester'},
                    'predictions': {
                        'match_winner': {'home_win': 35, 'draw': 30, 'away_win': 35},
                        'goals': {'over_25': 60, 'under_25': 40, 'btts_yes': 55, 'btts_no': 45},
                        'correct_scores': []
                    } if include_predictions else None
                },
                {
                    'id': 2,
                    'date': (datetime.utcnow() + timedelta(days=2)).isoformat(),
                    'league': {
                        'id': 8,
                        'name': 'Premier League',
                        'logo': 'https://via.placeholder.com/50'
                    },
                    'home_team': {
                        'id': 3,
                        'name': 'Chelsea',
                        'logo': 'https://via.placeholder.com/50'
                    },
                    'away_team': {
                        'id': 4,
                        'name': 'Arsenal',
                        'logo': 'https://via.placeholder.com/50'
                    },
                    'venue': {'name': 'Stamford Bridge', 'city': 'London'},
                    'predictions': {
                        'match_winner': {'home_win': 40, 'draw': 28, 'away_win': 32},
                        'goals': {'over_25': 65, 'under_25': 35, 'btts_yes': 58, 'btts_no': 42},
                        'correct_scores': []
                    } if include_predictions else None
                }
            ]
            
            return jsonify({
                'fixtures': mock_fixtures,
                'count': len(mock_fixtures),
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'is_mock_data': True
            }), 200
        
        # Get fixtures from API
        league_ids = [int(league_id)] if league_id else None
        include_params = ['localTeam', 'visitorTeam', 'league', 'venue']
        
        fixtures = sportmonks_client.get_fixtures_by_date_range(
            start_date=start_date,
            end_date=end_date,
            league_ids=league_ids,
            include=include_params
        )
        
        logger.info(f"Retrieved {len(fixtures)} fixtures from API")
        
        # Process fixtures and add predictions if requested
        processed_fixtures = []
        
        # First, extract fixture IDs for batch operations
        fixture_ids = [f['id'] for f in fixtures if f.get('id')]
        
        # Fetch predictions in batch if requested (faster than one by one)
        predictions_map = {}
        if include_predictions and fixture_ids:
            logger.info(f"Fetching predictions for {len(fixture_ids)} fixtures")
            # Try to get predictions from database first
            try:
                # Check if we have recent predictions in the database
                from sqlalchemy import and_
                recent_predictions = SportMonksPrediction.query.filter(
                    and_(
                        SportMonksPrediction.fixture_id.in_(fixture_ids),
                        SportMonksPrediction.updated_at > datetime.utcnow() - timedelta(hours=6)
                    )
                ).all()
                
                for pred in recent_predictions:
                    predictions_map[pred.fixture_id] = {
                        'match_winner': {
                            'home_win': pred.home_win_percentage,
                            'draw': pred.draw_percentage,
                            'away_win': pred.away_win_percentage
                        },
                        'goals': {
                            'over_25': pred.over_25_percentage,
                            'under_25': pred.under_25_percentage,
                            'btts_yes': pred.btts_yes_percentage,
                            'btts_no': pred.btts_no_percentage
                        },
                        'correct_scores': pred.correct_scores or []
                    }
                
                logger.info(f"Found {len(predictions_map)} predictions in database")
                
                # Get missing predictions from API
                missing_ids = [fid for fid in fixture_ids if fid not in predictions_map]
                if missing_ids:
                    logger.info(f"Fetching {len(missing_ids)} missing predictions from API")
                    # Batch API calls for missing predictions
                    for fixture_id in missing_ids[:10]:  # Limit to 10 to avoid timeout
                        try:
                            prediction_response = sportmonks_client.get_predictions_by_fixture(fixture_id)
                            if prediction_response and 'data' in prediction_response:
                                prediction_data = prediction_response['data']
                                predictions_map[fixture_id] = {
                                    'match_winner': {
                                        'home_win': prediction_data.get('predictions', {}).get('home', 0),
                                        'draw': prediction_data.get('predictions', {}).get('draw', 0),
                                        'away_win': prediction_data.get('predictions', {}).get('away', 0)
                                    },
                                    'goals': {
                                        'over_25': prediction_data.get('predictions', {}).get('over_25', 0),
                                        'under_25': prediction_data.get('predictions', {}).get('under_25', 0),
                                        'btts_yes': prediction_data.get('predictions', {}).get('btts_yes', 0),
                                        'btts_no': prediction_data.get('predictions', {}).get('btts_no', 0)
                                    },
                                    'correct_scores': prediction_data.get('predictions', {}).get('correct_scores', [])
                                }
                        except Exception as e:
                            logger.warning(f"Failed to get predictions for fixture {fixture_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error fetching predictions: {str(e)}")
        
        # Process fixtures with optimized data extraction
        for fixture_data in fixtures:
            fixture = {
                'id': fixture_data['id'],
                'date': fixture_data['starting_at'],
                'league': {
                    'id': fixture_data.get('league', {}).get('data', {}).get('id') if 'league' in fixture_data else None,
                    'name': fixture_data.get('league', {}).get('data', {}).get('name') if 'league' in fixture_data else None,
                    'logo': fixture_data.get('league', {}).get('data', {}).get('logo_path') if 'league' in fixture_data else None
                },
                'home_team': {
                    'id': fixture_data.get('localTeam', {}).get('data', {}).get('id') if 'localTeam' in fixture_data else None,
                    'name': fixture_data.get('localTeam', {}).get('data', {}).get('name') if 'localTeam' in fixture_data else None,
                    'logo': fixture_data.get('localTeam', {}).get('data', {}).get('logo_path') if 'localTeam' in fixture_data else None
                },
                'away_team': {
                    'id': fixture_data.get('visitorTeam', {}).get('data', {}).get('id') if 'visitorTeam' in fixture_data else None,
                    'name': fixture_data.get('visitorTeam', {}).get('data', {}).get('name') if 'visitorTeam' in fixture_data else None,
                    'logo': fixture_data.get('visitorTeam', {}).get('data', {}).get('logo_path') if 'visitorTeam' in fixture_data else None
                },
                'venue': fixture_data.get('venue', {}).get('data', {}) if 'venue' in fixture_data else {}
            }
            
            # Add predictions from our map if available
            if include_predictions and fixture_data['id'] in predictions_map:
                fixture['predictions'] = predictions_map[fixture_data['id']]
            
            processed_fixtures.append(fixture)
        
        logger.info(f"Processed {len(processed_fixtures)} fixtures")
        
        return jsonify({
            'fixtures': processed_fixtures,
            'count': len(processed_fixtures),
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        }), 200
    except Exception as e:
        logger.error(f"Error in get_upcoming_fixtures: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch upcoming fixtures',
            'message': str(e),
            'fixtures': [],
            'count': 0
        }), 200  # Return 200 with empty data to avoid CORS preflight issues

@sportmonks_bp.route('/fixtures/past', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=600)
def get_past_fixtures():
    """Get past fixtures from the last N days"""
    try:
        days_back = int(request.args.get('days', 7))
        league_id = request.args.get('league_id')
        include_predictions = request.args.get('predictions', 'false').lower() == 'true'
        
        # Get fixtures from the past N days up to yesterday
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching past fixtures from {start_date} to {end_date}")
        
        # Check if API key is configured
        import os
        if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
            logger.warning("No SportMonks API key configured, returning empty data")
            return jsonify({
                'fixtures': [],
                'count': 0,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'is_mock_data': True
            }), 200
        
        # Get fixtures from API
        league_ids = [int(league_id)] if league_id else None
        include_params = ['localTeam', 'visitorTeam', 'league', 'venue', 'scores']
        
        fixtures = sportmonks_client.get_fixtures_by_date_range(
            start_date=start_date,
            end_date=end_date,
            league_ids=league_ids,
            include=include_params
        )
        
        logger.info(f"Retrieved {len(fixtures)} past fixtures from API")
        
        # Process fixtures
        processed_fixtures = []
        for fixture_data in fixtures:
            fixture = {
                'id': fixture_data['id'],
                'date': fixture_data['starting_at'],
                'status': fixture_data.get('state', {}).get('state', 'FT'),
                'league': {
                    'id': fixture_data.get('league', {}).get('data', {}).get('id') if 'league' in fixture_data else None,
                    'name': fixture_data.get('league', {}).get('data', {}).get('name') if 'league' in fixture_data else None,
                    'logo': fixture_data.get('league', {}).get('data', {}).get('logo_path') if 'league' in fixture_data else None
                },
                'home_team': {
                    'id': fixture_data.get('localTeam', {}).get('data', {}).get('id') if 'localTeam' in fixture_data else None,
                    'name': fixture_data.get('localTeam', {}).get('data', {}).get('name') if 'localTeam' in fixture_data else None,
                    'logo': fixture_data.get('localTeam', {}).get('data', {}).get('logo_path') if 'localTeam' in fixture_data else None
                },
                'away_team': {
                    'id': fixture_data.get('visitorTeam', {}).get('data', {}).get('id') if 'visitorTeam' in fixture_data else None,
                    'name': fixture_data.get('visitorTeam', {}).get('data', {}).get('name') if 'visitorTeam' in fixture_data else None,
                    'logo': fixture_data.get('visitorTeam', {}).get('data', {}).get('logo_path') if 'visitorTeam' in fixture_data else None
                },
                'scores': fixture_data.get('scores', {}),
                'venue': fixture_data.get('venue', {}).get('data', {}) if 'venue' in fixture_data else {}
            }
            
            processed_fixtures.append(fixture)
        
        logger.info(f"Processed {len(processed_fixtures)} past fixtures")
        
        return jsonify({
            'fixtures': processed_fixtures,
            'count': len(processed_fixtures),
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        }), 200
    except Exception as e:
        logger.error(f"Error in get_past_fixtures: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch past fixtures',
            'message': str(e),
            'fixtures': [],
            'count': 0
        }), 200  # Return 200 with empty data to avoid CORS preflight issues

def _get_status_name(state_id: int) -> str:
    """Convert state_id to status name"""
    status_map = {
        1: 'NS',  # Not Started
        2: 'LIVE',
        3: 'HT',  # Half Time
        4: 'FT',  # Full Time
        5: 'ET',  # Extra Time
        6: 'PEN',  # Penalties
        7: 'FT_PEN',  # Full Time after Penalties
        8: 'CANCL',  # Cancelled
        9: 'POSTP',  # Postponed
        10: 'INT',  # Interrupted
        11: 'ABAN',  # Abandoned
        12: 'SUSP',  # Suspended
        13: 'AWARDED',
        14: 'DELAYED',
        15: 'TBA',  # To Be Announced
        16: 'WO',  # Walkover
        17: 'AU',  # Awaiting Updates
        18: 'Deleted'
    }
    return status_map.get(state_id, 'NS')

def _transform_scores(scores: List[Dict]) -> Dict:
    """Transform scores array to our format"""
    if not scores:
        return {}
    
    # Find the most recent score (usually FT)
    for score in scores:
        if score.get('description') == 'CURRENT':
            return {
                'localteam_score': score.get('score', {}).get('participant', {}).get('home'),
                'visitorteam_score': score.get('score', {}).get('participant', {}).get('away')
            }
    
    # Fallback to first score if no CURRENT found
    if scores:
        first_score = scores[0]
        return {
            'localteam_score': first_score.get('score', {}).get('participant', {}).get('home'),
            'visitorteam_score': first_score.get('score', {}).get('participant', {}).get('away')
        }
    
    return {}

@sportmonks_bp.route('/fixtures/all', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=600)
def get_all_fixtures():
    """Get all fixtures - past, today, and upcoming"""
    try:
        days_back = int(request.args.get('days_back', 7))
        days_ahead = int(request.args.get('days_ahead', 7))
        league_id = int(request.args.get('league_id', 8))  # Default to EPL
        team_id = request.args.get('team_id')
        include_predictions = request.args.get('predictions', 'false').lower() == 'true'
        
        # Calculate date range
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = today - timedelta(days=days_back)
        end_date = today + timedelta(days=days_ahead)
        
        logger.info(f"Fetching all fixtures from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Check if API key is configured
        import os
        if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
            logger.warning("No SportMonks API key configured, returning empty data")
            return jsonify({
                'fixtures': {
                    'past': [],
                    'today': [],
                    'upcoming': []
                },
                'count': {
                    'past': 0,
                    'today': 0,
                    'upcoming': 0,
                    'total': 0
                },
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'is_mock_data': True
            }), 200
        
        # Get current season ID for the league
        season_id = sportmonks_client.get_current_season_id(league_id)
        if not season_id:
            # Fallback to known season IDs
            season_ids = {
                8: 25583,  # EPL 2025-26 season
                564: 23764,  # La Liga
                82: 23625,  # Bundesliga
            }
            season_id = season_ids.get(league_id, 25583)
        
        logger.info(f"Using season ID: {season_id} for league ID: {league_id}")
        
        # Get fixtures from season schedule
        fixtures = []
        if team_id:
            # Get fixtures for specific team
            fixtures = sportmonks_client.get_season_schedule(season_id, int(team_id))
        else:
            # Get all fixtures for the season
            fixtures = sportmonks_client.get_season_schedule(season_id)
        
        logger.info(f"Retrieved {len(fixtures)} total fixtures from season schedule")
        
        # Categorize and transform fixtures
        past_fixtures = []
        today_fixtures = []
        upcoming_fixtures = []
        today_str = today.strftime('%Y-%m-%d')
        
        for fixture_data in fixtures:
            # Parse fixture date
            fixture_datetime = datetime.fromisoformat(fixture_data.get('starting_at', '').replace(' ', 'T'))
            fixture_date_str = fixture_datetime.strftime('%Y-%m-%d')
            
            # Filter by date range
            if fixture_datetime.date() < start_date.date() or fixture_datetime.date() > end_date.date():
                continue
            
            # Transform fixture data to match our format
            participants = fixture_data.get('participants', [])
            home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
            away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
            
            fixture = {
                'id': fixture_data.get('id'),
                'fixture_id': fixture_data.get('id'),
                'date': fixture_data.get('starting_at'),
                'status': _get_status_name(fixture_data.get('state_id', 1)),
                'league': {
                    'id': fixture_data.get('league_id', league_id),
                    'name': 'Premier League' if fixture_data.get('league_id') == 8 else f'League {fixture_data.get("league_id")}',
                    'logo': None
                },
                'home_team': {
                    'id': home_team.get('id'),
                    'name': home_team.get('name', 'Unknown'),
                    'logo': home_team.get('image_path'),
                    'short_code': home_team.get('short_code')
                },
                'away_team': {
                    'id': away_team.get('id'),
                    'name': away_team.get('name', 'Unknown'),
                    'logo': away_team.get('image_path'),
                    'short_code': away_team.get('short_code')
                },
                'scores': _transform_scores(fixture_data.get('scores', [])),
                'venue': {
                    'id': fixture_data.get('venue_id'),
                    'name': fixture_data.get('name', '').split(' vs ')[0] if ' vs ' in fixture_data.get('name', '') else 'Unknown'
                }
            }
            
            # Add predictions for upcoming/today fixtures if requested
            if include_predictions and fixture_datetime >= today:
                fixture['predictions'] = None  # Would fetch from predictions API
            
            # Categorize by date
            if fixture_date_str < today_str:
                past_fixtures.append(fixture)
            elif fixture_date_str == today_str:
                today_fixtures.append(fixture)
            else:
                upcoming_fixtures.append(fixture)
        
        # Sort fixtures by date
        past_fixtures.sort(key=lambda x: x['date'], reverse=True)
        today_fixtures.sort(key=lambda x: x['date'])
        upcoming_fixtures.sort(key=lambda x: x['date'])
        
        logger.info(f"Categorized fixtures - Past: {len(past_fixtures)}, Today: {len(today_fixtures)}, Upcoming: {len(upcoming_fixtures)}")
        
        return jsonify({
            'fixtures': {
                'past': past_fixtures,
                'today': today_fixtures,
                'upcoming': upcoming_fixtures
            },
            'count': {
                'past': len(past_fixtures),
                'today': len(today_fixtures),
                'upcoming': len(upcoming_fixtures),
                'total': len(past_fixtures) + len(today_fixtures) + len(upcoming_fixtures)
            },
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'today': today_str
            },
            'season_id': season_id
        }), 200
    except Exception as e:
        logger.error(f"Error in get_all_fixtures: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch fixtures',
            'message': str(e),
            'fixtures': {
                'past': [],
                'today': [],
                'upcoming': []
            },
            'count': {
                'past': 0,
                'today': 0,
                'upcoming': 0,
                'total': 0
            }
        }), 200  # Return 200 with empty data to avoid CORS preflight issues

@sportmonks_bp.route('/predictions/<int:fixture_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=1800)
def get_fixture_predictions(fixture_id):
    """Get detailed predictions for a specific fixture"""
    # Try to get from database first
    db_prediction = SportMonksPrediction.query.filter_by(fixture_id=fixture_id).first()
    
    if db_prediction and (datetime.utcnow() - db_prediction.updated_at).seconds < 3600:
        # Return cached prediction if less than 1 hour old
        return jsonify({
            'fixture_id': fixture_id,
            'predictions': {
                'match_winner': {
                    'home_win': db_prediction.home_win_probability,
                    'draw': db_prediction.draw_probability,
                    'away_win': db_prediction.away_win_probability
                },
                'goals': {
                    'over_15': db_prediction.over_15_probability,
                    'under_15': db_prediction.under_15_probability,
                    'over_25': db_prediction.over_25_probability,
                    'under_25': db_prediction.under_25_probability,
                    'over_35': db_prediction.over_35_probability,
                    'under_35': db_prediction.under_35_probability
                },
                'btts': {
                    'yes': db_prediction.btts_yes_probability,
                    'no': db_prediction.btts_no_probability
                },
                'correct_scores': db_prediction.correct_scores,
                'confidence': db_prediction.confidence_level
            },
            'source': 'database',
            'updated_at': db_prediction.updated_at.isoformat()
        }), 200
    
    # Get fresh prediction from API
    response = sportmonks_client.get_predictions_by_fixture(fixture_id)
    
    if not response or 'data' not in response:
        return jsonify({'error': 'No predictions available for this fixture'}), 404
    
    prediction_data = response['data']['predictions']
    
    # Store in database for caching
    if db_prediction:
        db_prediction.home_win_probability = prediction_data.get('home', 0)
        db_prediction.draw_probability = prediction_data.get('draw', 0)
        db_prediction.away_win_probability = prediction_data.get('away', 0)
        db_prediction.over_25_probability = prediction_data.get('over_25', 0)
        db_prediction.under_25_probability = prediction_data.get('under_25', 0)
        db_prediction.btts_yes_probability = prediction_data.get('btts_yes', 0)
        db_prediction.btts_no_probability = prediction_data.get('btts_no', 0)
        db_prediction.correct_scores = prediction_data.get('correct_scores', [])
        db_prediction.updated_at = datetime.utcnow()
    else:
        db_prediction = SportMonksPrediction(
            fixture_id=fixture_id,
            home_win_probability=prediction_data.get('home', 0),
            draw_probability=prediction_data.get('draw', 0),
            away_win_probability=prediction_data.get('away', 0),
            over_25_probability=prediction_data.get('over_25', 0),
            under_25_probability=prediction_data.get('under_25', 0),
            btts_yes_probability=prediction_data.get('btts_yes', 0),
            btts_no_probability=prediction_data.get('btts_no', 0),
            correct_scores=prediction_data.get('correct_scores', [])
        )
        db.session.add(db_prediction)
    
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to cache prediction: {str(e)}")
        db.session.rollback()
    
    return jsonify({
        'fixture_id': fixture_id,
        'predictions': prediction_data,
        'source': 'api',
        'updated_at': datetime.utcnow().isoformat()
    }), 200

@sportmonks_bp.route('/value-bets', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=600)
def get_value_bets():
    """Get value bet recommendations"""
    min_value = float(request.args.get('min_value', 5.0))  # Minimum 5% value
    date = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    # Get fixtures for the date
    fixtures_response = sportmonks_client.get_fixtures(date=date)
    
    if not fixtures_response or 'data' not in fixtures_response:
        return jsonify({'value_bets': [], 'message': 'No fixtures found for the date'}), 200
    
    value_bets = []
    
    for fixture in fixtures_response['data']:
        # Get value bets for each fixture
        value_bet_response = sportmonks_client.get_value_bets_by_fixture(fixture['id'])
        
        if value_bet_response and 'data' in value_bet_response:
            for bet in value_bet_response['data']:
                if bet.get('value', 0) >= min_value:
                    value_bets.append({
                        'fixture_id': fixture['id'],
                        'fixture_name': f"{fixture.get('localTeam', {}).get('name', 'Home')} vs {fixture.get('visitorTeam', {}).get('name', 'Away')}",
                        'market': bet['market'],
                        'selection': bet['selection'],
                        'predicted_probability': bet['probability'],
                        'bookmaker_odds': bet['odds'],
                        'value_percentage': bet['value'],
                        'recommended_stake': bet.get('stake', 1.0)
                    })
    
    # Sort by value percentage descending
    value_bets.sort(key=lambda x: x['value_percentage'], reverse=True)
    
    return jsonify({
        'value_bets': value_bets[:50],  # Limit to top 50
        'count': len(value_bets),
        'date': date,
        'min_value_filter': min_value
    }), 200

@sportmonks_bp.route('/standings/<int:league_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=1800)
def get_league_standings(league_id):
    """Get current standings for a league"""
    season_id = request.args.get('season_id')
    
    # If no season_id provided, try to get current season
    if not season_id:
        seasons_response = sportmonks_client.get_seasons(league_id=league_id)
        if seasons_response and 'data' in seasons_response:
            # Get the most recent season
            seasons = sorted(seasons_response['data'], key=lambda x: x['id'], reverse=True)
            if seasons:
                season_id = seasons[0]['id']
    
    if not season_id:
        return jsonify({'error': 'Could not determine season for league'}), 400
    
    # Get standings from API
    response = sportmonks_client.get_standings(
        season_id=season_id,
        include=['team', 'league']
    )
    
    if not response or 'data' not in response:
        return jsonify({'error': 'No standings available'}), 404
    
    standings = []
    for standing_data in response['data']:
        standings.append({
            'position': standing_data['position'],
            'team': {
                'id': standing_data['team']['id'],
                'name': standing_data['team']['name'],
                'logo': standing_data['team']['logo_path']
            },
            'played': standing_data['overall']['games_played'],
            'won': standing_data['overall']['won'],
            'draw': standing_data['overall']['draw'],
            'lost': standing_data['overall']['lost'],
            'goals_for': standing_data['overall']['goals_scored'],
            'goals_against': standing_data['overall']['goals_against'],
            'goal_difference': standing_data['overall']['goals_scored'] - standing_data['overall']['goals_against'],
            'points': standing_data['overall']['points'],
            'form': standing_data.get('recent_form', ''),
            'home': {
                'played': standing_data['home']['games_played'],
                'won': standing_data['home']['won'],
                'draw': standing_data['home']['draw'],
                'lost': standing_data['home']['lost']
            },
            'away': {
                'played': standing_data['away']['games_played'],
                'won': standing_data['away']['won'],
                'draw': standing_data['away']['draw'],
                'lost': standing_data['away']['lost']
            }
        })
    
    return jsonify({
        'standings': standings,
        'league_id': league_id,
        'season_id': season_id,
        'updated_at': datetime.utcnow().isoformat()
    }), 200

@sportmonks_bp.route('/teams/<int:team_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=3600)
def get_team_details(team_id):
    """Get detailed team information including squad and recent form"""
    include_params = request.args.get('include', 'squad,venue,league,stats').split(',')
    
    # Check if API key is configured
    import os
    if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
        logger.warning("No SportMonks API key configured, returning mock team data")
        # Return mock data for testing
        mock_teams = {
            1: {  # Manchester United
                'id': 1,
                'name': 'Manchester United',
                'short_code': 'MUN',
                'logo': 'https://via.placeholder.com/50',
                'founded': 1878,
                'country': 'England',
                'venue': {
                    'name': 'Old Trafford',
                    'city': 'Manchester',
                    'capacity': 74310,
                    'image': 'https://via.placeholder.com/300x200'
                },
                'squad': [
                    {'id': 101, 'name': 'David de Gea', 'position': 'Goalkeeper', 'number': 1, 'nationality': 'Spain', 'age': 32, 'image': 'https://via.placeholder.com/50'},
                    {'id': 102, 'name': 'Harry Maguire', 'position': 'Defender', 'number': 5, 'nationality': 'England', 'age': 30, 'image': 'https://via.placeholder.com/50'},
                    {'id': 103, 'name': 'Bruno Fernandes', 'position': 'Midfielder', 'number': 8, 'nationality': 'Portugal', 'age': 28, 'image': 'https://via.placeholder.com/50'},
                    {'id': 104, 'name': 'Marcus Rashford', 'position': 'Forward', 'number': 10, 'nationality': 'England', 'age': 25, 'image': 'https://via.placeholder.com/50'}
                ]
            },
            2: {  # Liverpool
                'id': 2,
                'name': 'Liverpool',
                'short_code': 'LIV',
                'logo': 'https://via.placeholder.com/50',
                'founded': 1892,
                'country': 'England',
                'venue': {
                    'name': 'Anfield',
                    'city': 'Liverpool',
                    'capacity': 53394,
                    'image': 'https://via.placeholder.com/300x200'
                },
                'squad': [
                    {'id': 201, 'name': 'Alisson', 'position': 'Goalkeeper', 'number': 1, 'nationality': 'Brazil', 'age': 30, 'image': 'https://via.placeholder.com/50'},
                    {'id': 202, 'name': 'Virgil van Dijk', 'position': 'Defender', 'number': 4, 'nationality': 'Netherlands', 'age': 31, 'image': 'https://via.placeholder.com/50'},
                    {'id': 203, 'name': 'Mohamed Salah', 'position': 'Forward', 'number': 11, 'nationality': 'Egypt', 'age': 30, 'image': 'https://via.placeholder.com/50'}
                ]
            }
        }
        
        team_info = mock_teams.get(team_id)
        if not team_info:
            return jsonify({'error': 'Team not found'}), 404
        
        team_info['is_mock_data'] = True
        return jsonify(team_info), 200
    
    response = sportmonks_client.get_team_by_id(team_id, include=include_params)
    
    if not response or 'data' not in response:
        return jsonify({'error': 'Team not found'}), 404
    
    team_data = response['data']
    
    team_info = {
        'id': team_data['id'],
        'name': team_data['name'],
        'short_code': team_data.get('short_code'),
        'logo': team_data.get('logo_path'),
        'founded': team_data.get('founded'),
        'country': team_data.get('country', {}).get('name'),
        'venue': {
            'name': team_data.get('venue', {}).get('name'),
            'city': team_data.get('venue', {}).get('city'),
            'capacity': team_data.get('venue', {}).get('capacity'),
            'image': team_data.get('venue', {}).get('image_path')
        } if 'venue' in team_data else None,
        'squad': []
    }
    
    # Process squad if included
    if 'squad' in team_data:
        for player in team_data['squad']['data']:
            team_info['squad'].append({
                'id': player['player_id'],
                'name': player['player']['data']['display_name'],
                'position': player['position']['data']['name'],
                'number': player.get('number'),
                'nationality': player['player']['data'].get('nationality'),
                'age': player['player']['data'].get('age'),
                'image': player['player']['data'].get('image_path')
            })
    
    return jsonify(team_info), 200

@sportmonks_bp.route('/leagues', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=86400)  # Cache for 24 hours
def get_leagues():
    """Get all available leagues"""
    country = request.args.get('country')
    
    # Check if API key is configured
    import os
    if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
        logger.warning("No SportMonks API key configured, returning mock leagues")
        # Return mock data for testing
        mock_leagues = [
            {'id': 8, 'name': 'Premier League', 'country': 'England'},
            {'id': 384, 'name': 'Serie A', 'country': 'Italy'},
            {'id': 564, 'name': 'La Liga', 'country': 'Spain'},
            {'id': 82, 'name': 'Bundesliga', 'country': 'Germany'},
            {'id': 301, 'name': 'Ligue 1', 'country': 'France'}
        ]
        
        if country:
            mock_leagues = [l for l in mock_leagues if l['country'].lower() == country.lower()]
        
        return jsonify({
            'leagues': mock_leagues,
            'count': len(mock_leagues),
            'is_mock_data': True
        }), 200
    
    response = sportmonks_client.get_leagues(include=['country'])
    
    if not response or 'data' not in response:
        return jsonify({'leagues': []}), 200
    
    leagues = []
    for league_data in response['data']:
        if country and league_data.get('country', {}).get('name', '').lower() != country.lower():
            continue
            
        leagues.append({
            'id': league_data['id'],
            'name': league_data['name'],
            'country': league_data.get('country', {}).get('name')
        })
    
    return jsonify({
        'leagues': leagues,
        'count': len(leagues)
    }), 200

@sportmonks_bp.route('/odds/<int:fixture_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=300)
def get_fixture_odds(fixture_id):
    """Get odds for a fixture from various bookmakers"""
    market_id = int(request.args.get('market_id', 1))  # Default to Fulltime Result
    bookmaker_id = request.args.get('bookmaker_id')
    
    # Prepare filters
    market_ids = [market_id]
    bookmaker_ids = [int(bookmaker_id)] if bookmaker_id else None
    
    response = sportmonks_client.get_fixture_with_odds(fixture_id, market_ids=market_ids, bookmaker_ids=bookmaker_ids)
    
    if not response or 'data' not in response:
        return jsonify({'odds': {}, 'fixture': None}), 200
    
    fixture_data = response['data']
    
    # Transform fixture data
    participants = fixture_data.get('participants', [])
    home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
    away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
    
    fixture = {
        'id': fixture_data.get('id'),
        'name': fixture_data.get('name'),
        'date': fixture_data.get('starting_at'),
        'home_team': {
            'id': home_team.get('id'),
            'name': home_team.get('name'),
            'logo': home_team.get('image_path')
        },
        'away_team': {
            'id': away_team.get('id'),
            'name': away_team.get('name'),
            'logo': away_team.get('image_path')
        }
    }
    
    # Process odds
    odds_by_bookmaker = {}
    
    for odds_data in fixture_data.get('odds', []):
        bookmaker = odds_data.get('bookmaker', {})
        bookmaker_name = bookmaker.get('name', 'Unknown')
        bookmaker_id = bookmaker.get('id')
        
        if bookmaker_name not in odds_by_bookmaker:
            odds_by_bookmaker[bookmaker_name] = {
                'bookmaker_id': bookmaker_id,
                'bookmaker_name': bookmaker_name,
                'odds': []
            }
        
        odds_by_bookmaker[bookmaker_name]['odds'].append({
            'id': odds_data.get('id'),
            'label': odds_data.get('label'),
            'value': odds_data.get('value'),
            'probability': odds_data.get('probability'),
            'american': odds_data.get('american'),
            'fractional': odds_data.get('fractional'),
            'decimal': odds_data.get('dp3'),
            'winning': odds_data.get('winning', False),
            'market': odds_data.get('market', {}).get('name', 'Fulltime Result'),
            'updated_at': odds_data.get('latest_bookmaker_update', odds_data.get('updated_at'))
        })
    
    return jsonify({
        'fixture_id': fixture_id,
        'fixture': fixture,
        'odds': odds_by_bookmaker,
        'market_id': market_id,
        'updated_at': datetime.utcnow().isoformat()
    }), 200

@sportmonks_bp.route('/fixtures/round/<int:round_id>/odds', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=600)
def get_round_fixtures_with_odds(round_id):
    """Get all fixtures in a round with odds"""
    market_id = int(request.args.get('market_id', 1))  # Default to Fulltime Result
    bookmaker_id = request.args.get('bookmaker_id', 2)  # Default to bet365
    
    # Prepare filters
    market_ids = [market_id]
    bookmaker_ids = [int(bookmaker_id)] if bookmaker_id else None
    
    response = sportmonks_client.get_round_with_odds(round_id, market_ids=market_ids, bookmaker_ids=bookmaker_ids)
    
    if not response or 'data' not in response:
        return jsonify({'fixtures': [], 'round': None}), 200
    
    round_data = response['data']
    
    # Transform round data
    round_info = {
        'id': round_data.get('id'),
        'name': round_data.get('name'),
        'league': round_data.get('league', {}),
        'season_id': round_data.get('season_id'),
        'starting_at': round_data.get('starting_at'),
        'ending_at': round_data.get('ending_at'),
        'is_current': round_data.get('is_current', False)
    }
    
    # Process fixtures with odds
    fixtures_with_odds = []
    
    for fixture_data in round_data.get('fixtures', []):
        participants = fixture_data.get('participants', [])
        home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
        away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
        
        # Process odds for this fixture
        odds_list = []
        for odds_data in fixture_data.get('odds', []):
            odds_list.append({
                'id': odds_data.get('id'),
                'label': odds_data.get('label'),
                'value': odds_data.get('value'),
                'probability': odds_data.get('probability'),
                'american': odds_data.get('american'),
                'fractional': odds_data.get('fractional'),
                'decimal': odds_data.get('dp3'),
                'winning': odds_data.get('winning', False),
                'bookmaker': odds_data.get('bookmaker', {}).get('name', 'bet365'),
                'updated_at': odds_data.get('latest_bookmaker_update', odds_data.get('updated_at'))
            })
        
        fixtures_with_odds.append({
            'id': fixture_data.get('id'),
            'name': fixture_data.get('name'),
            'date': fixture_data.get('starting_at'),
            'state_id': fixture_data.get('state_id'),
            'result_info': fixture_data.get('result_info'),
            'home_team': {
                'id': home_team.get('id'),
                'name': home_team.get('name'),
                'logo': home_team.get('image_path'),
                'winner': home_team.get('meta', {}).get('winner', None)
            },
            'away_team': {
                'id': away_team.get('id'),
                'name': away_team.get('name'),
                'logo': away_team.get('image_path'),
                'winner': away_team.get('meta', {}).get('winner', None)
            },
            'odds': odds_list,
            'has_odds': fixture_data.get('has_odds', False)
        })
    
    return jsonify({
        'round': round_info,
        'fixtures': fixtures_with_odds,
        'count': len(fixtures_with_odds),
        'market_id': market_id,
        'bookmaker_id': bookmaker_id,
        'updated_at': datetime.utcnow().isoformat()
    }), 200

@sportmonks_bp.route('/search/teams', methods=['GET'])
@cross_origin()
@handle_errors
def search_teams():
    """Search for teams by name"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 3:
        return jsonify({'error': 'Search query must be at least 3 characters'}), 400
    
    response = sportmonks_client.search_teams(query)
    
    if not response or 'data' not in response:
        return jsonify({'teams': []}), 200
    
    teams = []
    for team_data in response['data']:
        teams.append({
            'id': team_data['id'],
            'name': team_data['name'],
            'logo': team_data.get('logo_path'),
            'country': team_data.get('country', {}).get('name') if 'country' in team_data else None
        })
    
    return jsonify({
        'teams': teams,
        'query': query,
        'count': len(teams)
    }), 200

@sportmonks_bp.route('/leagues/<int:league_id>/teams', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=86400)  # Cache for 24 hours
def get_league_teams(league_id):
    """Get all teams in a specific league"""
    include_params = request.args.get('include', 'venue,country').split(',')
    
    # Check if API key is configured
    import os
    if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
        logger.warning("No SportMonks API key configured, returning mock teams")
        # Return mock data for testing based on league
        mock_teams_by_league = {
            8: [  # Premier League
                {'id': 1, 'name': 'Manchester United', 'short_code': 'MUN', 'logo': 'https://via.placeholder.com/50', 'founded': 1878, 'country': 'England'},
                {'id': 2, 'name': 'Liverpool', 'short_code': 'LIV', 'logo': 'https://via.placeholder.com/50', 'founded': 1892, 'country': 'England'},
                {'id': 3, 'name': 'Chelsea', 'short_code': 'CHE', 'logo': 'https://via.placeholder.com/50', 'founded': 1905, 'country': 'England'},
                {'id': 4, 'name': 'Arsenal', 'short_code': 'ARS', 'logo': 'https://via.placeholder.com/50', 'founded': 1886, 'country': 'England'}
            ],
            384: [  # Serie A
                {'id': 5, 'name': 'Juventus', 'short_code': 'JUV', 'logo': 'https://via.placeholder.com/50', 'founded': 1897, 'country': 'Italy'},
                {'id': 6, 'name': 'AC Milan', 'short_code': 'MIL', 'logo': 'https://via.placeholder.com/50', 'founded': 1899, 'country': 'Italy'}
            ]
        }
        
        mock_teams = mock_teams_by_league.get(league_id, [])
        
        return jsonify({
            'teams': mock_teams,
            'league_id': league_id,
            'count': len(mock_teams),
            'is_mock_data': True
        }), 200
    
    response = sportmonks_client.get_teams_by_league(league_id, include=include_params)
    
    if not response or 'data' not in response:
        return jsonify({'teams': []}), 200
    
    teams = []
    for team_data in response['data']:
        team = {
            'id': team_data['id'],
            'name': team_data['name'],
            'short_code': team_data.get('short_code'),
            'logo': team_data.get('logo_path'),
            'founded': team_data.get('founded'),
            'country': team_data.get('country', {}).get('name') if 'country' in team_data else None
        }
        
        if 'venue' in team_data and team_data['venue']:
            team['venue'] = {
                'name': team_data['venue'].get('name'),
                'city': team_data['venue'].get('city'),
                'capacity': team_data['venue'].get('capacity')
            }
        
        teams.append(team)
    
    return jsonify({
        'teams': teams,
        'league_id': league_id,
        'count': len(teams)
    }), 200

@sportmonks_bp.route('/fixtures/<int:fixture_id>/h2h', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=3600)
def get_head_to_head(fixture_id):
    """Get head-to-head statistics for teams in a fixture"""
    # First get the fixture to know the teams
    fixture_response = sportmonks_client.get_fixture_by_id(
        fixture_id, 
        include=['localTeam', 'visitorTeam']
    )
    
    if not fixture_response or 'data' not in fixture_response:
        return jsonify({'error': 'Fixture not found'}), 404
    
    fixture_data = fixture_response['data']
    home_team_id = fixture_data['localteam_id']
    away_team_id = fixture_data['visitorteam_id']
    
    # Get H2H data
    h2h_response = sportmonks_client.get_h2h([home_team_id, away_team_id])
    
    if not h2h_response or 'data' not in h2h_response:
        return jsonify({'h2h': []}), 200
    
    # Process H2H matches
    h2h_matches = []
    home_wins = 0
    away_wins = 0
    draws = 0
    
    for match in h2h_response['data']:
        is_home_team = match['localteam_id'] == home_team_id
        home_score = match['scores']['localteam_score']
        away_score = match['scores']['visitorteam_score']
        
        if home_score > away_score:
            if is_home_team:
                home_wins += 1
            else:
                away_wins += 1
        elif away_score > home_score:
            if is_home_team:
                away_wins += 1
            else:
                home_wins += 1
        else:
            draws += 1
        
        h2h_matches.append({
            'date': match['starting_at'],
            'home_team': match['localTeam']['data']['name'],
            'away_team': match['visitorTeam']['data']['name'],
            'score': f"{home_score}-{away_score}",
            'venue': match.get('venue', {}).get('data', {}).get('name')
        })
    
    return jsonify({
        'fixture_id': fixture_id,
        'summary': {
            'total_matches': len(h2h_matches),
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws
        },
        'matches': h2h_matches[:10],  # Last 10 matches
        'home_team': fixture_data['localTeam']['data']['name'],
        'away_team': fixture_data['visitorTeam']['data']['name']
    }), 200

@sportmonks_bp.route('/schedules/teams/<int:team_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=600)
def get_team_schedule(team_id):
    """Get the complete schedule for a specific team"""
    include_params = request.args.get('include', 'localTeam,visitorTeam,league,venue,stage,round').split(',')
    
    # Check if API key is configured
    import os
    if not os.getenv('SPORTMONKS_API_KEY'):
        # Return mock data if no API key
        current_date = datetime.now()
        mock_fixtures = []
        
        # Generate some mock upcoming fixtures
        for i in range(5):
            fixture_date = current_date + timedelta(days=i*7)
            mock_fixtures.append({
                'id': 10000 + i,
                'league_id': 501,
                'league': {'name': 'Premier League'},
                'round': f'Round {i+25}',
                'stage_id': 1,
                'localteam_id': team_id if i % 2 == 0 else 502 + i,
                'visitorteam_id': 502 + i if i % 2 == 0 else team_id,
                'localTeam': {'name': 'Team Home', 'logo_path': None},
                'visitorTeam': {'name': 'Team Away', 'logo_path': None},
                'starting_at': fixture_date.isoformat(),
                'venue': {'name': 'Stadium Name'},
                'status': 'NS'
            })
        
        return jsonify({
            'fixtures': mock_fixtures,
            'count': len(mock_fixtures),
            'is_mock_data': True
        }), 200
    
    # Get real data from SportMonks API
    response = sportmonks_client.get(f'schedules/teams/{team_id}', include=include_params)
    
    if not response or 'data' not in response:
        return jsonify({'error': 'Failed to fetch team schedule'}), 500
    
    fixtures = []
    for fixture in response['data']:
        fixtures.append({
            'id': fixture['id'],
            'league_id': fixture['league_id'],
            'league': fixture.get('league', {}).get('data', {}) if 'league' in fixture else None,
            'round': fixture.get('round'),
            'stage_id': fixture.get('stage_id'),
            'localteam_id': fixture['localteam_id'],
            'visitorteam_id': fixture['visitorteam_id'],
            'localTeam': fixture.get('localTeam', {}).get('data', {}) if 'localTeam' in fixture else None,
            'visitorTeam': fixture.get('visitorTeam', {}).get('data', {}) if 'visitorTeam' in fixture else None,
            'starting_at': fixture['time']['starting_at']['date_time'],
            'venue': fixture.get('venue', {}).get('data', {}) if 'venue' in fixture else None,
            'status': fixture['time']['status']
        })
    
    return jsonify({
        'fixtures': fixtures,
        'count': len(fixtures)
    }), 200

@sportmonks_bp.route('/schedules/seasons/<int:season_id>/teams/<int:team_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=600)
def get_team_season_schedule(season_id, team_id):
    """Get the schedule for a specific team in a specific season"""
    include_params = request.args.get('include', 'localTeam,visitorTeam,league,venue,stage,round').split(',')
    
    # Check if API key is configured
    import os
    if not os.getenv('SPORTMONKS_API_KEY'):
        # Return mock data if no API key
        return jsonify({
            'fixtures': [],
            'count': 0,
            'is_mock_data': True,
            'message': 'Configure SportMonks API key to get real season schedule data'
        }), 200
    
    # Get real data from SportMonks API
    response = sportmonks_client.get(f'schedules/seasons/{season_id}/teams/{team_id}', include=include_params)
    
    if not response or 'data' not in response:
        return jsonify({'error': 'Failed to fetch team season schedule'}), 500
    
    fixtures = []
    for fixture in response['data']:
        fixtures.append({
            'id': fixture['id'],
            'league_id': fixture['league_id'],
            'league': fixture.get('league', {}).get('data', {}) if 'league' in fixture else None,
            'round': fixture.get('round'),
            'stage_id': fixture.get('stage_id'),
            'localteam_id': fixture['localteam_id'],
            'visitorteam_id': fixture['visitorteam_id'],
            'localTeam': fixture.get('localTeam', {}).get('data', {}) if 'localTeam' in fixture else None,
            'visitorTeam': fixture.get('visitorTeam', {}).get('data', {}) if 'visitorTeam' in fixture else None,
            'starting_at': fixture['time']['starting_at']['date_time'],
            'venue': fixture.get('venue', {}).get('data', {}) if 'venue' in fixture else None,
            'status': fixture['time']['status']
        })
    
    return jsonify({
        'fixtures': fixtures,
        'count': len(fixtures),
        'season_id': season_id
    }), 200

@sportmonks_bp.route('/fixtures/between/<start_date>/<end_date>/<int:team_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=300)
def get_team_fixtures_between_dates(start_date, end_date, team_id):
    """Get fixtures for a specific team between two dates"""
    include_params = request.args.get('include', 'localTeam,visitorTeam,league,venue,stage,round').split(',')
    
    # Validate date format
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        if end_dt < start_dt:
            return jsonify({'error': 'End date must be after start date'}), 400
            
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Check if API key is configured
    import os
    if not os.getenv('SPORTMONKS_API_KEY'):
        # Return mock data if no API key
        mock_fixtures = []
        current_date = start_dt
        fixture_id = 20000
        
        while current_date <= end_dt:
            if current_date.weekday() in [5, 6]:  # Weekend fixtures
                mock_fixtures.append({
                    'id': fixture_id,
                    'league_id': 501,
                    'league': {'name': 'Premier League'},
                    'round': 'Round X',
                    'localteam_id': team_id if fixture_id % 2 == 0 else 502,
                    'visitorteam_id': 502 if fixture_id % 2 == 0 else team_id,
                    'localTeam': {'name': 'Home Team', 'logo_path': None},
                    'visitorTeam': {'name': 'Away Team', 'logo_path': None},
                    'starting_at': current_date.isoformat(),
                    'venue': {'name': 'Stadium'},
                    'status': 'NS' if current_date > datetime.now() else 'FT'
                })
                fixture_id += 1
            current_date += timedelta(days=1)
        
        return jsonify({
            'fixtures': mock_fixtures,
            'count': len(mock_fixtures),
            'is_mock_data': True,
            'period': {
                'start': start_date,
                'end': end_date
            }
        }), 200
    
    # Get real data from SportMonks API
    response = sportmonks_client.get(
        f'fixtures/between/{start_date}/{end_date}/{team_id}',
        include=include_params
    )
    
    if not response or 'data' not in response:
        return jsonify({'error': 'Failed to fetch fixtures between dates'}), 500
    
    fixtures = []
    for fixture in response['data']:
        fixtures.append({
            'id': fixture['id'],
            'league_id': fixture['league_id'],
            'league': fixture.get('league', {}).get('data', {}) if 'league' in fixture else None,
            'round': fixture.get('round'),
            'stage_id': fixture.get('stage_id'),
            'localteam_id': fixture['localteam_id'],
            'visitorteam_id': fixture['visitorteam_id'],
            'localTeam': fixture.get('localTeam', {}).get('data', {}) if 'localTeam' in fixture else None,
            'visitorTeam': fixture.get('visitorTeam', {}).get('data', {}) if 'visitorTeam' in fixture else None,
            'starting_at': fixture['time']['starting_at']['date_time'],
            'venue': fixture.get('venue', {}).get('data', {}) if 'venue' in fixture else None,
            'status': fixture['time']['status']
        })
    
    return jsonify({
        'fixtures': fixtures,
        'count': len(fixtures),
        'period': {
            'start': start_date,
            'end': end_date
        }
    }), 200

@sportmonks_bp.route('/squad/<int:team_id>', methods=['GET'])
@cross_origin()
@handle_errors
@cache_response(timeout=3600)  # Cache for 1 hour
def get_team_squad(team_id):
    """Get squad/players data for a specific team"""
    try:
        season_id = request.args.get('season_id')
        
        logger.info(f"Fetching squad data for team {team_id}")
        
        # Check if API key is configured
        import os
        if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
            logger.warning("No SportMonks API key configured, returning mock squad data")
            # Return mock data for testing
            mock_squad = {
                'team': {
                    'id': team_id,
                    'name': 'Manchester United',
                    'logo': 'https://via.placeholder.com/100'
                },
                'players': [
                    {
                        'id': 1,
                        'name': 'Marcus Rashford',
                        'position': 'Forward',
                        'number': 10,
                        'nationality': 'England',
                        'age': 26,
                        'photo': 'https://via.placeholder.com/50'
                    },
                    {
                        'id': 2,
                        'name': 'Bruno Fernandes',
                        'position': 'Midfielder',
                        'number': 8,
                        'nationality': 'Portugal',
                        'age': 29,
                        'photo': 'https://via.placeholder.com/50'
                    },
                    {
                        'id': 3,
                        'name': 'Harry Maguire',
                        'position': 'Defender',
                        'number': 5,
                        'nationality': 'England',
                        'age': 31,
                        'photo': 'https://via.placeholder.com/50'
                    }
                ],
                'coach': {
                    'id': 100,
                    'name': 'Erik ten Hag',
                    'nationality': 'Netherlands',
                    'photo': 'https://via.placeholder.com/50'
                },
                'is_mock_data': True
            }
            return jsonify(mock_squad), 200
        
        # Get team data with squad
        include_params = ['squad.player', 'coach']
        if season_id:
            include_params.append(f'squad:season:{season_id}')
        
        team_data = sportmonks_client.get_team_by_id(
            team_id=team_id,
            include=include_params
        )
        
        if not team_data:
            return jsonify({'error': 'Team not found'}), 404
        
        # Process squad data
        squad_data = {
            'team': {
                'id': team_data.get('id'),
                'name': team_data.get('name'),
                'logo': team_data.get('logo_path'),
                'founded': team_data.get('founded'),
                'venue': team_data.get('venue', {}).get('data', {}) if 'venue' in team_data else None
            },
            'players': [],
            'coach': None
        }
        
        # Process players
        if 'squad' in team_data and 'data' in team_data['squad']:
            for squad_member in team_data['squad']['data']:
                player_info = squad_member.get('player', {}).get('data', {}) if 'player' in squad_member else {}
                player = {
                    'id': player_info.get('id') or squad_member.get('player_id'),
                    'name': player_info.get('display_name') or player_info.get('fullname') or 'Unknown',
                    'position': squad_member.get('position', {}).get('data', {}).get('name') if isinstance(squad_member.get('position'), dict) else squad_member.get('position'),
                    'number': squad_member.get('number'),
                    'nationality': player_info.get('nationality'),
                    'age': calculate_age(player_info.get('birthdate')) if player_info.get('birthdate') else None,
                    'photo': player_info.get('image_path'),
                    'injured': squad_member.get('injured', False),
                    'minutes': squad_member.get('minutes', 0),
                    'appearances': squad_member.get('appearences', 0),
                    'goals': squad_member.get('goals', 0),
                    'assists': squad_member.get('assists', 0)
                }
                squad_data['players'].append(player)
        
        # Process coach
        if 'coach' in team_data and 'data' in team_data['coach']:
            coach_info = team_data['coach']['data']
            squad_data['coach'] = {
                'id': coach_info.get('id'),
                'name': coach_info.get('fullname') or coach_info.get('common_name'),
                'nationality': coach_info.get('nationality'),
                'photo': coach_info.get('image_path'),
                'birthdate': coach_info.get('birthdate')
            }
        
        # Sort players by position and number
        position_order = {'Goalkeeper': 1, 'Defender': 2, 'Midfielder': 3, 'Forward': 4}
        squad_data['players'].sort(key=lambda x: (
            position_order.get(x.get('position', ''), 5),
            x.get('number', 999)
        ))
        
        logger.info(f"Retrieved squad with {len(squad_data['players'])} players for team {team_id}")
        
        return jsonify(squad_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching squad data: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to fetch squad data',
            'message': str(e)
        }), 500

def calculate_age(birthdate_str):
    """Calculate age from birthdate string"""
    if not birthdate_str:
        return None
    try:
        birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age
    except:
        return None