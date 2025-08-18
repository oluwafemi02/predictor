"""
SportMonks Data Initialization Script
Syncs initial data from SportMonks API when the app starts
"""

import os
import logging
from datetime import datetime, timedelta
from sportmonks_client import SportMonksAPIClient
from sportmonks_models import db, SportMonksLeague, SportMonksTeam, SportMonksFixture, SportMonksPrediction

logger = logging.getLogger(__name__)

def initialize_sportmonks_data(app):
    """Initialize SportMonks data on app startup"""
    
    # Check if API key is configured
    if not os.environ.get('SPORTMONKS_API_KEY'):
        logger.warning("SPORTMONKS_API_KEY not set, skipping SportMonks initialization")
        return False
    
    try:
        with app.app_context():
            # Check if we already have data
            fixture_count = SportMonksFixture.query.count()
            if fixture_count > 0:
                logger.info(f"SportMonks data already exists ({fixture_count} fixtures), skipping initialization")
                return True
            
            logger.info("Initializing SportMonks data...")
            client = SportMonksAPIClient()
            
            # 1. Sync popular leagues
            logger.info("Syncing leagues...")
            leagues_synced = sync_leagues(client)
            logger.info(f"Synced {leagues_synced} leagues")
            
            # 2. Sync teams from those leagues
            logger.info("Syncing teams...")
            teams_synced = sync_teams(client)
            logger.info(f"Synced {teams_synced} teams")
            
            # 3. Sync fixtures (past 30 days and next 30 days)
            logger.info("Syncing fixtures...")
            fixtures_synced = sync_fixtures(client)
            logger.info(f"Synced {fixtures_synced} fixtures")
            
            # 4. Sync predictions for upcoming fixtures
            logger.info("Syncing predictions...")
            predictions_synced = sync_predictions(client)
            logger.info(f"Synced {predictions_synced} predictions")
            
            logger.info("SportMonks initialization complete!")
            return True
            
    except Exception as e:
        logger.error(f"Error initializing SportMonks data: {str(e)}")
        return False

def sync_leagues(client):
    """Sync popular football leagues"""
    try:
        # Get popular leagues (Premier League, La Liga, Serie A, Bundesliga, Ligue 1)
        popular_league_ids = [8, 564, 384, 82, 301]  # SportMonks IDs for major leagues
        
        count = 0
        for league_id in popular_league_ids:
            try:
                league_data = client.get_league(league_id)
                if league_data and 'data' in league_data:
                    league = league_data['data']
                    
                    # Check if league exists
                    existing = SportMonksLeague.query.filter_by(league_id=league['id']).first()
                    if not existing:
                        new_league = SportMonksLeague(
                            league_id=league['id'],
                            name=league.get('name'),
                            country=league.get('country', {}).get('name'),
                            logo_path=league.get('image_path'),
                            is_active=True
                        )
                        db.session.add(new_league)
                        count += 1
            except Exception as e:
                logger.error(f"Error syncing league {league_id}: {str(e)}")
        
        db.session.commit()
        return count
        
    except Exception as e:
        logger.error(f"Error in sync_leagues: {str(e)}")
        return 0

def sync_teams(client):
    """Sync teams from active leagues"""
    try:
        count = 0
        leagues = SportMonksLeague.query.filter_by(is_active=True).all()
        
        for league in leagues:
            try:
                # Get current season
                season_data = client.get_seasons_by_league(league.league_id)
                if not season_data or 'data' not in season_data:
                    continue
                
                current_season = None
                for season in season_data['data']:
                    if season.get('is_current'):
                        current_season = season
                        break
                
                if not current_season:
                    continue
                
                # Get teams for this season
                teams_data = client.get_teams_by_season(current_season['id'])
                if teams_data and 'data' in teams_data:
                    for team in teams_data['data']:
                        existing = SportMonksTeam.query.filter_by(team_id=team['id']).first()
                        if not existing:
                            new_team = SportMonksTeam(
                                team_id=team['id'],
                                name=team.get('name'),
                                short_code=team.get('short_code'),
                                country=team.get('country', {}).get('name'),
                                founded=team.get('founded'),
                                image_path=team.get('image_path'),
                                venue_id=team.get('venue_id'),
                                venue_name=team.get('venue', {}).get('name')
                            )
                            db.session.add(new_team)
                            count += 1
                            
            except Exception as e:
                logger.error(f"Error syncing teams for league {league.name}: {str(e)}")
        
        db.session.commit()
        return count
        
    except Exception as e:
        logger.error(f"Error in sync_teams: {str(e)}")
        return 0

def sync_fixtures(client, days_back=30, days_ahead=30):
    """Sync fixtures from SportMonks"""
    try:
        count = 0
        
        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        end_date = (datetime.utcnow() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Get fixtures for date range with includes
        fixtures_data = client.get_fixtures_by_date_range(
            start_date, 
            end_date,
            includes=['participants', 'league', 'venue', 'state', 'scores']
        )
        
        if fixtures_data and 'data' in fixtures_data:
            for fixture in fixtures_data['data']:
                try:
                    # Extract team IDs from participants
                    home_team_id = None
                    away_team_id = None
                    participants = fixture.get('participants', [])
                    
                    for participant in participants:
                        if participant.get('meta', {}).get('location') == 'home':
                            home_team_id = participant['id']
                            # Also ensure team exists
                            if not SportMonksTeam.query.get(home_team_id):
                                new_team = SportMonksTeam(
                                    team_id=participant['id'],
                                    name=participant.get('name'),
                                    short_code=participant.get('short_code'),
                                    country=participant.get('country', {}).get('name'),
                                    founded=participant.get('founded'),
                                    image_path=participant.get('image_path'),
                                    venue_id=participant.get('venue_id')
                                )
                                db.session.add(new_team)
                        elif participant.get('meta', {}).get('location') == 'away':
                            away_team_id = participant['id']
                            # Also ensure team exists
                            if not SportMonksTeam.query.get(away_team_id):
                                new_team = SportMonksTeam(
                                    team_id=participant['id'],
                                    name=participant.get('name'),
                                    short_code=participant.get('short_code'),
                                    country=participant.get('country', {}).get('name'),
                                    founded=participant.get('founded'),
                                    image_path=participant.get('image_path'),
                                    venue_id=participant.get('venue_id')
                                )
                                db.session.add(new_team)
                    
                    existing = SportMonksFixture.query.filter_by(fixture_id=fixture['id']).first()
                    if existing:
                        # Update existing fixture
                        if fixture.get('scores'):
                            # Handle scores array structure
                            for score in fixture['scores']:
                                if score.get('description') == 'CURRENT':
                                    existing.home_score = score.get('score', {}).get('home')
                                    existing.away_score = score.get('score', {}).get('away')
                                    break
                        existing.state_id = fixture.get('state_id')
                        existing.state_name = fixture.get('state', {}).get('name')
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Extract scores from array
                        home_score = None
                        away_score = None
                        if fixture.get('scores'):
                            for score in fixture['scores']:
                                if score.get('description') == 'CURRENT':
                                    home_score = score.get('score', {}).get('home')
                                    away_score = score.get('score', {}).get('away')
                                    break
                        
                        # Create new fixture
                        new_fixture = SportMonksFixture(
                            fixture_id=fixture['id'],
                            league_id=fixture.get('league_id'),
                            league_name=fixture.get('league', {}).get('name'),
                            season_id=fixture.get('season_id'),
                            stage_id=fixture.get('stage_id'),
                            round_id=fixture.get('round_id'),
                            home_team_id=home_team_id,
                            away_team_id=away_team_id,
                            starting_at=datetime.fromisoformat(fixture['starting_at'].replace('Z', '+00:00')) if fixture.get('starting_at') else None,
                            result_info=fixture.get('result_info'),
                            home_score=home_score,
                            away_score=away_score,
                            venue_id=fixture.get('venue_id'),
                            venue_name=fixture.get('venue', {}).get('name'),
                            referee_id=fixture.get('referee_id'),
                            state_id=fixture.get('state_id'),
                            state_name=fixture.get('state', {}).get('name')
                        )
                        db.session.add(new_fixture)
                        count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing fixture {fixture.get('id')}: {str(e)}")
            
            db.session.commit()
            
        return count
        
    except Exception as e:
        logger.error(f"Error in sync_fixtures: {str(e)}")
        return 0

def sync_predictions(client):
    """Sync predictions for upcoming fixtures"""
    try:
        count = 0
        
        # Get upcoming fixtures that don't have predictions
        upcoming_fixtures = SportMonksFixture.query.filter(
            SportMonksFixture.starting_at > datetime.utcnow(),
            SportMonksFixture.state_id.in_([1, 2, 3, 4])  # Not started or in progress
        ).limit(20).all()  # Limit to avoid rate limits
        
        for fixture in upcoming_fixtures:
            try:
                # Check if prediction already exists
                existing = SportMonksPrediction.query.filter_by(fixture_id=fixture.fixture_id).first()
                if existing:
                    continue
                
                # Get fixture with predictions from SportMonks
                # Using the include parameter as shown in the example
                fixture_data = client.get_fixture(
                    fixture.fixture_id,
                    includes=['predictions.type']
                )
                
                if fixture_data and 'data' in fixture_data:
                    predictions = fixture_data['data'].get('predictions', [])
                    
                    # Extract key predictions from the array
                    fulltime_result = None
                    btts = None
                    over_25 = None
                    correct_score = None
                    
                    for pred in predictions:
                        pred_type = pred.get('type', {}).get('developer_name', '')
                        pred_values = pred.get('predictions', {})
                        
                        if pred_type == 'FULLTIME_RESULT_PROBABILITY':
                            fulltime_result = pred_values
                        elif pred_type == 'BTTS_PROBABILITY':
                            btts = pred_values
                        elif pred_type == 'OVER_UNDER_2_5_PROBABILITY':
                            over_25 = pred_values
                        elif pred_type == 'CORRECT_SCORE_PROBABILITY':
                            correct_score = pred_values
                    
                    if fulltime_result:
                        # Extract most likely score from correct score predictions
                        home_score = 1
                        away_score = 1
                        if correct_score and 'scores' in correct_score:
                            # Find the most likely score
                            max_prob = 0
                            for score_str, prob in correct_score['scores'].items():
                                if '-' in score_str and prob > max_prob:
                                    try:
                                        h, a = score_str.split('-')
                                        if h.isdigit() and a.isdigit():
                                            max_prob = prob
                                            home_score = int(h)
                                            away_score = int(a)
                                    except:
                                        pass
                        
                        new_prediction = SportMonksPrediction(
                            fixture_id=fixture.fixture_id,
                            predictions_data=predictions,  # Store full predictions array
                            home_win_probability=fulltime_result.get('home', 0) / 100.0,
                            draw_probability=fulltime_result.get('draw', 0) / 100.0,
                            away_win_probability=fulltime_result.get('away', 0) / 100.0,
                            btts_probability=btts.get('yes', 0) / 100.0 if btts else 0.5,
                            over_25_probability=over_25.get('yes', 0) / 100.0 if over_25 else 0.5,
                            under_25_probability=over_25.get('no', 0) / 100.0 if over_25 else 0.5,
                            predicted_home_score=home_score,
                            predicted_away_score=away_score,
                            confidence_score=0.75  # Could calculate based on probability strength
                        )
                        db.session.add(new_prediction)
                        count += 1
                    
            except Exception as e:
                logger.error(f"Error syncing prediction for fixture {fixture.fixture_id}: {str(e)}")
        
        db.session.commit()
        return count
        
    except Exception as e:
        logger.error(f"Error in sync_predictions: {str(e)}")
        return 0