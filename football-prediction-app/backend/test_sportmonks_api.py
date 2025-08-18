#!/usr/bin/env python3
"""
Test SportMonks API connection and diagnose issues
"""
import os
import requests
from datetime import datetime, timedelta
import json

def test_sportmonks():
    api_key = os.environ.get('SPORTMONKS_API_KEY')
    if not api_key:
        print("❌ No SPORTMONKS_API_KEY found in environment variables!")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    headers = {"Authorization": api_key}
    base_url = "https://api.sportmonks.com/v3/football"
    
    # Test 1: Basic API connection
    print("\n📡 Testing API connection...")
    try:
        response = requests.get(f"{base_url}/leagues", headers=headers, params={"per_page": 1})
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ API Key is invalid or expired!")
            return False
        elif response.status_code == 403:
            print("❌ API Key doesn't have permission for this endpoint!")
            return False
        elif response.status_code == 200:
            print("✅ API connection successful!")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    
    # Test 2: Get today's fixtures
    print("\n📅 Checking today's fixtures...")
    today = datetime.utcnow().strftime('%Y-%m-%d')
    try:
        url = f"{base_url}/fixtures/date/{today}"
        response = requests.get(url, headers=headers, params={
            "include": "participants;league",
            "per_page": 10
        })
        
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('data', [])
            print(f"Found {len(fixtures)} fixtures for today ({today})")
            
            if fixtures:
                print("\nSample fixture:")
                fixture = fixtures[0]
                participants = fixture.get('participants', [])
                if len(participants) >= 2:
                    home = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
                    away = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
                    print(f"  {home.get('name', 'Unknown')} vs {away.get('name', 'Unknown')}")
                    print(f"  League: {fixture.get('league', {}).get('name', 'Unknown')}")
                    print(f"  Time: {fixture.get('starting_at', 'Unknown')}")
        else:
            print(f"❌ Failed to get fixtures: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Error getting fixtures: {str(e)}")
    
    # Test 3: Get fixtures for date range
    print("\n📆 Checking fixtures for next 7 days...")
    start_date = datetime.utcnow().strftime('%Y-%m-%d')
    end_date = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    try:
        url = f"{base_url}/fixtures/between/{start_date}/{end_date}"
        response = requests.get(url, headers=headers, params={
            "include": "participants;league;predictions",
            "per_page": 50
        })
        
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('data', [])
            print(f"Found {len(fixtures)} fixtures between {start_date} and {end_date}")
            
            # Count by league
            leagues = {}
            for fixture in fixtures:
                league_name = fixture.get('league', {}).get('name', 'Unknown')
                leagues[league_name] = leagues.get(league_name, 0) + 1
            
            print("\nFixtures by league:")
            for league, count in sorted(leagues.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {league}: {count}")
        else:
            print(f"❌ Failed to get date range fixtures: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Error getting date range fixtures: {str(e)}")
    
    # Test 4: Check specific leagues
    print("\n🏆 Checking major leagues...")
    league_ids = [8, 564, 384, 82, 301]  # Premier League, La Liga, Serie A, Bundesliga, Ligue 1
    
    for league_id in league_ids:
        try:
            url = f"{base_url}/leagues/{league_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                league = response.json().get('data', {})
                print(f"✅ League {league_id}: {league.get('name', 'Unknown')}")
            else:
                print(f"❌ League {league_id}: Not accessible (status {response.status_code})")
        except Exception as e:
            print(f"❌ League {league_id}: Error - {str(e)}")
    
    return True

if __name__ == "__main__":
    print("🔍 SportMonks API Diagnostic Test")
    print("=" * 50)
    test_sportmonks()