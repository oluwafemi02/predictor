"""
Direct SportMonks sync - simpler version that just works
"""
import os
import logging
from datetime import datetime, timedelta
from sportmonks_models import db, SportMonksLeague, SportMonksTeam, SportMonksFixture, SportMonksPrediction
import requests

logger = logging.getLogger(__name__)

def direct_sync(app):
    """Direct sync - no filters, just get data"""
    
    api_key = os.environ.get('SPORTMONKS_API_KEY')
    if not api_key:
        return False, "No API key"
    
    headers = {"Authorization": api_key}
    
    with app.app_context():
        try:
            # Clear old data
            SportMonksPrediction.query.delete()
            SportMonksFixture.query.delete()
            SportMonksTeam.query.delete()
            SportMonksLeague.query.delete()
            db.session.commit()
            
            # Get today's fixtures first
            today = datetime.utcnow().strftime('%Y-%m-%d')
            url = f"https://api.sportmonks.com/v3/football/fixtures/date/{today}"
            
            response = requests.get(url, headers=headers, params={
                "include": "participants;league;venue;state;scores;predictions.type",
                "per_page": 100
            })
            
            if response.status_code != 200:
                return False, f"API error: {response.status_code}"
            
            data = response.json()
            fixtures = data.get('data', [])
            
            fixture_count = 0
            team_count = 0
            
            # Process each fixture
            for fixture in fixtures:
                try:
                    # Save league
                    league = fixture.get('league', {})
                    if league:
                        existing = SportMonksLeague.query.filter_by(league_id=league['id']).first()
                        if not existing:
                            new_league = SportMonksLeague(
                                league_id=league['id'],
                                name=league.get('name', 'Unknown'),
                                country=league.get('country', {}).get('name', 'Unknown')
                            )
                            db.session.add(new_league)
                    
                    # Get teams
                    participants = fixture.get('participants', [])
                    home_team = None
                    away_team = None
                    
                    for p in participants:
                        if p.get('meta', {}).get('location') == 'home':
                            home_team = p
                        elif p.get('meta', {}).get('location') == 'away':
                            away_team = p
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Save teams
                    for team in [home_team, away_team]:
                        existing = SportMonksTeam.query.filter_by(team_id=team['id']).first()
                        if not existing:
                            new_team = SportMonksTeam(
                                team_id=team['id'],
                                name=team.get('name', 'Unknown'),
                                short_code=team.get('short_code', ''),
                                logo_path=team.get('image_path', '')
                            )
                            db.session.add(new_team)
                            team_count += 1
                    
                    # Save fixture
                    existing = SportMonksFixture.query.filter_by(fixture_id=fixture['id']).first()
                    if not existing:
                        # Get score
                        home_score = None
                        away_score = None
                        scores = fixture.get('scores', [])
                        for score in scores:
                            if score.get('description') == 'CURRENT':
                                s = score.get('score', {})
                                home_score = s.get('home')
                                away_score = s.get('away')
                                break
                        
                        new_fixture = SportMonksFixture(
                            fixture_id=fixture['id'],
                            league_id=fixture.get('league_id'),
                            league_name=league.get('name', 'Unknown'),
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
                        
                        # Add predictions for upcoming matches
                        predictions = fixture.get('predictions', [])
                        if predictions and fixture.get('state_id') in [1, 2, 3, 4]:
                            pred_data = {}
                            
                            for pred in predictions:
                                pred_type = pred.get('type', {}).get('developer_name', '')
                                values = pred.get('predictions', {})
                                
                                if pred_type == 'FULLTIME_RESULT_PROBABILITY':
                                    pred_data['home_win'] = values.get('home', 0) / 100.0
                                    pred_data['draw'] = values.get('draw', 0) / 100.0
                                    pred_data['away_win'] = values.get('away', 0) / 100.0
                                elif pred_type == 'BTTS_PROBABILITY':
                                    pred_data['btts'] = values.get('yes', 0) / 100.0
                            
                            new_pred = SportMonksPrediction(
                                fixture_id=fixture['id'],
                                predictions_data=predictions,
                                home_win_probability=pred_data.get('home_win', 0.33),
                                draw_probability=pred_data.get('draw', 0.33),
                                away_win_probability=pred_data.get('away_win', 0.33),
                                btts_probability=pred_data.get('btts', 0.5),
                                over_25_probability=0.5,
                                under_25_probability=0.5,
                                predicted_home_score=1,
                                predicted_away_score=1,
                                confidence_score=0.75
                            )
                            db.session.add(new_pred)
                
                except Exception as e:
                    logger.error(f"Error processing fixture: {str(e)}")
                    continue
            
            db.session.commit()
            return True, f"Synced {fixture_count} fixtures, {team_count} teams"
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)