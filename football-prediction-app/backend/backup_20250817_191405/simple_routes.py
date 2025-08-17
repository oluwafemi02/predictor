from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sportmonks_api_v3 import SportMonksV3Client
from simple_prediction_engine import SimplePredictionEngine
import logging
import os

logger = logging.getLogger(__name__)

# Create Blueprint
simple_bp = Blueprint('simple', __name__, url_prefix='/api/v2')

# Initialize clients
try:
    client = SportMonksV3Client()
    prediction_engine = SimplePredictionEngine()
    api_available = True
except Exception as e:
    logger.error(f"Failed to initialize SportMonks client: {str(e)}")
    client = None
    prediction_engine = None
    api_available = False

@simple_bp.route('/health', methods=['GET'])
def health_check():
    """Check API health status"""
    return jsonify({
        'status': 'healthy' if api_available else 'unhealthy',
        'api_configured': bool(os.environ.get('SPORTMONKS_API_KEY') or os.environ.get('SPORTMONKS_PRIMARY_TOKEN')),
        'timestamp': datetime.utcnow().isoformat()
    })

@simple_bp.route('/fixtures/today', methods=['GET'])
def get_todays_fixtures():
    """Get today's fixtures with predictions"""
    if not api_available:
        return jsonify({'error': 'API not available', 'fixtures': []}), 503
    
    try:
        # Get fixtures
        fixtures_data = client.get_todays_fixtures()
        
        if not fixtures_data or 'data' not in fixtures_data:
            return jsonify({'fixtures': [], 'message': 'No fixtures found for today'})
        
        fixtures = fixtures_data['data']
        
        # Format response
        formatted_fixtures = []
        for fixture in fixtures:
            formatted = _format_fixture(fixture)
            
            # Add prediction if fixture hasn't started
            if fixture.get('state_id') in [1, 2]:  # Not started or in play
                try:
                    prediction = prediction_engine.analyze_fixture(fixture['id'])
                    if prediction:
                        formatted['prediction'] = {
                            'home_win': prediction.home_win_probability,
                            'draw': prediction.draw_probability,
                            'away_win': prediction.away_win_probability,
                            'predicted_outcome': prediction.predicted_outcome,
                            'predicted_score': f"{prediction.predicted_score[0]}-{prediction.predicted_score[1]}",
                            'confidence': prediction.confidence,
                            'reasoning': prediction.reasoning
                        }
                except Exception as e:
                    logger.error(f"Error getting prediction for fixture {fixture['id']}: {str(e)}")
            
            formatted_fixtures.append(formatted)
        
        return jsonify({
            'fixtures': formatted_fixtures,
            'count': len(formatted_fixtures),
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        logger.error(f"Error getting today's fixtures: {str(e)}")
        return jsonify({'error': 'Failed to fetch fixtures', 'fixtures': []}), 500

@simple_bp.route('/fixtures/upcoming', methods=['GET'])
def get_upcoming_fixtures():
    """Get upcoming fixtures with optional predictions"""
    if not api_available:
        return jsonify({'error': 'API not available', 'fixtures': []}), 503
    
    try:
        days = int(request.args.get('days', 7))
        include_predictions = request.args.get('predictions', 'true').lower() == 'true'
        
        # Get fixtures
        fixtures_data = client.get_upcoming_fixtures(days=days)
        
        if not fixtures_data or 'data' not in fixtures_data:
            return jsonify({'fixtures': [], 'message': 'No upcoming fixtures found'})
        
        fixtures = fixtures_data['data']
        
        # Format response
        formatted_fixtures = []
        for fixture in fixtures:
            formatted = _format_fixture(fixture)
            
            # Add prediction if requested
            if include_predictions and fixture.get('state_id') == 1:  # Not started
                try:
                    prediction = prediction_engine.analyze_fixture(fixture['id'])
                    if prediction:
                        formatted['prediction'] = {
                            'home_win': prediction.home_win_probability,
                            'draw': prediction.draw_probability,
                            'away_win': prediction.away_win_probability,
                            'predicted_outcome': prediction.predicted_outcome,
                            'predicted_score': f"{prediction.predicted_score[0]}-{prediction.predicted_score[1]}",
                            'confidence': prediction.confidence,
                            'reasoning': prediction.reasoning
                        }
                except Exception as e:
                    logger.error(f"Error getting prediction for fixture {fixture['id']}: {str(e)}")
            
            formatted_fixtures.append(formatted)
        
        return jsonify({
            'fixtures': formatted_fixtures,
            'count': len(formatted_fixtures),
            'date_range': {
                'start': datetime.now().strftime('%Y-%m-%d'),
                'end': (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting upcoming fixtures: {str(e)}")
        return jsonify({'error': 'Failed to fetch fixtures', 'fixtures': []}), 500

@simple_bp.route('/fixtures/past', methods=['GET'])
def get_past_fixtures():
    """Get past fixtures with results"""
    if not api_available:
        return jsonify({'error': 'API not available', 'fixtures': []}), 503
    
    try:
        days = int(request.args.get('days', 7))
        
        # Get fixtures
        fixtures_data = client.get_past_fixtures(days=days)
        
        if not fixtures_data or 'data' not in fixtures_data:
            return jsonify({'fixtures': [], 'message': 'No past fixtures found'})
        
        fixtures = fixtures_data['data']
        
        # Format response
        formatted_fixtures = []
        for fixture in fixtures:
            formatted = _format_fixture(fixture)
            formatted_fixtures.append(formatted)
        
        return jsonify({
            'fixtures': formatted_fixtures,
            'count': len(formatted_fixtures),
            'date_range': {
                'start': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting past fixtures: {str(e)}")
        return jsonify({'error': 'Failed to fetch fixtures', 'fixtures': []}), 500

@simple_bp.route('/fixtures/<int:fixture_id>', methods=['GET'])
def get_fixture_details(fixture_id):
    """Get detailed information about a specific fixture"""
    if not api_available:
        return jsonify({'error': 'API not available'}), 503
    
    try:
        # Get fixture with full details
        fixture_data = client.get_fixture_by_id(
            fixture_id,
            include='scores;participants;statistics.type;events;lineups;league;venue'
        )
        
        if not fixture_data or 'data' not in fixture_data:
            return jsonify({'error': 'Fixture not found'}), 404
        
        fixture = fixture_data['data']
        formatted = _format_fixture(fixture, detailed=True)
        
        # Add prediction if fixture hasn't finished
        if fixture.get('state_id') in [1, 2]:  # Not started or in play
            try:
                prediction = prediction_engine.analyze_fixture(fixture_id)
                if prediction:
                    formatted['prediction'] = {
                        'home_win': prediction.home_win_probability,
                        'draw': prediction.draw_probability,
                        'away_win': prediction.away_win_probability,
                        'predicted_outcome': prediction.predicted_outcome,
                        'predicted_score': f"{prediction.predicted_score[0]}-{prediction.predicted_score[1]}",
                        'confidence': prediction.confidence,
                        'reasoning': prediction.reasoning
                    }
            except Exception as e:
                logger.error(f"Error getting prediction: {str(e)}")
        
        return jsonify(formatted)
        
    except Exception as e:
        logger.error(f"Error getting fixture details: {str(e)}")
        return jsonify({'error': 'Failed to fetch fixture details'}), 500

@simple_bp.route('/fixtures/<int:fixture_id>/prediction', methods=['GET'])
def get_fixture_prediction(fixture_id):
    """Get prediction for a specific fixture"""
    if not api_available or not prediction_engine:
        return jsonify({'error': 'Prediction service not available'}), 503
    
    try:
        prediction = prediction_engine.analyze_fixture(fixture_id)
        
        if not prediction:
            return jsonify({'error': 'Could not generate prediction'}), 404
        
        return jsonify({
            'fixture_id': fixture_id,
            'probabilities': {
                'home_win': prediction.home_win_probability,
                'draw': prediction.draw_probability,
                'away_win': prediction.away_win_probability
            },
            'predicted_outcome': prediction.predicted_outcome,
            'predicted_score': {
                'home': prediction.predicted_score[0],
                'away': prediction.predicted_score[1],
                'display': f"{prediction.predicted_score[0]}-{prediction.predicted_score[1]}"
            },
            'confidence': prediction.confidence,
            'reasoning': prediction.reasoning
        })
        
    except Exception as e:
        logger.error(f"Error generating prediction: {str(e)}")
        return jsonify({'error': 'Failed to generate prediction'}), 500

@simple_bp.route('/teams/<int:team_id>/fixtures', methods=['GET'])
def get_team_fixtures(team_id):
    """Get fixtures for a specific team"""
    if not api_available:
        return jsonify({'error': 'API not available', 'fixtures': []}), 503
    
    try:
        days_back = int(request.args.get('days_back', 30))
        days_forward = int(request.args.get('days_forward', 30))
        
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days_forward)).strftime('%Y-%m-%d')
        
        # Get fixtures
        fixtures_data = client.get_fixtures_by_date_range_for_team(
            start_date, end_date, team_id,
            include='scores;participants;league'
        )
        
        if not fixtures_data or 'data' not in fixtures_data:
            return jsonify({'fixtures': [], 'message': 'No fixtures found for this team'})
        
        fixtures = fixtures_data['data']
        
        # Separate past, current, and future fixtures
        past_fixtures = []
        live_fixtures = []
        upcoming_fixtures = []
        
        for fixture in fixtures:
            formatted = _format_fixture(fixture)
            
            if fixture.get('state_id') == 5:  # Finished
                past_fixtures.append(formatted)
            elif fixture.get('state_id') in [2, 3, 4]:  # In play
                live_fixtures.append(formatted)
            else:  # Not started
                upcoming_fixtures.append(formatted)
        
        return jsonify({
            'team_id': team_id,
            'past_fixtures': past_fixtures,
            'live_fixtures': live_fixtures,
            'upcoming_fixtures': upcoming_fixtures,
            'totals': {
                'past': len(past_fixtures),
                'live': len(live_fixtures),
                'upcoming': len(upcoming_fixtures)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting team fixtures: {str(e)}")
        return jsonify({'error': 'Failed to fetch team fixtures', 'fixtures': []}), 500

@simple_bp.route('/head-to-head/<int:team1_id>/<int:team2_id>', methods=['GET'])
def get_head_to_head(team1_id, team2_id):
    """Get head-to-head record between two teams"""
    if not api_available:
        return jsonify({'error': 'API not available'}), 503
    
    try:
        # Get H2H fixtures
        h2h_data = client.get_fixtures_by_head_to_head(
            team1_id, team2_id,
            include='scores;participants;league'
        )
        
        if not h2h_data or 'data' not in h2h_data:
            return jsonify({'fixtures': [], 'message': 'No head-to-head fixtures found'})
        
        fixtures = h2h_data['data']
        
        # Calculate statistics
        team1_wins = 0
        team2_wins = 0
        draws = 0
        total_goals = 0
        
        formatted_fixtures = []
        for fixture in fixtures[:20]:  # Last 20 H2H matches
            formatted = _format_fixture(fixture)
            formatted_fixtures.append(formatted)
            
            if fixture.get('state_id') == 5:  # Finished
                scores = fixture.get('scores', [])
                for score in scores:
                    if score.get('description') == 'FULLTIME':
                        home_score = score.get('score', {}).get('home', 0)
                        away_score = score.get('score', {}).get('away', 0)
                        total_goals += home_score + away_score
                        
                        # Determine which team was home
                        home_team_id = None
                        for participant in fixture.get('participants', []):
                            if participant.get('meta', {}).get('location') == 'home':
                                home_team_id = participant['id']
                                break
                        
                        if home_score > away_score:
                            if home_team_id == team1_id:
                                team1_wins += 1
                            else:
                                team2_wins += 1
                        elif away_score > home_score:
                            if home_team_id == team1_id:
                                team2_wins += 1
                            else:
                                team1_wins += 1
                        else:
                            draws += 1
                        break
        
        total_matches = team1_wins + team2_wins + draws
        
        return jsonify({
            'team1_id': team1_id,
            'team2_id': team2_id,
            'statistics': {
                'total_matches': total_matches,
                'team1_wins': team1_wins,
                'team2_wins': team2_wins,
                'draws': draws,
                'team1_win_percentage': round((team1_wins / total_matches * 100) if total_matches > 0 else 0, 1),
                'team2_win_percentage': round((team2_wins / total_matches * 100) if total_matches > 0 else 0, 1),
                'draw_percentage': round((draws / total_matches * 100) if total_matches > 0 else 0, 1),
                'average_goals_per_match': round(total_goals / total_matches if total_matches > 0 else 0, 2)
            },
            'fixtures': formatted_fixtures
        })
        
    except Exception as e:
        logger.error(f"Error getting head-to-head: {str(e)}")
        return jsonify({'error': 'Failed to fetch head-to-head data'}), 500

def _format_fixture(fixture: dict, detailed: bool = False) -> dict:
    """Format fixture data for response"""
    # Extract basic info
    formatted = {
        'id': fixture.get('id'),
        'name': fixture.get('name'),
        'date': fixture.get('starting_at'),
        'timestamp': fixture.get('starting_at_timestamp'),
        'status': _get_fixture_status(fixture.get('state_id')),
        'state_id': fixture.get('state_id'),
        'venue': None,
        'league': None,
        'home_team': None,
        'away_team': None,
        'score': None
    }
    
    # Add venue info
    if 'venue' in fixture and fixture['venue']:
        formatted['venue'] = {
            'id': fixture['venue'].get('id'),
            'name': fixture['venue'].get('name'),
            'city': fixture['venue'].get('city')
        }
    
    # Add league info
    if 'league' in fixture and fixture['league']:
        formatted['league'] = {
            'id': fixture['league'].get('id'),
            'name': fixture['league'].get('name'),
            'logo': fixture['league'].get('image_path')
        }
    
    # Extract teams from participants
    if 'participants' in fixture:
        for participant in fixture['participants']:
            team_data = {
                'id': participant.get('id'),
                'name': participant.get('name'),
                'logo': participant.get('image_path')
            }
            
            if participant.get('meta', {}).get('location') == 'home':
                formatted['home_team'] = team_data
            elif participant.get('meta', {}).get('location') == 'away':
                formatted['away_team'] = team_data
    
    # Extract scores
    if 'scores' in fixture and fixture['scores']:
        for score in fixture['scores']:
            if score.get('description') == 'FULLTIME':
                formatted['score'] = {
                    'home': score.get('score', {}).get('home'),
                    'away': score.get('score', {}).get('away'),
                    'display': f"{score.get('score', {}).get('home')}-{score.get('score', {}).get('away')}"
                }
                break
        
        # If no fulltime score, check for current score
        if not formatted['score']:
            for score in fixture['scores']:
                if score.get('description') == 'CURRENT':
                    formatted['score'] = {
                        'home': score.get('score', {}).get('home'),
                        'away': score.get('score', {}).get('away'),
                        'display': f"{score.get('score', {}).get('home')}-{score.get('score', {}).get('away')}",
                        'is_live': True
                    }
                    break
    
    # Add detailed information if requested
    if detailed:
        # Add statistics
        if 'statistics' in fixture:
            formatted['statistics'] = fixture['statistics']
        
        # Add events
        if 'events' in fixture:
            formatted['events'] = [
                {
                    'id': event.get('id'),
                    'type': event.get('type', {}).get('name') if isinstance(event.get('type'), dict) else event.get('type'),
                    'minute': event.get('minute'),
                    'player': event.get('player', {}).get('name') if isinstance(event.get('player'), dict) else None,
                    'team_id': event.get('participant_id')
                }
                for event in fixture.get('events', [])
            ]
        
        # Add lineups if available
        if 'lineups' in fixture:
            formatted['lineups'] = fixture['lineups']
    
    return formatted

def _get_fixture_status(state_id: int) -> str:
    """Convert state_id to human-readable status"""
    status_map = {
        1: 'Not Started',
        2: 'In Play',
        3: 'Half Time',
        4: 'Extra Time',
        5: 'Finished',
        6: 'Finished After Extra Time',
        7: 'Finished After Penalty Shootout',
        8: 'Postponed',
        9: 'Cancelled',
        10: 'Abandoned',
        11: 'Technical Loss',
        12: 'Walkover',
        13: 'In Progress',
        14: 'Suspended',
        15: 'Awarded'
    }
    return status_map.get(state_id, 'Unknown')