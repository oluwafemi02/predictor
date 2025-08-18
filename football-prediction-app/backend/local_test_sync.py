#!/usr/bin/env python3
"""
Local test script to debug SportMonks sync
Run this locally to see what's happening
"""
import os
import requests
from datetime import datetime
import json

# Set your API key here or use environment variable
API_KEY = os.environ.get('SPORTMONKS_API_KEY', 'YOUR_API_KEY_HERE')

def test_sportmonks_locally():
    """Test SportMonks API locally to debug issues"""
    
    print("=" * 60)
    print("SportMonks Local Debug Test")
    print("=" * 60)
    
    if API_KEY == 'YOUR_API_KEY_HERE':
        print("❌ Please set your API key in the script or SPORTMONKS_API_KEY env var")
        return
    
    print(f"✅ Using API key: {API_KEY[:10]}...")
    
    headers = {"Authorization": API_KEY}
    
    # Test 1: Get today's fixtures
    print("\n📅 Fetching today's fixtures...")
    today = datetime.utcnow().strftime('%Y-%m-%d')
    url = f"https://api.sportmonks.com/v3/football/fixtures/date/{today}"
    
    response = requests.get(url, headers=headers, params={
        "per_page": 3,
        "include": "participants;league"
    })
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Error: {response.text[:500]}")
        return
    
    data = response.json()
    fixtures = data.get('data', [])
    
    print(f"✅ Found {len(fixtures)} fixtures")
    
    # Show fixture structure
    if fixtures:
        print("\n📊 First fixture structure:")
        fixture = fixtures[0]
        
        # Pretty print the fixture
        print(json.dumps(fixture, indent=2))
        
        print("\n🔍 Parsing fixture data:")
        print(f"ID: {fixture.get('id')}")
        print(f"League ID: {fixture.get('league_id')}")
        print(f"League: {fixture.get('league', {}).get('name', 'Unknown')}")
        
        # Parse participants
        participants = fixture.get('participants', [])
        print(f"\nParticipants: {len(participants)}")
        
        for p in participants:
            location = p.get('meta', {}).get('location', 'unknown')
            print(f"  - {p.get('name', 'Unknown')} ({location})")
            print(f"    ID: {p.get('id')}")
        
        # Check for teams in different places
        print("\n🔍 Checking for team IDs:")
        print(f"home_team_id: {fixture.get('home_team_id', 'Not found')}")
        print(f"away_team_id: {fixture.get('away_team_id', 'Not found')}")
        
        # Check scores
        print("\n📊 Scores:")
        scores = fixture.get('scores', [])
        for score in scores:
            if score.get('description') == 'CURRENT':
                s = score.get('score', {})
                print(f"Current: {s.get('home')} - {s.get('away')}")
        
        # Check state
        print(f"\nState: {fixture.get('state', {}).get('name', 'Unknown')} (ID: {fixture.get('state_id')})")
    
    # Test 2: Can we save to a test database?
    print("\n💾 Testing database save (using SQLite)...")
    try:
        import sqlite3
        
        # Create test database
        conn = sqlite3.connect(':memory:')
        c = conn.cursor()
        
        # Create simple tables
        c.execute('''CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT)''')
        c.execute('''CREATE TABLE fixtures (id INTEGER PRIMARY KEY, home_team_id INTEGER, away_team_id INTEGER)''')
        
        # Try to save data
        saved_teams = 0
        saved_fixtures = 0
        
        for fixture in fixtures[:3]:
            participants = fixture.get('participants', [])
            
            for p in participants:
                c.execute("INSERT OR IGNORE INTO teams (id, name) VALUES (?, ?)", 
                         (p.get('id'), p.get('name')))
                saved_teams += c.rowcount
            
            # Get team IDs
            home_id = None
            away_id = None
            
            for p in participants:
                if p.get('meta', {}).get('location') == 'home':
                    home_id = p.get('id')
                elif p.get('meta', {}).get('location') == 'away':
                    away_id = p.get('id')
            
            if home_id and away_id:
                c.execute("INSERT INTO fixtures (id, home_team_id, away_team_id) VALUES (?, ?, ?)",
                         (fixture.get('id'), home_id, away_id))
                saved_fixtures += c.rowcount
        
        conn.commit()
        
        # Check what we saved
        c.execute("SELECT COUNT(*) FROM teams")
        team_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM fixtures")
        fixture_count = c.fetchone()[0]
        
        print(f"✅ Saved {team_count} teams and {fixture_count} fixtures to test DB")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Debug test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_sportmonks_locally()