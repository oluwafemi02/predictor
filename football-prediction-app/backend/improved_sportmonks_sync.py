"""
Improved SportMonks sync with better error handling and flexibility
"""
import os
import logging
from datetime import datetime, timedelta
from sportmonks_models import db, SportMonksLeague, SportMonksTeam, SportMonksFixture, SportMonksPrediction
import requests
import time

logger = logging.getLogger(__name__)

def improved_sync(app, days_back=7, days_forward=30, max_fixtures=500):
    """
    Improved sync with flexible parameters and better error handling
    
    Args:
        app: Flask app instance
        days_back: Number of days to look back for fixtures
        days_forward: Number of days to look forward for fixtures
        max_fixtures: Maximum number of fixtures to sync
    """
    
    api_key = os.environ.get('SPORTMONKS_API_KEY')
    if not api_key:
        logger.error("No SportMonks API key found")
        return False, "No API key configured"
    
    base_url = "https://api.sportmonks.com/v3/football"
    headers = {"Authorization": api_key}
    
    with app.app_context():
        try:
            # Clear existing data for fresh sync
            logger.info("Clearing existing SportMonks data...")
            SportMonksPrediction.query.delete()
            SportMonksFixture.query.delete()
            SportMonksTeam.query.delete()
            SportMonksLeague.query.delete()
            db.session.commit()
            
            # 1. First, try to get fixtures without any filters
            logger.info(f"Fetching fixtures for {days_back} days back to {days_forward} days forward...")
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            end_date = (datetime.utcnow() + timedelta(days=days_forward)).strftime('%Y-%m-%d')
            
            all_fixtures = []
            page = 1
            
            while len(all_fixtures) < max_fixtures:
                fixtures_url = f"{base_url}/fixtures/between/{start_date}/{end_date}"
                params = {
                    "include": "participants;league;venue;state;scores;predictions.type",
                    "page": page,
                    "per_page": 100
                }
                
                logger.info(f"Requesting page {page}...")
                response = requests.get(fixtures_url, headers=headers, params=params)
                
                if response.status_code == 429:
                    logger.warning("Rate limited, waiting 60 seconds...")
                    time.sleep(60)
                    continue
                
                if response.status_code != 200:
                    logger.error(f"API error: {response.status_code} - {response.text[:500]}")
                    break
                
                data = response.json()
                fixtures = data.get('data', [])
                
                if not fixtures:
                    logger.info(f"No more fixtures on page {page}")
                    break
                
                all_fixtures.extend(fixtures)
                logger.info(f"Got {len(fixtures)} fixtures from page {page}, total: {len(all_fixtures)}")
                
                # Check if there are more pages
                if not data.get('meta', {}).get('has_more', False):
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting
            
            logger.info(f"Total fixtures fetched: {len(all_fixtures)}")
            
            if not all_fixtures:
                # Try alternative approach - get by specific dates
                logger.info("No fixtures found in date range, trying daily approach...")
                for day_offset in range(-days_back, days_forward + 1):
                    date = (datetime.utcnow() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
                    url = f"{base_url}/fixtures/date/{date}"
                    
                    response = requests.get(url, headers=headers, params={
                        "include": "participants;league;venue;state;scores;predictions.type",
                        "per_page": 50
                    })
                    
                    if response.status_code == 200:
                        fixtures = response.json().get('data', [])
                        if fixtures:
                            all_fixtures.extend(fixtures)
                            logger.info(f"Found {len(fixtures)} fixtures for {date}")
                    
                    if len(all_fixtures) >= max_fixtures:
                        break
                    
                    time.sleep(0.5)  # Rate limiting
            
            # Process fixtures
            fixture_count = 0
            team_count = 0
            prediction_count = 0
            league_ids = set()
            
            for fixture in all_fixtures[:max_fixtures]:
                try:
                    # Save league if not exists
                    league = fixture.get('league', {})
                    if league and league.get('id') not in league_ids:
                        league_ids.add(league['id'])
                        existing_league = SportMonksLeague.query.filter_by(league_id=league['id']).first()
                        if not existing_league:
                            new_league = SportMonksLeague(
                                league_id=league['id'],
                                name=league.get('name', 'Unknown League'),
                                country=league.get('country', {}).get('name', 'Unknown')
                            )
                            db.session.add(new_league)
                    
                    # Extract teams from participants
                    participants = fixture.get('participants', [])
                    home_team = None
                    away_team = None
                    
                    for participant in participants:
                        location = participant.get('meta', {}).get('location')
                        if location == 'home':
                            home_team = participant
                        elif location == 'away':
                            away_team = participant
                    
                    if not home_team or not away_team:
                        logger.warning(f"Fixture {fixture.get('id')} missing teams")
                        continue
                    
                    # Save teams
                    for team_data in [home_team, away_team]:
                        existing_team = SportMonksTeam.query.filter_by(team_id=team_data['id']).first()
                        if not existing_team:
                            new_team = SportMonksTeam(
                                team_id=team_data['id'],
                                name=team_data.get('name', 'Unknown Team'),
                                short_code=team_data.get('short_code', ''),
                                logo_path=team_data.get('image_path', '')
                            )
                            db.session.add(new_team)
                            team_count += 1
                    
                    # Check if fixture already exists
                    existing_fixture = SportMonksFixture.query.filter_by(fixture_id=fixture['id']).first()
                    if not existing_fixture:
                        # Get scores
                        home_score = None
                        away_score = None
                        scores = fixture.get('scores', [])
                        for score in scores:
                            if score.get('description') == 'CURRENT':
                                score_data = score.get('score', {})
                                home_score = score_data.get('home')
                                away_score = score_data.get('away')
                                break
                        
                        # Create fixture
                        new_fixture = SportMonksFixture(
                            fixture_id=fixture['id'],
                            league_id=fixture.get('league_id'),
                            league_name=league.get('name', 'Unknown League'),
                            season_id=fixture.get('season_id'),
                            home_team_id=home_team['id'],
                            away_team_id=away_team['id'],
                            starting_at=datetime.fromisoformat(fixture['starting_at'].replace('Z', '+00:00')),
                            home_score=home_score,
                            away_score=away_score,
                            venue_id=fixture.get('venue_id'),
                            venue_name=fixture.get('venue', {}).get('name'),
                            state_id=fixture.get('state_id'),
                            state_name=fixture.get('state', {}).get('name', 'Unknown')
                        )
                        db.session.add(new_fixture)
                        fixture_count += 1
                        
                        # Save predictions for upcoming fixtures
                        predictions = fixture.get('predictions', [])
                        if predictions and fixture.get('state_id') in [1, 2, 3, 4]:  # Not finished
                            # Process predictions
                            prediction_data = {}
                            
                            for pred in predictions:
                                pred_type = pred.get('type', {}).get('developer_name', '')
                                pred_values = pred.get('predictions', {})
                                
                                if pred_type == 'FULLTIME_RESULT_PROBABILITY':
                                    prediction_data['home_win'] = pred_values.get('home', 0) / 100.0
                                    prediction_data['draw'] = pred_values.get('draw', 0) / 100.0
                                    prediction_data['away_win'] = pred_values.get('away', 0) / 100.0
                                elif pred_type == 'BTTS_PROBABILITY':
                                    prediction_data['btts'] = pred_values.get('yes', 0) / 100.0
                                elif pred_type == 'OVER_UNDER_2_5_PROBABILITY':
                                    prediction_data['over_25'] = pred_values.get('yes', 0) / 100.0
                                    prediction_data['under_25'] = pred_values.get('no', 0) / 100.0
                                elif pred_type == 'CORRECT_SCORE_PROBABILITY':
                                    # Find most likely score
                                    max_prob = 0
                                    best_score = (0, 0)
                                    for score_key, prob in pred_values.items():
                                        if '-' in score_key and prob > max_prob:
                                            max_prob = prob
                                            parts = score_key.split('-')
                                            if len(parts) == 2:
                                                try:
                                                    best_score = (int(parts[0]), int(parts[1]))
                                                except ValueError:
                                                    pass
                                    prediction_data['predicted_home_score'] = best_score[0]
                                    prediction_data['predicted_away_score'] = best_score[1]
                            
                            if prediction_data:
                                new_prediction = SportMonksPrediction(
                                    fixture_id=fixture['id'],
                                    predictions_data=predictions,
                                    home_win_probability=prediction_data.get('home_win', 0.33),
                                    draw_probability=prediction_data.get('draw', 0.33),
                                    away_win_probability=prediction_data.get('away_win', 0.33),
                                    btts_probability=prediction_data.get('btts', 0.5),
                                    over_25_probability=prediction_data.get('over_25', 0.5),
                                    under_25_probability=prediction_data.get('under_25', 0.5),
                                    predicted_home_score=prediction_data.get('predicted_home_score', 1),
                                    predicted_away_score=prediction_data.get('predicted_away_score', 1),
                                    confidence_score=0.75
                                )
                                db.session.add(new_prediction)
                                prediction_count += 1
                
                except Exception as e:
                    logger.error(f"Error processing fixture {fixture.get('id')}: {str(e)}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            message = f"Sync complete: {fixture_count} fixtures, {team_count} teams, {prediction_count} predictions"
            logger.info(message)
            return True, message
            
        except Exception as e:
            logger.error(f"Sync error: {str(e)}")
            db.session.rollback()
            return False, str(e)