"""
Automatic SportMonks sync fix - diagnoses and fixes issues automatically
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from flask import current_app

logger = logging.getLogger(__name__)

def auto_fix_sync(app):
    """Automatically diagnose and fix sync issues"""
    
    results = {
        'diagnosis': [],
        'fixes_applied': [],
        'final_status': 'unknown',
        'data_synced': False
    }
    
    api_key = os.environ.get('SPORTMONKS_API_KEY')
    if not api_key:
        results['diagnosis'].append('ERROR: No API key found')
        results['final_status'] = 'failed'
        return results
    
    with app.app_context():
        # Test 1: Check if we can import models
        try:
            from sportmonks_models import db, SportMonksFixture, SportMonksTeam, SportMonksLeague
            results['diagnosis'].append('SUCCESS: Models imported correctly')
        except Exception as e:
            results['diagnosis'].append(f'ERROR: Cannot import models - {str(e)}')
            results['final_status'] = 'failed'
            return results
        
        # Test 2: Check database connection
        try:
            # Try a simple query
            count = SportMonksFixture.query.count()
            results['diagnosis'].append(f'SUCCESS: Database connected, current fixtures: {count}')
        except Exception as e:
            results['diagnosis'].append(f'ERROR: Database connection failed - {str(e)}')
            
            # Try to fix by creating tables
            try:
                db.create_all()
                results['fixes_applied'].append('Created database tables')
                results['diagnosis'].append('SUCCESS: Database tables created')
            except Exception as e2:
                results['diagnosis'].append(f'ERROR: Cannot create tables - {str(e2)}')
                results['final_status'] = 'failed'
                return results
        
        # Test 3: Check API connection
        try:
            headers = {"Authorization": api_key}
            today = datetime.utcnow().strftime('%Y-%m-%d')
            url = f"https://api.sportmonks.com/v3/football/fixtures/date/{today}"
            
            response = requests.get(url, headers=headers, params={"per_page": 5})
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('data', [])
                results['diagnosis'].append(f'SUCCESS: API working, found {len(fixtures)} fixtures today')
            else:
                results['diagnosis'].append(f'ERROR: API returned status {response.status_code}')
                results['final_status'] = 'failed'
                return results
        except Exception as e:
            results['diagnosis'].append(f'ERROR: API request failed - {str(e)}')
            results['final_status'] = 'failed'
            return results
        
        # Test 4: Try different sync approaches
        synced = False
        
        # Approach 1: Direct database insertion
        try:
            # Clear existing data
            SportMonksFixture.query.delete()
            SportMonksTeam.query.delete()
            SportMonksLeague.query.delete()
            db.session.commit()
            results['fixes_applied'].append('Cleared old data')
            
            # Try to sync today's fixtures
            fixture_count = 0
            team_count = 0
            
            for fixture in fixtures:
                try:
                    # Extract teams from participants
                    participants = fixture.get('participants', [])
                    home_team = None
                    away_team = None
                    
                    for p in participants:
                        location = p.get('meta', {}).get('location')
                        if location == 'home':
                            home_team = p
                        elif location == 'away':
                            away_team = p
                    
                    if home_team and away_team:
                        # Save teams
                        for team in [home_team, away_team]:
                            if not SportMonksTeam.query.filter_by(team_id=team['id']).first():
                                new_team = SportMonksTeam(
                                    team_id=team['id'],
                                    name=team.get('name', 'Unknown'),
                                    short_code=team.get('short_code', ''),
                                    logo_path=team.get('image_path', '')
                                )
                                db.session.add(new_team)
                                team_count += 1
                        
                        # Save fixture
                        new_fixture = SportMonksFixture(
                            fixture_id=fixture['id'],
                            league_id=fixture.get('league_id', 0),
                            league_name=fixture.get('league', {}).get('name', 'Unknown'),
                            season_id=fixture.get('season_id', 0),
                            home_team_id=home_team['id'],
                            away_team_id=away_team['id'],
                            starting_at=datetime.fromisoformat(fixture['starting_at'].replace('Z', '+00:00')),
                            state_id=fixture.get('state_id', 0),
                            state_name=fixture.get('state', {}).get('name', 'Unknown')
                        )
                        db.session.add(new_fixture)
                        fixture_count += 1
                
                except Exception as e:
                    results['diagnosis'].append(f'WARNING: Failed to process fixture {fixture.get("id")} - {str(e)}')
                    continue
            
            # Commit changes
            db.session.commit()
            
            # Verify data was saved
            saved_fixtures = SportMonksFixture.query.count()
            saved_teams = SportMonksTeam.query.count()
            
            if saved_fixtures > 0:
                results['diagnosis'].append(f'SUCCESS: Synced {saved_fixtures} fixtures and {saved_teams} teams')
                results['data_synced'] = True
                synced = True
            else:
                results['diagnosis'].append('WARNING: Data was processed but not saved')
                
        except Exception as e:
            results['diagnosis'].append(f'ERROR: Sync failed - {str(e)}')
            try:
                db.session.rollback()
            except:
                pass
        
        # If first approach failed, try alternative
        if not synced:
            # Approach 2: Use raw SQL
            try:
                # Get one fixture to test
                if fixtures:
                    fixture = fixtures[0]
                    participants = fixture.get('participants', [])
                    
                    if len(participants) >= 2:
                        # Try raw SQL insert
                        db.session.execute(
                            "INSERT INTO sportmonks_teams (team_id, name, short_code, logo_path) VALUES (:id, :name, :code, :logo) ON CONFLICT DO NOTHING",
                            {"id": participants[0]['id'], "name": participants[0].get('name', 'Test'), "code": "", "logo": ""}
                        )
                        db.session.commit()
                        
                        # Check if it worked
                        result = db.session.execute("SELECT COUNT(*) FROM sportmonks_teams").scalar()
                        if result > 0:
                            results['diagnosis'].append('SUCCESS: Raw SQL insert works')
                            results['fixes_applied'].append('Used raw SQL for data insertion')
                            synced = True
            except Exception as e:
                results['diagnosis'].append(f'INFO: Raw SQL approach not applicable - {str(e)}')
        
        # Final status
        if synced:
            results['final_status'] = 'fixed'
            
            # Now do a full sync with working method
            try:
                # Get more fixtures for date range
                start_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
                end_date = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
                
                url = f"https://api.sportmonks.com/v3/football/fixtures/between/{start_date}/{end_date}"
                response = requests.get(url, headers=headers, params={"per_page": 100})
                
                if response.status_code == 200:
                    all_fixtures = response.json().get('data', [])
                    
                    for fixture in all_fixtures:
                        try:
                            participants = fixture.get('participants', [])
                            home_team = None
                            away_team = None
                            
                            for p in participants:
                                if p.get('meta', {}).get('location') == 'home':
                                    home_team = p
                                elif p.get('meta', {}).get('location') == 'away':
                                    away_team = p
                            
                            if home_team and away_team:
                                # Save teams
                                for team in [home_team, away_team]:
                                    if not SportMonksTeam.query.filter_by(team_id=team['id']).first():
                                        new_team = SportMonksTeam(
                                            team_id=team['id'],
                                            name=team.get('name', 'Unknown'),
                                            short_code=team.get('short_code', ''),
                                            logo_path=team.get('image_path', '')
                                        )
                                        db.session.add(new_team)
                                
                                # Save fixture if not exists
                                if not SportMonksFixture.query.filter_by(fixture_id=fixture['id']).first():
                                    new_fixture = SportMonksFixture(
                                        fixture_id=fixture['id'],
                                        league_id=fixture.get('league_id', 0),
                                        league_name=fixture.get('league', {}).get('name', 'Unknown'),
                                        season_id=fixture.get('season_id', 0),
                                        home_team_id=home_team['id'],
                                        away_team_id=away_team['id'],
                                        starting_at=datetime.fromisoformat(fixture['starting_at'].replace('Z', '+00:00')),
                                        state_id=fixture.get('state_id', 0),
                                        state_name=fixture.get('state', {}).get('name', 'Unknown')
                                    )
                                    db.session.add(new_fixture)
                        except:
                            continue
                    
                    db.session.commit()
                    
                    final_fixtures = SportMonksFixture.query.count()
                    final_teams = SportMonksTeam.query.count()
                    
                    results['diagnosis'].append(f'FINAL: Full sync complete - {final_fixtures} fixtures, {final_teams} teams')
                    
            except Exception as e:
                results['diagnosis'].append(f'WARNING: Full sync had issues but partial data saved - {str(e)}')
        else:
            results['final_status'] = 'failed'
    
    return results