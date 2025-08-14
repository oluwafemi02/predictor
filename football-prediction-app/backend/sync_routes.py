"""
Manual sync routes for forcing data synchronization
Useful for debugging and ensuring data is stored in the database
"""

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from datetime import datetime, timedelta
import logging

from models import db
from data_collector import FootballDataCollector
from sportmonks_client import SportMonksClient
from sportmonks_scheduler import SportMonksScheduler
from scheduler import FootballScheduler
from auth import require_api_key

logger = logging.getLogger(__name__)

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

@sync_bp.route('/status', methods=['GET'])
@cross_origin()
def sync_status():
    """Get current sync status and database statistics"""
    try:
        from models import Team, Match, SportMonksFixture, SportMonksPrediction
        
        stats = {
            'database': {
                'teams': Team.query.count(),
                'matches': Match.query.count(),
                'sportmonks_fixtures': SportMonksFixture.query.count(),
                'sportmonks_predictions': SportMonksPrediction.query.count()
            },
            'last_sync': {
                'teams': Team.query.order_by(Team.id.desc()).first(),
                'matches': Match.query.order_by(Match.id.desc()).first(),
            }
        }
        
        # Add last sync times if available
        if stats['last_sync']['teams']:
            stats['last_sync']['teams'] = {
                'name': stats['last_sync']['teams'].name,
                'id': stats['last_sync']['teams'].id
            }
        
        if stats['last_sync']['matches']:
            stats['last_sync']['matches'] = {
                'date': stats['last_sync']['matches'].match_date.isoformat(),
                'home_team': stats['last_sync']['matches'].home_team.name if stats['last_sync']['matches'].home_team else 'Unknown',
                'away_team': stats['last_sync']['matches'].away_team.name if stats['last_sync']['matches'].away_team else 'Unknown'
            }
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@sync_bp.route('/football-data/all', methods=['POST'])
@cross_origin()
@require_api_key
def sync_football_data_all():
    """Sync all data from football-data.org API"""
    try:
        collector = FootballDataCollector()
        results = {
            'teams': {'synced': 0, 'updated': 0},
            'matches': {'synced': 0, 'updated': 0}
        }
        
        # Premier League ID
        competition_id = 2021
        
        # Sync teams first
        logger.info("Syncing teams...")
        teams_result = collector.sync_teams(competition_id)
        results['teams'] = teams_result
        
        # Sync recent matches
        logger.info("Syncing recent matches...")
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        matches_result = collector.sync_matches(competition_id, date_from, date_to)
        results['matches'] = matches_result
        
        return jsonify({
            'status': 'success',
            'message': 'Data sync completed',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in full sync: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@sync_bp.route('/sportmonks/fixtures', methods=['POST'])
@cross_origin()
@require_api_key
def sync_sportmonks_fixtures():
    """Sync fixtures from SportMonks API and store in database"""
    try:
        from app import create_app
        app = create_app()
        
        # Initialize SportMonks scheduler
        scheduler = SportMonksScheduler()
        scheduler.init_app(app)
        
        # Get date range from request
        data = request.get_json() or {}
        days_ahead = data.get('days_ahead', 7)
        days_behind = data.get('days_behind', 0)
        
        with app.app_context():
            # Update upcoming fixtures
            logger.info(f"Syncing fixtures for next {days_ahead} days...")
            scheduler.update_upcoming_fixtures()
            
            # Update recent results if requested
            if days_behind > 0:
                logger.info(f"Syncing results for past {days_behind} days...")
                scheduler.update_recent_results()
            
            # Get stats
            from models import SportMonksFixture
            fixture_count = SportMonksFixture.query.count()
            recent_fixtures = SportMonksFixture.query.order_by(
                SportMonksFixture.updated_at.desc()
            ).limit(5).all()
            
            return jsonify({
                'status': 'success',
                'message': 'SportMonks fixtures synced',
                'stats': {
                    'total_fixtures': fixture_count,
                    'recent_updates': [
                        {
                            'id': f.sportmonks_id,
                            'home_team': f.home_team.name if f.home_team else 'Unknown',
                            'away_team': f.away_team.name if f.away_team else 'Unknown',
                            'date': f.starting_at.isoformat() if f.starting_at else None,
                            'updated': f.updated_at.isoformat() if f.updated_at else None
                        }
                        for f in recent_fixtures
                    ]
                }
            })
            
    except Exception as e:
        logger.error(f"Error syncing SportMonks fixtures: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@sync_bp.route('/sportmonks/predictions', methods=['POST'])
@cross_origin()
@require_api_key
def sync_sportmonks_predictions():
    """Sync predictions from SportMonks API"""
    try:
        from app import create_app
        app = create_app()
        
        scheduler = SportMonksScheduler()
        scheduler.init_app(app)
        
        with app.app_context():
            # Update predictions
            logger.info("Updating SportMonks predictions...")
            scheduler.update_predictions()
            
            # Get stats
            from models import SportMonksPrediction
            prediction_count = SportMonksPrediction.query.count()
            
            return jsonify({
                'status': 'success',
                'message': 'SportMonks predictions synced',
                'stats': {
                    'total_predictions': prediction_count
                }
            })
            
    except Exception as e:
        logger.error(f"Error syncing SportMonks predictions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@sync_bp.route('/force-all', methods=['POST'])
@cross_origin()
@require_api_key
def force_sync_all():
    """Force sync all data from all sources"""
    try:
        from app import create_app
        app = create_app()
        
        results = {
            'football_data': {},
            'sportmonks': {}
        }
        
        with app.app_context():
            # Football Data sync
            logger.info("Starting Football Data sync...")
            collector = FootballDataCollector()
            
            # Sync Premier League
            competition_id = 2021
            teams_result = collector.sync_teams(competition_id)
            results['football_data']['teams'] = teams_result
            
            # Sync matches
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            date_to = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            matches_result = collector.sync_matches(competition_id, date_from, date_to)
            results['football_data']['matches'] = matches_result
            
            # SportMonks sync
            logger.info("Starting SportMonks sync...")
            scheduler = SportMonksScheduler()
            scheduler.init_app(app)
            
            # Update fixtures
            scheduler.update_upcoming_fixtures()
            from models import SportMonksFixture
            results['sportmonks']['fixtures'] = SportMonksFixture.query.count()
            
            # Update predictions
            scheduler.update_predictions()
            from models import SportMonksPrediction
            results['sportmonks']['predictions'] = SportMonksPrediction.query.count()
            
            return jsonify({
                'status': 'success',
                'message': 'All data sources synced',
                'results': results
            })
            
    except Exception as e:
        logger.error(f"Error in force sync all: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@sync_bp.route('/test-database', methods=['GET'])
@cross_origin()
def test_database_connection():
    """Test database connection and write capability"""
    try:
        from models import db, Team
        
        # Test read
        team_count = Team.query.count()
        logger.info(f"Database read test: {team_count} teams found")
        
        # Test write (create a test team and then delete it)
        test_team = Team(
            name="Test Team",
            code="TST",
            api_id=999999  # Use a high ID that won't conflict
        )
        db.session.add(test_team)
        db.session.commit()
        logger.info("Database write test: Test team created")
        
        # Clean up
        db.session.delete(test_team)
        db.session.commit()
        logger.info("Database cleanup: Test team deleted")
        
        return jsonify({
            'status': 'success',
            'message': 'Database connection and write test successful',
            'team_count': team_count
        })
        
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Database test failed: {str(e)}"
        }), 500