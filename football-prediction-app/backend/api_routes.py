from flask import Blueprint, jsonify, request
from models import db, Match, MatchOdds, Team
from data_collector import RapidAPIFootballOddsCollector
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

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
            'data': odds_data.get('api', {}).get('odds', []),
            'league_id': league_id,
            'bookmaker_id': bookmaker_id,
            'page': page
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/fixture/<int:fixture_id>', methods=['GET'])
def get_fixture_odds(fixture_id):
    """Get odds for a specific fixture from all bookmakers"""
    try:
        collector = RapidAPIFootballOddsCollector()
        odds_data = collector.fetch_odds_by_fixture(fixture_id)
        
        return jsonify({
            'status': 'success',
            'data': odds_data.get('api', {}).get('odds', []),
            'fixture_id': fixture_id
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/date/<date_str>', methods=['GET'])
def get_odds_by_date(date_str):
    """Get odds for all fixtures on a specific date (YYYY-MM-DD)"""
    try:
        # Validate date format
        datetime.strptime(date_str, '%Y-%m-%d')
        
        collector = RapidAPIFootballOddsCollector()
        odds_data = collector.fetch_odds_by_date(date_str)
        
        return jsonify({
            'status': 'success',
            'data': odds_data.get('api', {}).get('odds', []),
            'date': date_str
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

@api_bp.route('/odds/match/<int:match_id>', methods=['GET'])
def get_match_odds(match_id):
    """Get stored odds for a specific match from the database"""
    try:
        match = Match.query.get_or_404(match_id)
        odds = MatchOdds.query.filter_by(match_id=match_id).all()
        
        odds_data = []
        for odd in odds:
            odds_data.append({
                'bookmaker_id': odd.bookmaker_id,
                'bookmaker_name': odd.bookmaker_name,
                'home_win': odd.home_win_odds,
                'draw': odd.draw_odds,
                'away_win': odd.away_win_odds,
                'over_2_5': odd.over_2_5_odds,
                'under_2_5': odd.under_2_5_odds,
                'btts_yes': odd.btts_yes_odds,
                'btts_no': odd.btts_no_odds,
                'home_handicap': odd.home_handicap,
                'home_handicap_odds': odd.home_handicap_odds,
                'away_handicap': odd.away_handicap,
                'away_handicap_odds': odd.away_handicap_odds,
                'additional_odds': odd.additional_odds,
                'last_updated': odd.update_timestamp.isoformat() if odd.update_timestamp else None
            })
        
        return jsonify({
            'status': 'success',
            'match': {
                'id': match.id,
                'home_team': match.home_team.name,
                'away_team': match.away_team.name,
                'date': match.match_date.isoformat(),
                'venue': match.venue,
                'competition': match.competition
            },
            'odds': odds_data,
            'count': len(odds_data)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/odds/sync/league/<int:league_id>', methods=['POST'])
def sync_league_odds(league_id):
    """Sync odds for a specific league"""
    try:
        bookmaker_id = request.json.get('bookmaker_id', 5)
        max_pages = request.json.get('max_pages', 1)
        
        collector = RapidAPIFootballOddsCollector()
        collector.sync_league_odds(league_id, bookmaker_id, max_pages)
        
        return jsonify({
            'status': 'success',
            'message': f'Started syncing odds for league {league_id}'
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
        match = Match.query.get_or_404(match_id)
        fixture_id = request.json.get('fixture_id')
        
        if not fixture_id:
            return jsonify({
                'status': 'error',
                'message': 'fixture_id is required'
            }), 400
        
        collector = RapidAPIFootballOddsCollector()
        collector.sync_odds_for_match(match, fixture_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Synced odds for match {match_id}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500