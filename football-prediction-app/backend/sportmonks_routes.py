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

logger = logging.getLogger(__name__)

# Create Blueprint
sportmonks_bp = Blueprint('sportmonks', __name__, url_prefix='/api/sportmonks')

# Initialize SportMonks client
sportmonks_client = SportMonksAPIClient()

# Cache decorator
def cache_response(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # For now, just call the function
            # In production, implement proper caching
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Error handler decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'An error occurred processing your request',
                'message': str(e)
            }), 500
    return decorated_function

# Routes

@sportmonks_bp.route('/health', methods=['GET'])
@cross_origin()
@handle_errors
def health_check():
    """Check SportMonks API health and configuration"""
    health_status = sportmonks_client.health_check()
    return jsonify(health_status), 200

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
    days_ahead = int(request.args.get('days', 7))
    league_id = request.args.get('league_id')
    include_predictions = request.args.get('predictions', 'true').lower() == 'true'
    
    start_date = datetime.utcnow().strftime('%Y-%m-%d')
    end_date = (datetime.utcnow() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    # Get fixtures from API
    league_ids = [int(league_id)] if league_id else None
    include_params = ['localTeam', 'visitorTeam', 'league', 'venue']
    
    fixtures = sportmonks_client.get_fixtures_by_date_range(
        start_date=start_date,
        end_date=end_date,
        league_ids=league_ids,
        include=include_params
    )
    
    # Process fixtures and add predictions if requested
    processed_fixtures = []
    for fixture_data in fixtures:
        fixture = {
            'id': fixture_data['id'],
            'date': fixture_data['starting_at'],
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
            'venue': fixture_data.get('venue', {})
        }
        
        # Add predictions if requested
        if include_predictions:
            prediction_response = sportmonks_client.get_predictions_by_fixture(fixture_data['id'])
            if prediction_response and 'data' in prediction_response:
                prediction_data = prediction_response['data']
                fixture['predictions'] = {
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
        
        processed_fixtures.append(fixture)
    
    return jsonify({
        'fixtures': processed_fixtures,
        'count': len(processed_fixtures),
        'date_range': {
            'start': start_date,
            'end': end_date
        }
    }), 200

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
    include_params = request.args.get('include', 'country').split(',')
    
    response = sportmonks_client.get_leagues(include=include_params)
    
    if not response or 'data' not in response:
        return jsonify({'leagues': []}), 200
    
    leagues = []
    for league_data in response['data']:
        if country and league_data.get('country', {}).get('name', '').lower() != country.lower():
            continue
        
        leagues.append({
            'id': league_data['id'],
            'name': league_data['name'],
            'type': league_data.get('type'),
            'logo': league_data.get('logo_path'),
            'country': league_data.get('country', {}).get('name') if 'country' in league_data else None,
            'is_cup': league_data.get('is_cup', False),
            'active': league_data.get('active', True)
        })
    
    # Sort by country and name
    leagues.sort(key=lambda x: (x.get('country', ''), x['name']))
    
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
    bookmaker_id = request.args.get('bookmaker_id')
    
    response = sportmonks_client.get_odds_by_fixture(fixture_id, bookmaker_id=bookmaker_id)
    
    if not response or 'data' not in response:
        return jsonify({'odds': []}), 200
    
    odds_by_market = {}
    
    for odds_data in response['data']:
        market = odds_data['name']
        if market not in odds_by_market:
            odds_by_market[market] = []
        
        odds_by_market[market].append({
            'bookmaker': odds_data['bookmaker']['data']['name'],
            'bookmaker_id': odds_data['bookmaker']['data']['id'],
            'odds': odds_data['odds']['data'],
            'last_updated': odds_data['updated_at']
        })
    
    return jsonify({
        'fixture_id': fixture_id,
        'odds': odds_by_market,
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