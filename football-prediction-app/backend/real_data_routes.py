from flask import Blueprint, jsonify, request
from models import db, Team, Match, MatchOdds
from data_collector import FootballDataCollector, RapidAPIFootballOddsCollector
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

real_data_bp = Blueprint('real_data', __name__, url_prefix='/api/v1')

@real_data_bp.route('/sync/competitions', methods=['POST'])
def sync_competitions():
    """Sync available competitions from football-data.org"""
    try:
        collector = FootballDataCollector()
        competitions = collector.fetch_competitions()
        
        # Store popular competitions
        popular_comps = {
            2021: 'Premier League',
            2014: 'La Liga',
            2019: 'Serie A',
            2002: 'Bundesliga',
            2015: 'Ligue 1'
        }
        
        synced = []
        for comp in competitions:
            if comp.get('id') in popular_comps:
                synced.append({
                    'id': comp.get('id'),
                    'name': comp.get('name'),
                    'code': comp.get('code')
                })
        
        return jsonify({
            'status': 'success',
            'message': f'Found {len(synced)} popular competitions',
            'competitions': synced
        })
    except Exception as e:
        logger.error(f"Error syncing competitions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@real_data_bp.route('/sync/teams/<int:competition_id>', methods=['POST'])
def sync_teams_real(competition_id):
    """Sync teams from football-data.org for a specific competition"""
    try:
        collector = FootballDataCollector()
        teams_data = collector.sync_teams(competition_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Synced {teams_data["synced"]} teams, {teams_data["updated"]} updated',
            'data': teams_data
        })
    except Exception as e:
        logger.error(f"Error syncing teams: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@real_data_bp.route('/sync/matches/<int:competition_id>', methods=['POST'])
def sync_matches_real(competition_id):
    """Sync matches from football-data.org"""
    try:
        # Get date range from request or use defaults
        data = request.get_json() or {}
        date_from = data.get('date_from', datetime.now().strftime('%Y-%m-%d'))
        date_to = data.get('date_to', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
        
        collector = FootballDataCollector()
        matches_data = collector.sync_matches(competition_id, date_from, date_to)
        
        return jsonify({
            'status': 'success',
            'message': f'Synced {matches_data["synced"]} matches, {matches_data["updated"]} updated',
            'data': matches_data
        })
    except Exception as e:
        logger.error(f"Error syncing matches: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@real_data_bp.route('/data/fetch-and-train', methods=['POST'])
def fetch_data_and_train():
    """Fetch real data and prepare for training"""
    try:
        # First, let's sync some real data
        collector = FootballDataCollector()
        
        # Sync Premier League (ID: 2021) as an example
        competition_id = 2021
        
        # Check if API key is configured
        if not collector.api_key:
            # Try to use RapidAPI data instead
            rapid_collector = RapidAPIFootballOddsCollector()
            
            # Fetch some leagues with odds
            leagues = rapid_collector.fetch_leagues()
            
            return jsonify({
                'status': 'success',
                'message': 'Using RapidAPI data. Found leagues with odds data.',
                'leagues_count': len(leagues.get('response', [])),
                'sample_leagues': leagues.get('response', [])[:5] if leagues else []
            })
        
        # Sync teams
        teams_result = collector.sync_teams(competition_id)
        
        # Sync recent matches
        date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        matches_result = collector.sync_matches(competition_id, date_from, date_to)
        
        # Get match count
        match_count = Match.query.count()
        team_count = Team.query.count()
        
        return jsonify({
            'status': 'success',
            'message': 'Data synchronized successfully',
            'data': {
                'teams_synced': teams_result.get('synced', 0),
                'matches_synced': matches_result.get('synced', 0),
                'total_teams_in_db': team_count,
                'total_matches_in_db': match_count,
                'ready_for_training': match_count > 100
            }
        })
        
    except Exception as e:
        logger.error(f"Error in fetch_data_and_train: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'hint': 'Make sure FOOTBALL_API_KEY is set in environment variables'
        }), 500

@real_data_bp.route('/data/stats', methods=['GET'])
def get_data_stats():
    """Get statistics about available data"""
    try:
        match_count = Match.query.count()
        team_count = Team.query.count()
        odds_count = MatchOdds.query.count()
        
        # Get recent matches
        recent_matches = Match.query.order_by(Match.match_date.desc()).limit(5).all()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_matches': match_count,
                'total_teams': team_count,
                'total_odds_records': odds_count,
                'recent_matches': [
                    {
                        'id': m.id,
                        'date': m.match_date.isoformat() if m.match_date else None,
                        'home_team': m.home_team.name if m.home_team else 'Unknown',
                        'away_team': m.away_team.name if m.away_team else 'Unknown',
                        'home_score': m.home_score,
                        'away_score': m.away_score
                    } for m in recent_matches
                ],
                'data_sufficient_for_training': match_count >= 100
            }
        })
    except Exception as e:
        logger.error(f"Error getting data stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500