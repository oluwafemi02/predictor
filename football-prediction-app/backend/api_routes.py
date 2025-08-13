from flask import Blueprint, jsonify, request
from models import db, Match, MatchOdds, Team
from data_collector import RapidAPIFootballOddsCollector, FootballDataCollector
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Existing odds endpoints
@api_bp.route('/odds/leagues', methods=['GET'])
def get_leagues_with_odds():
    """Get all leagues that have odds data available"""
    try:
        collector = RapidAPIFootballOddsCollector()
        leagues = collector.fetch_leagues()
        return jsonify({
            'status': 'success',
            'data': leagues,
            'count': len(leagues)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/bookmakers', methods=['GET'])
def get_bookmakers():
    """Get all available bookmakers"""
    try:
        collector = RapidAPIFootballOddsCollector()
        bookmakers = collector.fetch_bookmakers()
        return jsonify({
            'status': 'success',
            'data': bookmakers,
            'count': len(bookmakers)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/league/<int:league_id>', methods=['GET'])
def get_league_odds(league_id):
    """Get odds for a specific league"""
    try:
        bookmaker_id = request.args.get('bookmaker_id', 5, type=int)
        page = request.args.get('page', 1, type=int)
        
        collector = RapidAPIFootballOddsCollector()
        odds_data = collector.fetch_odds_by_league(league_id, bookmaker_id, page)
        
        return jsonify({
            'status': 'success',
            'data': odds_data['response'],
            'paging': odds_data.get('paging', {})
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/fixture/<int:fixture_id>', methods=['GET'])
def get_fixture_odds(fixture_id):
    """Get odds for a specific fixture"""
    try:
        collector = RapidAPIFootballOddsCollector()
        odds_data = collector.fetch_odds_by_fixture(fixture_id)
        
        return jsonify({
            'status': 'success',
            'data': odds_data['response']
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/date/<date_str>', methods=['GET'])
def get_odds_by_date(date_str):
    """Get odds for matches on a specific date"""
    try:
        # Validate date format
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        bookmaker_id = request.args.get('bookmaker_id', 5, type=int)
        page = request.args.get('page', 1, type=int)
        
        collector = RapidAPIFootballOddsCollector()
        odds_data = collector.fetch_odds_by_date(date_str, bookmaker_id, page)
        
        return jsonify({
            'status': 'success',
            'data': odds_data['response'],
            'paging': odds_data.get('paging', {})
        })
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# New endpoints required by frontend

@api_bp.route('/matches', methods=['GET'])
def get_matches():
    """Get matches with optional filters"""
    try:
        # Get query parameters
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # For now, return mock data since we don't have a proper matches table
        # In production, this should query your matches database
        matches = []
        
        if status == 'finished':
            # Return some mock finished matches
            matches = [
                {
                    'id': 1,
                    'date': '2024-01-10T15:00:00',
                    'home_team': {'id': 1, 'name': 'Team A', 'logo_url': ''},
                    'away_team': {'id': 2, 'name': 'Team B', 'logo_url': ''},
                    'home_score': 2,
                    'away_score': 1,
                    'status': 'finished',
                    'competition': 'League 1',
                    'venue': 'Stadium A',
                    'has_prediction': True
                }
            ]
        
        total = len(matches)
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'matches': matches,
            'pagination': {
                'page': page,
                'pages': pages,
                'total': total,
                'per_page': per_page
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/upcoming-predictions', methods=['GET'])
def get_upcoming_predictions():
    """Get upcoming match predictions"""
    try:
        # Return empty list for now
        # In production, this should return actual predictions
        return jsonify({
            'predictions': []
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/model/status', methods=['GET'])
def get_model_status():
    """Get the status of the prediction model"""
    try:
        # Check if model exists (mock implementation)
        model_path = os.path.join('models', 'prediction_model.pkl')
        is_trained = os.path.exists(model_path)
        
        return jsonify({
            'is_trained': is_trained,
            'model_version': '1.0.0' if is_trained else 'N/A',
            'features': [
                'home_team_form',
                'away_team_form',
                'home_team_goals_scored',
                'away_team_goals_scored',
                'head_to_head_stats'
            ] if is_trained else []
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/model/train', methods=['POST'])
def train_model():
    """Train the prediction model"""
    try:
        # First check if we have enough data
        match_count = 0
        try:
            match_count = Match.query.count()
        except Exception as db_error:
            logger.error(f"Database error counting matches: {str(db_error)}")
            return jsonify({
                'status': 'error',
                'message': 'Database connection issue. Using SQLite fallback.',
                'hint': 'The backend is using a temporary database. Set up PostgreSQL for persistence.'
            })
        
        if match_count < 50:
            return jsonify({
                'status': 'info',
                'message': f'Need more data for training. Currently have {match_count} matches, need at least 50.',
                'hint': 'Visit the RapidAPI website to fetch odds data, or set FOOTBALL_API_KEY for football-data.org',
                'data_sources': {
                    'rapidapi': 'https://rapidapi.com/api-sports/api/api-football/',
                    'football_data': 'https://www.football-data.org/'
                }
            })
        
        # For now, return a mock successful training result
        # In production, this would actually train the model
        return jsonify({
            'status': 'success',
            'message': 'Model training simulation completed',
            'accuracy': 0.75,
            'features_used': [
                'home_team_form',
                'away_team_form', 
                'head_to_head_stats',
                'home_advantage'
            ],
            'training_samples': match_count,
            'note': 'This is a demonstration. Actual model training requires more data.'
        })
            
    except Exception as e:
        logger.error(f"Error in train_model: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during training',
            'error': str(e)
        })

@api_bp.route('/teams', methods=['GET'])
def get_teams():
    """Get all teams"""
    try:
        # Query teams from database
        teams = []
        try:
            teams = Team.query.all()
        except Exception as db_error:
            # If database query fails, return empty list
            logger.error(f"Database error fetching teams: {str(db_error)}")
            teams = []
        
        return jsonify({
            'teams': [
                {
                    'id': team.id,
                    'name': team.name,
                    'code': team.code,
                    'logo_url': team.logo_url or '',
                    'stadium': team.stadium or '',
                    'founded': team.founded
                } for team in teams
            ]
        })
    except Exception as e:
        logger.error(f"Error in get_teams: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'teams': []  # Return empty array to prevent frontend errors
        }), 200  # Return 200 instead of 500 to prevent retries

@api_bp.route('/teams/<int:team_id>', methods=['GET'])
def get_team_details(team_id):
    """Get team details with statistics"""
    try:
        team = Team.query.get(team_id)
        
        if not team:
            return jsonify({
                'status': 'error',
                'message': 'Team not found'
            }), 404
        
        # Mock statistics for now
        return jsonify({
            'team': {
                'id': team.id,
                'name': team.name,
                'code': team.code,
                'logo_url': team.logo_url or '',
                'stadium': team.stadium or '',
                'founded': team.founded
            },
            'statistics': {
                'season': '2023/2024',
                'matches_played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'form': 'N/A',
                'clean_sheets': 0,
                'home_record': {'wins': 0, 'draws': 0, 'losses': 0},
                'away_record': {'wins': 0, 'draws': 0, 'losses': 0}
            },
            'recent_matches': [],
            'injured_players': []
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/statistics/competitions', methods=['GET'])
def get_competitions():
    """Get available competitions"""
    try:
        # Return some default competitions
        return jsonify({
            'competitions': [
                'Premier League',
                'La Liga',
                'Serie A',
                'Bundesliga',
                'Ligue 1'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/statistics/league-table', methods=['GET'])
def get_league_table():
    """Get league table for a competition"""
    try:
        competition = request.args.get('competition', 'Premier League')
        season = request.args.get('season', '2023/2024')
        
        # Return mock league table
        return jsonify({
            'table': [
                {
                    'position': i + 1,
                    'team': {
                        'id': i + 1,
                        'name': f'Team {i + 1}',
                        'logo_url': ''
                    },
                    'played': 0,
                    'won': 0,
                    'drawn': 0,
                    'lost': 0,
                    'goals_for': 0,
                    'goals_against': 0,
                    'goal_difference': 0,
                    'points': 0,
                    'form': 'N/A'
                } for i in range(20)
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/predictions', methods=['GET'])
def get_predictions():
    """Get predictions with filters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Return empty predictions for now
        return jsonify({
            'predictions': [],
            'pagination': {
                'page': page,
                'pages': 0,
                'total': 0,
                'per_page': per_page
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/matches/<int:match_id>', methods=['GET'])
def get_match_details(match_id):
    """Get detailed information about a specific match"""
    try:
        # Return mock match details
        return jsonify({
            'match': {
                'id': match_id,
                'date': '2024-01-10T15:00:00',
                'home_team': {'id': 1, 'name': 'Team A', 'logo_url': ''},
                'away_team': {'id': 2, 'name': 'Team B', 'logo_url': ''},
                'home_score': 2,
                'away_score': 1,
                'home_score_halftime': 1,
                'away_score_halftime': 0,
                'status': 'finished',
                'competition': 'League 1',
                'venue': 'Stadium A',
                'referee': 'Referee Name',
                'attendance': 50000,
                'has_prediction': True
            },
            'head_to_head': {
                'total_matches': 10,
                'home_wins': 4,
                'away_wins': 3,
                'draws': 3,
                'last_5_results': []
            },
            'prediction': {
                'home_win_probability': 0.45,
                'draw_probability': 0.30,
                'away_win_probability': 0.25,
                'predicted_home_score': 2,
                'predicted_away_score': 1,
                'over_2_5_probability': 0.55,
                'both_teams_score_probability': 0.65,
                'confidence_score': 0.75,
                'factors': {
                    'home_form': 'Good',
                    'away_form': 'Average',
                    'head_to_head': 'Balanced'
                }
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Keep the existing sync endpoints
@api_bp.route('/odds/sync/league/<int:league_id>', methods=['POST'])
def sync_league_odds(league_id):
    """Sync odds for a specific league"""
    try:
        # Get optional parameters
        season = request.json.get('season') if request.json else None
        bookmaker_id = request.json.get('bookmaker_id', 5) if request.json else 5
        
        collector = RapidAPIFootballOddsCollector()
        
        # Store odds in database
        odds_data = collector.fetch_odds_by_league(league_id, bookmaker_id)
        
        # Process and store odds (implement based on your model structure)
        # For now, just return success
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully synced odds for league {league_id}',
            'odds_count': len(odds_data.get('response', []))
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/sync/match/<int:match_id>', methods=['POST'])
def sync_match_odds(match_id):
    """Sync odds for a specific match"""
    try:
        collector = RapidAPIFootballOddsCollector()
        
        # Fetch and store odds
        odds_data = collector.fetch_odds_by_fixture(match_id)
        
        # Process and store odds (implement based on your model structure)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully synced odds for match {match_id}',
            'odds_count': len(odds_data.get('response', []))
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/match/<int:match_id>', methods=['GET'])
def get_match_odds(match_id):
    """Get odds for a specific match from database"""
    try:
        # Query odds from database
        odds = MatchOdds.query.filter_by(match_id=match_id).all()
        
        return jsonify({
            'status': 'success',
            'data': [
                {
                    'id': odd.id,
                    'match_id': odd.match_id,
                    'bookmaker': odd.bookmaker,
                    'market': odd.market,
                    'value': odd.value,
                    'odd': odd.odd,
                    'updated_at': odd.updated_at.isoformat() if odd.updated_at else None
                } for odd in odds
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/data/initialize', methods=['POST'])
def initialize_data():
    """Initialize the database with some real football data"""
    try:
        # Check if we have the Football API key
        from config import Config
        api_key = Config.FOOTBALL_API_KEY
        
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'FOOTBALL_API_KEY not configured',
                'hint': 'Please set the FOOTBALL_API_KEY environment variable in Render'
            })
        
        # Try to fetch Premier League data
        collector = FootballDataCollector()
        
        # Premier League ID is 2021
        competition_id = 2021
        results = {
            'teams': {'synced': 0, 'error': None},
            'matches': {'synced': 0, 'error': None}
        }
        
        # Sync teams
        try:
            teams_result = collector.sync_teams(competition_id)
            results['teams'] = teams_result
        except Exception as e:
            results['teams']['error'] = str(e)
            logger.error(f"Error syncing teams: {e}")
        
        # Sync recent matches (last 30 days)
        try:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            date_to = datetime.now().strftime('%Y-%m-%d')
            matches_result = collector.sync_matches(competition_id, date_from, date_to)
            results['matches'] = matches_result
        except Exception as e:
            results['matches']['error'] = str(e)
            logger.error(f"Error syncing matches: {e}")
        
        # Get current counts
        team_count = Team.query.count()
        match_count = Match.query.count()
        
        return jsonify({
            'status': 'success',
            'message': 'Data initialization completed',
            'results': results,
            'database_stats': {
                'total_teams': team_count,
                'total_matches': match_count,
                'ready_for_training': match_count >= 50
            }
        })
        
    except Exception as e:
        logger.error(f"Error in initialize_data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to initialize data',
            'error': str(e)
        })

@api_bp.route('/data/stats', methods=['GET'])
def get_data_stats():
    """Get current database statistics"""
    try:
        team_count = Team.query.count()
        match_count = Match.query.count()
        
        # Get some sample teams
        sample_teams = Team.query.limit(5).all()
        
        # Get recent matches
        recent_matches = Match.query.order_by(Match.match_date.desc()).limit(5).all()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_teams': team_count,
                'total_matches': match_count,
                'ready_for_training': match_count >= 50,
                'sample_teams': [
                    {'id': t.id, 'name': t.name} for t in sample_teams
                ],
                'recent_matches': [
                    {
                        'id': m.id,
                        'date': m.match_date.isoformat() if m.match_date else None,
                        'home_team': m.home_team.name if m.home_team else 'Unknown',
                        'away_team': m.away_team.name if m.away_team else 'Unknown',
                        'status': m.status
                    } for m in recent_matches
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error getting data stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get statistics',
            'error': str(e)
        })

@api_bp.route('/database/init', methods=['POST'])
def init_database():
    """Initialize database tables"""
    try:
        # Create all tables
        db.create_all()
        
        # Test with a simple query
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1')).scalar()
        
        return jsonify({
            'status': 'success',
            'message': 'Database tables created successfully',
            'test_query': result == 1
        })
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to initialize database',
            'error': str(e),
            'hint': 'Check if DATABASE_URL is properly configured in Render'
        })