from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from models import db, Team, Player, Match, TeamStatistics, Injury, PlayerPerformance, Prediction, HeadToHead
from config import config
from data_collector import FootballDataCollector, FreeSportsDataCollector
from prediction_model import FootballPredictionModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    migrate = Migrate(app, db)
    
    # Initialize scheduler for periodic tasks
    scheduler = BackgroundScheduler()
    scheduler.start()
    
    # Initialize data collector and prediction model
    data_collector = FootballDataCollector()
    free_collector = FreeSportsDataCollector()
    prediction_model = FootballPredictionModel()
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # API Routes
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/teams', methods=['GET'])
    def get_teams():
        """Get all teams or filter by competition"""
        competition = request.args.get('competition')
        
        query = Team.query
        if competition:
            # Filter teams by competition (would need to join through matches)
            teams = query.join(Match, db.or_(
                Match.home_team_id == Team.id,
                Match.away_team_id == Team.id
            )).filter(Match.competition == competition).distinct().all()
        else:
            teams = query.all()
        
        return jsonify({
            'teams': [{
                'id': team.id,
                'name': team.name,
                'code': team.code,
                'logo_url': team.logo_url,
                'stadium': team.stadium,
                'founded': team.founded
            } for team in teams]
        })
    
    @app.route('/api/teams/<int:team_id>', methods=['GET'])
    def get_team_details(team_id):
        """Get detailed information about a specific team"""
        team = Team.query.get_or_404(team_id)
        
        # Get current season statistics
        current_season = request.args.get('season', '2023-24')
        stats = TeamStatistics.query.filter_by(
            team_id=team_id,
            season=current_season
        ).first()
        
        # Get recent matches
        recent_matches = Match.query.filter(
            db.or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).limit(10).all()
        
        # Get injured players
        injured_players = Player.query.join(Injury).filter(
            Player.team_id == team_id,
            Injury.status == 'active'
        ).all()
        
        return jsonify({
            'team': {
                'id': team.id,
                'name': team.name,
                'code': team.code,
                'logo_url': team.logo_url,
                'stadium': team.stadium,
                'founded': team.founded
            },
            'statistics': {
                'season': stats.season if stats else current_season,
                'matches_played': stats.matches_played if stats else 0,
                'wins': stats.wins if stats else 0,
                'draws': stats.draws if stats else 0,
                'losses': stats.losses if stats else 0,
                'goals_for': stats.goals_for if stats else 0,
                'goals_against': stats.goals_against if stats else 0,
                'form': stats.form if stats else '',
                'clean_sheets': stats.clean_sheets if stats else 0,
                'home_record': {
                    'wins': stats.home_wins if stats else 0,
                    'draws': stats.home_draws if stats else 0,
                    'losses': stats.home_losses if stats else 0
                },
                'away_record': {
                    'wins': stats.away_wins if stats else 0,
                    'draws': stats.away_draws if stats else 0,
                    'losses': stats.away_losses if stats else 0
                }
            } if stats else None,
            'recent_matches': [{
                'id': match.id,
                'date': match.match_date.isoformat(),
                'home_team': match.home_team.name,
                'away_team': match.away_team.name,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'status': match.status,
                'competition': match.competition
            } for match in recent_matches],
            'injured_players': [{
                'id': player.id,
                'name': player.name,
                'position': player.position,
                'injury_type': player.injuries[0].injury_type if player.injuries else None,
                'expected_return': player.injuries[0].expected_return_date.isoformat() if player.injuries and player.injuries[0].expected_return_date else None
            } for player in injured_players]
        })
    
    @app.route('/api/matches', methods=['GET'])
    def get_matches():
        """Get matches with optional filters"""
        # Parse query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        team_id = request.args.get('team_id', type=int)
        competition = request.args.get('competition')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = app.config['MATCHES_PER_PAGE']
        
        # Build query
        query = Match.query
        
        if date_from:
            query = query.filter(Match.match_date >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(Match.match_date <= datetime.fromisoformat(date_to))
        if team_id:
            query = query.filter(db.or_(
                Match.home_team_id == team_id,
                Match.away_team_id == team_id
            ))
        if competition:
            query = query.filter(Match.competition == competition)
        if status:
            query = query.filter(Match.status == status)
        
        # Order by date
        query = query.order_by(Match.match_date.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        matches = [{
            'id': match.id,
            'date': match.match_date.isoformat(),
            'home_team': {
                'id': match.home_team.id,
                'name': match.home_team.name,
                'logo_url': match.home_team.logo_url
            },
            'away_team': {
                'id': match.away_team.id,
                'name': match.away_team.name,
                'logo_url': match.away_team.logo_url
            },
            'home_score': match.home_score,
            'away_score': match.away_score,
            'status': match.status,
            'competition': match.competition,
            'venue': match.venue,
            'has_prediction': bool(match.predictions)
        } for match in paginated.items]
        
        return jsonify({
            'matches': matches,
            'pagination': {
                'page': paginated.page,
                'pages': paginated.pages,
                'total': paginated.total,
                'per_page': per_page
            }
        })
    
    @app.route('/api/matches/<int:match_id>', methods=['GET'])
    def get_match_details(match_id):
        """Get detailed information about a specific match"""
        match = Match.query.get_or_404(match_id)
        
        # Get head-to-head statistics
        h2h = HeadToHead.query.filter(
            db.or_(
                db.and_(HeadToHead.team1_id == match.home_team_id, HeadToHead.team2_id == match.away_team_id),
                db.and_(HeadToHead.team1_id == match.away_team_id, HeadToHead.team2_id == match.home_team_id)
            )
        ).first()
        
        # Get prediction if exists
        prediction = Prediction.query.filter_by(match_id=match_id).first()
        
        return jsonify({
            'match': {
                'id': match.id,
                'date': match.match_date.isoformat(),
                'home_team': {
                    'id': match.home_team.id,
                    'name': match.home_team.name,
                    'logo_url': match.home_team.logo_url
                },
                'away_team': {
                    'id': match.away_team.id,
                    'name': match.away_team.name,
                    'logo_url': match.away_team.logo_url
                },
                'home_score': match.home_score,
                'away_score': match.away_score,
                'home_score_halftime': match.home_score_halftime,
                'away_score_halftime': match.away_score_halftime,
                'status': match.status,
                'competition': match.competition,
                'venue': match.venue,
                'referee': match.referee,
                'attendance': match.attendance
            },
            'head_to_head': {
                'total_matches': h2h.total_matches,
                'home_wins': h2h.team1_wins if h2h.team1_id == match.home_team_id else h2h.team2_wins,
                'away_wins': h2h.team2_wins if h2h.team1_id == match.home_team_id else h2h.team1_wins,
                'draws': h2h.draws,
                'last_5_results': h2h.last_5_results
            } if h2h else None,
            'prediction': {
                'home_win_probability': prediction.home_win_probability,
                'draw_probability': prediction.draw_probability,
                'away_win_probability': prediction.away_win_probability,
                'predicted_home_score': prediction.predicted_home_score,
                'predicted_away_score': prediction.predicted_away_score,
                'over_2_5_probability': prediction.over_2_5_probability,
                'both_teams_score_probability': prediction.both_teams_score_probability,
                'confidence_score': prediction.confidence_score,
                'factors': prediction.factors
            } if prediction else None
        })
    
    @app.route('/api/predictions', methods=['GET'])
    def get_predictions():
        """Get all predictions or filter by date range"""
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = request.args.get('page', 1, type=int)
        per_page = app.config['PREDICTIONS_PER_PAGE']
        
        query = Prediction.query.join(Match)
        
        if date_from:
            query = query.filter(Match.match_date >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(Match.match_date <= datetime.fromisoformat(date_to))
        
        query = query.order_by(Match.match_date.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        predictions = [{
            'id': pred.id,
            'match': {
                'id': pred.match.id,
                'date': pred.match.match_date.isoformat(),
                'home_team': pred.match.home_team.name,
                'away_team': pred.match.away_team.name,
                'status': pred.match.status,
                'actual_home_score': pred.match.home_score,
                'actual_away_score': pred.match.away_score
            },
            'predictions': {
                'home_win_probability': pred.home_win_probability,
                'draw_probability': pred.draw_probability,
                'away_win_probability': pred.away_win_probability,
                'predicted_home_score': pred.predicted_home_score,
                'predicted_away_score': pred.predicted_away_score
            },
            'confidence_score': pred.confidence_score,
            'created_at': pred.created_at.isoformat()
        } for pred in paginated.items]
        
        return jsonify({
            'predictions': predictions,
            'pagination': {
                'page': paginated.page,
                'pages': paginated.pages,
                'total': paginated.total,
                'per_page': per_page
            }
        })
    
    @app.route('/api/predictions/<int:match_id>', methods=['POST'])
    def create_prediction(match_id):
        """Create a new prediction for a match"""
        match = Match.query.get_or_404(match_id)
        
        # Check if prediction already exists
        existing = Prediction.query.filter_by(match_id=match_id).first()
        if existing:
            return jsonify({'error': 'Prediction already exists for this match'}), 400
        
        # Generate prediction
        try:
            result = prediction_model.predict_match(match)
            if not result:
                return jsonify({'error': 'Could not generate prediction'}), 500
            
            return jsonify(result), 201
        except Exception as e:
            logger.error(f"Error generating prediction: {str(e)}")
            return jsonify({'error': 'Failed to generate prediction'}), 500
    
    @app.route('/api/upcoming-predictions', methods=['GET'])
    def get_upcoming_predictions():
        """Get predictions for upcoming matches"""
        # Get upcoming matches
        upcoming_matches = Match.query.filter(
            Match.status == 'scheduled',
            Match.match_date >= datetime.utcnow(),
            Match.match_date <= datetime.utcnow() + timedelta(days=7)
        ).order_by(Match.match_date).all()
        
        predictions = []
        for match in upcoming_matches:
            # Check if prediction exists
            pred = Prediction.query.filter_by(match_id=match.id).first()
            if not pred:
                # Generate prediction
                try:
                    result = prediction_model.predict_match(match)
                    if result:
                        predictions.append(result)
                except Exception as e:
                    logger.error(f"Error generating prediction for match {match.id}: {str(e)}")
            else:
                predictions.append({
                    'match_id': match.id,
                    'home_team': match.home_team.name,
                    'away_team': match.away_team.name,
                    'match_date': match.match_date.isoformat(),
                    'predictions': {
                        'ensemble': {
                            'home_win_probability': pred.home_win_probability,
                            'draw_probability': pred.draw_probability,
                            'away_win_probability': pred.away_win_probability
                        }
                    },
                    'expected_goals': {
                        'home': pred.predicted_home_score,
                        'away': pred.predicted_away_score
                    },
                    'confidence': pred.confidence_score
                })
        
        return jsonify({'predictions': predictions})
    
    @app.route('/api/statistics/competitions', methods=['GET'])
    def get_competitions():
        """Get list of available competitions"""
        competitions = db.session.query(Match.competition).distinct().all()
        return jsonify({
            'competitions': [comp[0] for comp in competitions if comp[0]]
        })
    
    @app.route('/api/statistics/league-table', methods=['GET'])
    def get_league_table():
        """Get league table for a specific competition and season"""
        competition = request.args.get('competition')
        season = request.args.get('season', '2023-24')
        
        if not competition:
            return jsonify({'error': 'Competition parameter required'}), 400
        
        # Get all teams in the competition
        teams = Team.query.join(TeamStatistics).filter(
            TeamStatistics.season == season,
            TeamStatistics.competition == competition
        ).all()
        
        table = []
        for team in teams:
            stats = TeamStatistics.query.filter_by(
                team_id=team.id,
                season=season,
                competition=competition
            ).first()
            
            if stats:
                points = (stats.wins * 3) + stats.draws
                goal_difference = stats.goals_for - stats.goals_against
                
                table.append({
                    'position': 0,  # Will be set after sorting
                    'team': {
                        'id': team.id,
                        'name': team.name,
                        'logo_url': team.logo_url
                    },
                    'played': stats.matches_played,
                    'won': stats.wins,
                    'drawn': stats.draws,
                    'lost': stats.losses,
                    'goals_for': stats.goals_for,
                    'goals_against': stats.goals_against,
                    'goal_difference': goal_difference,
                    'points': points,
                    'form': stats.form
                })
        
        # Sort by points, then goal difference, then goals scored
        table.sort(key=lambda x: (x['points'], x['goal_difference'], x['goals_for']), reverse=True)
        
        # Set positions
        for i, entry in enumerate(table):
            entry['position'] = i + 1
        
        return jsonify({'table': table})
    
    @app.route('/api/sync/teams/<int:competition_id>', methods=['POST'])
    def sync_teams(competition_id):
        """Manually trigger team synchronization"""
        try:
            data_collector.sync_teams(competition_id)
            return jsonify({'message': 'Teams synchronized successfully'})
        except Exception as e:
            logger.error(f"Error syncing teams: {str(e)}")
            return jsonify({'error': 'Failed to sync teams'}), 500
    
    @app.route('/api/sync/matches/<int:competition_id>', methods=['POST'])
    def sync_matches(competition_id):
        """Manually trigger match synchronization"""
        try:
            season = request.json.get('season') if request.json else None
            data_collector.sync_matches(competition_id, season)
            return jsonify({'message': 'Matches synchronized successfully'})
        except Exception as e:
            logger.error(f"Error syncing matches: {str(e)}")
            return jsonify({'error': 'Failed to sync matches'}), 500
    
    @app.route('/api/model/train', methods=['POST'])
    def train_model():
        """Manually trigger model training"""
        try:
            prediction_model.train()
            prediction_model.save_model()
            return jsonify({'message': 'Model trained successfully'})
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return jsonify({'error': 'Failed to train model'}), 500
    
    @app.route('/api/model/status', methods=['GET'])
    def model_status():
        """Get model training status"""
        return jsonify({
            'is_trained': prediction_model.is_trained,
            'model_version': 'ensemble_v1',
            'features': prediction_model.feature_names
        })
    
    # Schedule periodic tasks
    def update_match_data():
        """Periodic task to update match data"""
        with app.app_context():
            try:
                # Update matches for major competitions
                # You would need to configure which competitions to track
                logger.info("Updating match data...")
                # data_collector.sync_matches(competition_id)
            except Exception as e:
                logger.error(f"Error updating match data: {str(e)}")
    
    def update_predictions():
        """Periodic task to update predictions for upcoming matches"""
        with app.app_context():
            try:
                logger.info("Updating predictions...")
                # Get upcoming matches without predictions
                upcoming_matches = Match.query.filter(
                    Match.status == 'scheduled',
                    Match.match_date >= datetime.utcnow(),
                    Match.match_date <= datetime.utcnow() + timedelta(days=7)
                ).all()
                
                for match in upcoming_matches:
                    if not Prediction.query.filter_by(match_id=match.id).first():
                        try:
                            prediction_model.predict_match(match)
                        except Exception as e:
                            logger.error(f"Error predicting match {match.id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error updating predictions: {str(e)}")
    
    # Schedule tasks (comment out if you don't want automatic updates)
    # scheduler.add_job(update_match_data, 'interval', hours=6)
    # scheduler.add_job(update_predictions, 'interval', hours=12)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    # Load model on startup
    try:
        prediction_model.load_model()
    except:
        logger.warning("No saved model found. Please train the model.")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)