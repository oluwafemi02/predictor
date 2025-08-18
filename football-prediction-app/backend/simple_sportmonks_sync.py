"""
Simple SportMonks sync that directly populates the database
"""

import os
import logging
from datetime import datetime, timedelta
from sportmonks_models import db, SportMonksLeague, SportMonksTeam, SportMonksFixture, SportMonksPrediction
import requests

logger = logging.getLogger(__name__)

def simple_sync(app):
    """Simple sync using direct API calls"""
    
    api_key = os.environ.get('SPORTMONKS_API_KEY')
    if not api_key:
        logger.error("No SportMonks API key found")
        return False
    
    base_url = "https://api.sportmonks.com/v3/football"
    headers = {
        "Authorization": api_key
    }
    
    with app.app_context():
        try:
            # 1. Get fixtures for past 30 days and next 7 days
            logger.info("Fetching fixtures...")
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            fixtures_url = f"{base_url}/fixtures/between/{start_date}/{end_date}"
            params = {
                "include": "participants;league;venue;state;scores;predictions.type",
                "per_page": 100
            }
            
            # Try without league filter first to see if we get any data
            logger.info("Trying without league filter...")
            
            logger.info(f"Requesting: {fixtures_url}")
            logger.info(f"Date range: {start_date} to {end_date}")
            
            response = requests.get(fixtures_url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            fixtures = data.get('data', [])
            
            logger.info(f"Found {len(fixtures)} fixtures")
            if len(fixtures) == 0:
                logger.warning("No fixtures found - check date range and API key permissions")
            
            fixture_count = 0
            team_count = 0
            prediction_count = 0
            
            for fixture in fixtures:
                # Extract teams from participants
                home_team = None
                away_team = None
                
                for participant in fixture.get('participants', []):
                    if participant.get('meta', {}).get('location') == 'home':
                        home_team = participant
                    elif participant.get('meta', {}).get('location') == 'away':
                        away_team = participant
                
                if not home_team or not away_team:
                    continue
                
                # Save teams
                for team_data in [home_team, away_team]:
                    existing_team = SportMonksTeam.query.filter_by(team_id=team_data['id']).first()
                    if not existing_team:
                        new_team = SportMonksTeam(
                            team_id=team_data['id'],
                            name=team_data.get('name'),
                            short_code=team_data.get('short_code'),
                            image_path=team_data.get('image_path'),
                            country=team_data.get('country', {}).get('name'),
                            founded=team_data.get('founded'),
                            venue_id=team_data.get('venue_id')
                        )
                        db.session.add(new_team)
                        team_count += 1
                
                # Save league
                league = fixture.get('league', {})
                if league:
                    existing_league = SportMonksLeague.query.filter_by(league_id=league['id']).first()
                    if not existing_league:
                        new_league = SportMonksLeague(
                            league_id=league['id'],
                            name=league.get('name'),
                            country=league.get('country', {}).get('name'),
                            logo_path=league.get('image_path'),
                            is_active=True
                        )
                        db.session.add(new_league)
                
                # Save fixture
                existing_fixture = SportMonksFixture.query.filter_by(fixture_id=fixture['id']).first()
                if not existing_fixture:
                    # Get scores
                    home_score = None
                    away_score = None
                    if fixture.get('scores'):
                        for score in fixture['scores']:
                            if score.get('description') == 'CURRENT':
                                home_score = score.get('score', {}).get('home')
                                away_score = score.get('score', {}).get('away')
                                break
                    
                    new_fixture = SportMonksFixture(
                        fixture_id=fixture['id'],
                        league_id=fixture.get('league_id'),
                        league_name=league.get('name'),
                        season_id=fixture.get('season_id'),
                        home_team_id=home_team['id'],
                        away_team_id=away_team['id'],
                        starting_at=datetime.fromisoformat(fixture['starting_at'].replace('Z', '+00:00')),
                        home_score=home_score,
                        away_score=away_score,
                        venue_id=fixture.get('venue_id'),
                        venue_name=fixture.get('venue', {}).get('name'),
                        state_id=fixture.get('state_id'),
                        state_name=fixture.get('state', {}).get('name')
                    )
                    db.session.add(new_fixture)
                    fixture_count += 1
                    
                    # Save predictions
                    predictions = fixture.get('predictions', [])
                    if predictions and fixture.get('state_id') in [1, 2, 3, 4]:  # Not finished
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
                            # Extract most likely score
                            home_score_pred = 1
                            away_score_pred = 1
                            if correct_score and 'scores' in correct_score:
                                max_prob = 0
                                for score_str, prob in correct_score['scores'].items():
                                    if '-' in score_str and prob > max_prob:
                                        try:
                                            h, a = score_str.split('-')
                                            if h.isdigit() and a.isdigit():
                                                max_prob = prob
                                                home_score_pred = int(h)
                                                away_score_pred = int(a)
                                        except:
                                            pass
                            
                            new_prediction = SportMonksPrediction(
                                fixture_id=fixture['id'],
                                predictions_data=predictions,
                                home_win_probability=fulltime_result.get('home', 0) / 100.0,
                                draw_probability=fulltime_result.get('draw', 0) / 100.0,
                                away_win_probability=fulltime_result.get('away', 0) / 100.0,
                                btts_probability=btts.get('yes', 0) / 100.0 if btts else 0.5,
                                over_25_probability=over_25.get('yes', 0) / 100.0 if over_25 else 0.5,
                                under_25_probability=over_25.get('no', 0) / 100.0 if over_25 else 0.5,
                                predicted_home_score=home_score_pred,
                                predicted_away_score=away_score_pred,
                                confidence_score=0.75
                            )
                            db.session.add(new_prediction)
                            prediction_count += 1
            
            db.session.commit()
            
            logger.info(f"Sync complete: {fixture_count} fixtures, {team_count} teams, {prediction_count} predictions")
            return True
            
        except Exception as e:
            logger.error(f"Sync error: {str(e)}")
            db.session.rollback()
            return False