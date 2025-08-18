"""
Minimal SportMonks sync - absolute minimum to get data flowing
"""
import os
import requests
from datetime import datetime
from flask import current_app

def minimal_sync():
    """Minimal sync - just get it working"""
    
    api_key = os.environ.get('SPORTMONKS_API_KEY')
    if not api_key:
        return False, "No API key"
    
    try:
        # Import inside app context
        from sportmonks_models import db, SportMonksFixture, SportMonksTeam, SportMonksLeague
        
        # Clear old data
        db.session.query(SportMonksFixture).delete()
        db.session.query(SportMonksTeam).delete() 
        db.session.query(SportMonksLeague).delete()
        db.session.commit()
        
        # Get today's fixtures
        headers = {"Authorization": api_key}
        today = datetime.utcnow().strftime('%Y-%m-%d')
        url = f"https://api.sportmonks.com/v3/football/fixtures/date/{today}"
        
        response = requests.get(url, headers=headers, params={"per_page": 100})
        
        if response.status_code != 200:
            return False, f"API error: {response.status_code}"
        
        data = response.json()
        fixtures = data.get('data', [])
        
        if not fixtures:
            return False, "No fixtures found"
        
        # Process fixtures
        for fixture in fixtures[:10]:  # Just first 10 for now
            try:
                # Create dummy teams if needed
                home_id = fixture.get('home_team_id', 0)
                away_id = fixture.get('away_team_id', 0)
                
                # If no team IDs in fixture, try participants
                participants = fixture.get('participants', [])
                for p in participants:
                    if p.get('meta', {}).get('location') == 'home':
                        home_id = p.get('id', home_id)
                    elif p.get('meta', {}).get('location') == 'away':
                        away_id = p.get('id', away_id)
                
                if home_id and away_id:
                    # Create teams if they don't exist
                    for team_id in [home_id, away_id]:
                        if not SportMonksTeam.query.filter_by(team_id=team_id).first():
                            team = SportMonksTeam(
                                team_id=team_id,
                                name=f"Team {team_id}",
                                short_code=f"T{team_id}",
                                logo_path=""
                            )
                            db.session.add(team)
                    
                    # Create fixture
                    new_fixture = SportMonksFixture(
                        fixture_id=fixture.get('id', 0),
                        league_id=fixture.get('league_id', 0),
                        league_name="League",
                        season_id=fixture.get('season_id', 0),
                        home_team_id=home_id,
                        away_team_id=away_id,
                        starting_at=datetime.utcnow(),  # Simple date for now
                        state_id=fixture.get('state_id', 0),
                        state_name=fixture.get('state', {}).get('name', 'Unknown')
                    )
                    db.session.add(new_fixture)
            except Exception as e:
                current_app.logger.error(f"Error processing fixture: {str(e)}")
                continue
        
        db.session.commit()
        
        # Count what we saved
        fixture_count = SportMonksFixture.query.count()
        team_count = SportMonksTeam.query.count()
        
        return True, f"Saved {fixture_count} fixtures, {team_count} teams"
        
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        return False, f"Error: {str(e)}"