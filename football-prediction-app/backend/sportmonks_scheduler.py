"""
SportMonks Data Synchronization Scheduler
Handles periodic updates of fixtures, predictions, live scores, and standings
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
from sportmonks_client import SportMonksAPIClient
from sportmonks_models import (
    db, SportMonksLeague, SportMonksTeam, SportMonksFixture,
    SportMonksPrediction, SportMonksValueBet, SportMonksOdds,
    SportMonksLiveData, SportMonksPlayer, SportMonksStanding
)
from sqlalchemy import and_, or_
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SportMonksScheduler:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler(timezone=pytz.UTC)
        self.client = SportMonksAPIClient()
        self.app = app
        
    def init_app(self, app):
        """Initialize scheduler with Flask app"""
        self.app = app
        self.setup_jobs()
        
    def setup_jobs(self):
        """Configure all scheduled jobs"""
        # Live scores - every 30 seconds during match hours
        self.scheduler.add_job(
            func=self.update_live_scores,
            trigger=IntervalTrigger(seconds=30),
            id='update_live_scores',
            name='Update live scores',
            replace_existing=True
        )
        
        # Upcoming fixtures - every 30 minutes
        self.scheduler.add_job(
            func=self.update_upcoming_fixtures,
            trigger=IntervalTrigger(minutes=30),
            id='update_upcoming_fixtures',
            name='Update upcoming fixtures',
            replace_existing=True
        )
        
        # Predictions - every 2 hours
        self.scheduler.add_job(
            func=self.update_predictions,
            trigger=IntervalTrigger(hours=2),
            id='update_predictions',
            name='Update match predictions',
            replace_existing=True
        )
        
        # Standings - twice daily at 2 AM and 2 PM UTC
        self.scheduler.add_job(
            func=self.update_standings,
            trigger=CronTrigger(hour='2,14', minute=0),
            id='update_standings',
            name='Update league standings',
            replace_existing=True
        )
        
        # Value bets - every hour
        self.scheduler.add_job(
            func=self.update_value_bets,
            trigger=IntervalTrigger(hours=1),
            id='update_value_bets',
            name='Update value bets',
            replace_existing=True
        )
        
        # Leagues and teams - once daily at 3 AM UTC
        self.scheduler.add_job(
            func=self.update_leagues_and_teams,
            trigger=CronTrigger(hour=3, minute=0),
            id='update_leagues_teams',
            name='Update leagues and teams',
            replace_existing=True
        )
        
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("SportMonks scheduler started")
            
            # Run initial updates
            self.run_initial_updates()
            
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("SportMonks scheduler stopped")
            
    def run_initial_updates(self):
        """Run initial data updates when scheduler starts"""
        with self.app.app_context():
            try:
                logger.info("Running initial SportMonks data updates...")
                self.update_leagues_and_teams()
                self.update_upcoming_fixtures()
                self.update_predictions()
                logger.info("Initial updates completed")
            except Exception as e:
                logger.error(f"Error in initial updates: {str(e)}")
    
    def update_live_scores(self):
        """Update live match scores and statistics"""
        with self.app.app_context():
            try:
                logger.debug("Updating live scores...")
                
                # Get live fixtures
                response = self.client.get_live_scores(
                    include=['localTeam', 'visitorTeam', 'stats', 'events']
                )
                
                if not response or 'data' not in response:
                    return
                
                live_fixtures = response['data']
                logger.info(f"Found {len(live_fixtures)} live fixtures")
                
                for fixture_data in live_fixtures:
                    # Update or create fixture
                    fixture = SportMonksFixture.query.filter_by(
                        sportmonks_id=fixture_data['id']
                    ).first()
                    
                    if fixture:
                        # Update scores and status
                        fixture.home_score = fixture_data['scores']['localteam_score']
                        fixture.away_score = fixture_data['scores']['visitorteam_score']
                        fixture.status = fixture_data['time']['status']
                        fixture.minute = fixture_data['time']['minute']
                        fixture.updated_at = datetime.utcnow()
                        
                        # Update live data
                        live_data = SportMonksLiveData.query.filter_by(
                            fixture_id=fixture.id
                        ).first()
                        
                        if not live_data:
                            live_data = SportMonksLiveData(fixture_id=fixture.id)
                            db.session.add(live_data)
                        
                        # Update statistics if available
                        if 'stats' in fixture_data and fixture_data['stats']['data']:
                            stats = fixture_data['stats']['data']
                            for stat in stats:
                                if stat['name'] == 'Ball Possession':
                                    live_data.home_possession = stat['home']
                                    live_data.away_possession = stat['away']
                                elif stat['name'] == 'Total Shots':
                                    live_data.home_shots = stat['home']
                                    live_data.away_shots = stat['away']
                                # Add more stats as needed
                        
                        # Update events
                        if 'events' in fixture_data:
                            live_data.events = fixture_data['events']['data']
                        
                        live_data.last_updated = datetime.utcnow()
                
                db.session.commit()
                logger.debug("Live scores updated successfully")
                
            except Exception as e:
                logger.error(f"Error updating live scores: {str(e)}")
                db.session.rollback()
    
    def update_upcoming_fixtures(self):
        """Update upcoming fixtures for the next 7 days"""
        with self.app.app_context():
            try:
                logger.info("Updating upcoming fixtures...")
                
                start_date = datetime.utcnow().strftime('%Y-%m-%d')
                end_date = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
                
                # Get major leagues (you can customize this list)
                major_leagues = [2, 8, 82, 384, 564]  # Premier League, Championship, Bundesliga, Serie A, La Liga
                
                fixtures = self.client.get_fixtures_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    league_ids=major_leagues,
                    include=['localTeam', 'visitorTeam', 'league', 'venue']
                )
                
                logger.info(f"Found {len(fixtures)} upcoming fixtures")
                
                for fixture_data in fixtures:
                    # Check if teams exist, create if not
                    home_team = self._get_or_create_team(fixture_data.get('localTeam', {}))
                    away_team = self._get_or_create_team(fixture_data.get('visitorTeam', {}))
                    league = self._get_or_create_league(fixture_data.get('league', {}))
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Update or create fixture
                    fixture = SportMonksFixture.query.filter_by(
                        sportmonks_id=fixture_data['id']
                    ).first()
                    
                    if not fixture:
                        fixture = SportMonksFixture(
                            sportmonks_id=fixture_data['id'],
                            league_id=league.id if league else None,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id
                        )
                        db.session.add(fixture)
                    
                    # Update fixture details
                    fixture.season_id = fixture_data.get('season_id')
                    fixture.stage_id = fixture_data.get('stage_id')
                    fixture.round_id = fixture_data.get('round_id')
                    fixture.status = fixture_data['time']['status']
                    fixture.starting_at = datetime.fromisoformat(
                        fixture_data['starting_at'].replace('Z', '+00:00')
                    )
                    fixture.venue_id = fixture_data.get('venue_id')
                    fixture.updated_at = datetime.utcnow()
                
                db.session.commit()
                logger.info("Upcoming fixtures updated successfully")
                
            except Exception as e:
                logger.error(f"Error updating fixtures: {str(e)}")
                db.session.rollback()
    
    def update_predictions(self):
        """Update predictions for upcoming fixtures"""
        with self.app.app_context():
            try:
                logger.info("Updating match predictions...")
                
                # Get fixtures starting in the next 21 days (prediction availability window)
                cutoff_date = datetime.utcnow() + timedelta(days=21)
                
                fixtures = SportMonksFixture.query.filter(
                    and_(
                        SportMonksFixture.starting_at > datetime.utcnow(),
                        SportMonksFixture.starting_at <= cutoff_date,
                        SportMonksFixture.status == 'NS'  # Not Started
                    )
                ).all()
                
                logger.info(f"Updating predictions for {len(fixtures)} fixtures")
                
                for fixture in fixtures:
                    try:
                        # Get prediction from API
                        response = self.client.get_predictions_by_fixture(fixture.sportmonks_id)
                        
                        if response and 'data' in response:
                            prediction_data = response['data']['predictions']
                            
                            # Update or create prediction
                            prediction = SportMonksPrediction.query.filter_by(
                                fixture_id=fixture.id
                            ).first()
                            
                            if not prediction:
                                prediction = SportMonksPrediction(fixture_id=fixture.id)
                                db.session.add(prediction)
                            
                            # Update prediction values
                            prediction.home_win_probability = prediction_data.get('home', 0)
                            prediction.draw_probability = prediction_data.get('draw', 0)
                            prediction.away_win_probability = prediction_data.get('away', 0)
                            prediction.over_25_probability = prediction_data.get('over_25', 0)
                            prediction.under_25_probability = prediction_data.get('under_25', 0)
                            prediction.btts_yes_probability = prediction_data.get('btts_yes', 0)
                            prediction.btts_no_probability = prediction_data.get('btts_no', 0)
                            prediction.correct_scores = prediction_data.get('correct_scores', [])
                            prediction.updated_at = datetime.utcnow()
                            
                    except Exception as e:
                        logger.error(f"Error updating prediction for fixture {fixture.id}: {str(e)}")
                        continue
                
                db.session.commit()
                logger.info("Predictions updated successfully")
                
            except Exception as e:
                logger.error(f"Error updating predictions: {str(e)}")
                db.session.rollback()
    
    def update_value_bets(self):
        """Update value bet recommendations"""
        with self.app.app_context():
            try:
                logger.info("Updating value bets...")
                
                # Get today's and tomorrow's fixtures
                dates = [
                    datetime.utcnow().strftime('%Y-%m-%d'),
                    (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
                ]
                
                for date in dates:
                    fixtures_response = self.client.get_fixtures(date=date)
                    
                    if not fixtures_response or 'data' not in fixtures_response:
                        continue
                    
                    for fixture_data in fixtures_response['data']:
                        # Get value bets for fixture
                        value_bet_response = self.client.get_value_bets_by_fixture(
                            fixture_data['id']
                        )
                        
                        if value_bet_response and 'data' in value_bet_response:
                            # Find fixture in database
                            fixture = SportMonksFixture.query.filter_by(
                                sportmonks_id=fixture_data['id']
                            ).first()
                            
                            if not fixture:
                                continue
                            
                            # Clear old value bets for this fixture
                            SportMonksValueBet.query.filter_by(fixture_id=fixture.id).delete()
                            
                            # Add new value bets
                            for bet_data in value_bet_response['data']:
                                if bet_data.get('value', 0) >= 5.0:  # Minimum 5% value
                                    value_bet = SportMonksValueBet(
                                        fixture_id=fixture.id,
                                        market=bet_data['market'],
                                        selection=bet_data['selection'],
                                        predicted_probability=bet_data['probability'],
                                        bookmaker_odds=bet_data['odds'],
                                        implied_probability=1 / bet_data['odds'] if bet_data['odds'] > 0 else 0,
                                        value_percentage=bet_data['value'],
                                        confidence=bet_data.get('confidence', 0.5),
                                        stake_suggestion=bet_data.get('stake', 1.0)
                                    )
                                    db.session.add(value_bet)
                
                db.session.commit()
                logger.info("Value bets updated successfully")
                
            except Exception as e:
                logger.error(f"Error updating value bets: {str(e)}")
                db.session.rollback()
    
    def update_standings(self):
        """Update league standings"""
        with self.app.app_context():
            try:
                logger.info("Updating league standings...")
                
                # Get active leagues
                leagues = SportMonksLeague.query.filter_by(active=True).all()
                
                for league in leagues:
                    # Get current season
                    seasons_response = self.client.get_seasons(league_id=league.sportmonks_id)
                    
                    if not seasons_response or 'data' not in seasons_response:
                        continue
                    
                    # Get most recent season
                    seasons = sorted(seasons_response['data'], key=lambda x: x['id'], reverse=True)
                    if not seasons:
                        continue
                    
                    current_season = seasons[0]
                    
                    # Get standings
                    standings_response = self.client.get_standings(
                        season_id=current_season['id'],
                        include=['team']
                    )
                    
                    if standings_response and 'data' in standings_response:
                        # Clear old standings for this league/season
                        SportMonksStanding.query.filter_by(
                            league_id=league.id,
                            season_id=current_season['id']
                        ).delete()
                        
                        # Add new standings
                        for standing_data in standings_response['data']:
                            team = SportMonksTeam.query.filter_by(
                                sportmonks_id=standing_data['team']['id']
                            ).first()
                            
                            if not team:
                                team = self._get_or_create_team(standing_data['team'])
                            
                            if team:
                                standing = SportMonksStanding(
                                    league_id=league.id,
                                    season_id=current_season['id'],
                                    team_id=team.id,
                                    position=standing_data['position'],
                                    played=standing_data['overall']['games_played'],
                                    won=standing_data['overall']['won'],
                                    draw=standing_data['overall']['draw'],
                                    lost=standing_data['overall']['lost'],
                                    goals_for=standing_data['overall']['goals_scored'],
                                    goals_against=standing_data['overall']['goals_against'],
                                    goal_difference=standing_data['overall']['goals_scored'] - standing_data['overall']['goals_against'],
                                    points=standing_data['overall']['points'],
                                    recent_form=standing_data.get('recent_form', ''),
                                    home_played=standing_data['home']['games_played'],
                                    home_won=standing_data['home']['won'],
                                    home_draw=standing_data['home']['draw'],
                                    home_lost=standing_data['home']['lost'],
                                    away_played=standing_data['away']['games_played'],
                                    away_won=standing_data['away']['won'],
                                    away_draw=standing_data['away']['draw'],
                                    away_lost=standing_data['away']['lost']
                                )
                                db.session.add(standing)
                
                db.session.commit()
                logger.info("Standings updated successfully")
                
            except Exception as e:
                logger.error(f"Error updating standings: {str(e)}")
                db.session.rollback()
    
    def update_leagues_and_teams(self):
        """Update leagues and teams data"""
        with self.app.app_context():
            try:
                logger.info("Updating leagues and teams...")
                
                # Get all leagues
                leagues_response = self.client.get_leagues(include=['country'])
                
                if leagues_response and 'data' in leagues_response:
                    for league_data in leagues_response['data']:
                        self._get_or_create_league(league_data)
                
                db.session.commit()
                logger.info("Leagues and teams updated successfully")
                
            except Exception as e:
                logger.error(f"Error updating leagues and teams: {str(e)}")
                db.session.rollback()
    
    def _get_or_create_team(self, team_data):
        """Helper to get or create a team"""
        if not team_data or 'id' not in team_data:
            return None
        
        team = SportMonksTeam.query.filter_by(
            sportmonks_id=team_data['id']
        ).first()
        
        if not team:
            team = SportMonksTeam(
                sportmonks_id=team_data['id'],
                name=team_data.get('name', 'Unknown'),
                short_code=team_data.get('short_code'),
                country=team_data.get('country', {}).get('name'),
                logo_path=team_data.get('logo_path'),
                founded=team_data.get('founded')
            )
            db.session.add(team)
            db.session.flush()  # Get ID without committing
        
        return team
    
    def _get_or_create_league(self, league_data):
        """Helper to get or create a league"""
        if not league_data or 'id' not in league_data:
            return None
        
        league = SportMonksLeague.query.filter_by(
            sportmonks_id=league_data['id']
        ).first()
        
        if not league:
            league = SportMonksLeague(
                sportmonks_id=league_data['id'],
                name=league_data.get('name', 'Unknown'),
                country=league_data.get('country', {}).get('name') if 'country' in league_data else None,
                logo_path=league_data.get('logo_path'),
                type=league_data.get('type'),
                is_cup=league_data.get('is_cup', False),
                active=league_data.get('active', True)
            )
            db.session.add(league)
            db.session.flush()
        
        return league

# Create global scheduler instance
sportmonks_scheduler = SportMonksScheduler()