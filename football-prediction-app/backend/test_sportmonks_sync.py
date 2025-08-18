"""
Test script to verify SportMonks sync is working
Run this after deployment to test the sync endpoint
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

def test_sportmonks_sync():
    """Test the SportMonks sync endpoint"""
    print(f"\n=== Testing SportMonks Sync at {BASE_URL} ===\n")
    
    # 1. Check health
    print("1. Checking API health...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        health_data = response.json()
        sportmonks_status = health_data.get('services', {}).get('sportmonks', {})
        print(f"   SportMonks configured: {sportmonks_status.get('status')}")
    except Exception as e:
        print(f"   Error checking health: {e}")
    
    # 2. Trigger sync
    print("\n2. Triggering SportMonks data sync...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/data/sync-sportmonks")
        if response.status_code == 200:
            print("   ✅ Sync completed successfully!")
        else:
            print(f"   ❌ Sync failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error triggering sync: {e}")
    
    # 3. Check fixtures
    print("\n3. Checking fixtures endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/fixtures?page_size=5")
        data = response.json()
        if 'data_source' in data:
            print(f"   Data source: {data['data_source']}")
        print(f"   Fixtures count: {len(data.get('matches', []))}")
        
        # Show first fixture
        if data.get('matches'):
            fixture = data['matches'][0]
            print(f"\n   Sample fixture:")
            print(f"   - {fixture['home_team']['name']} vs {fixture['away_team']['name']}")
            print(f"   - Date: {fixture['date']}")
            print(f"   - Competition: {fixture['competition']}")
    except Exception as e:
        print(f"   Error checking fixtures: {e}")
    
    # 4. Check predictions
    print("\n4. Checking predictions endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/predictions?page_size=5")
        data = response.json()
        if 'data_source' in data:
            print(f"   Data source: {data['data_source']}")
        print(f"   Predictions count: {len(data.get('predictions', []))}")
        
        # Show first prediction
        if data.get('predictions'):
            pred = data['predictions'][0]
            print(f"\n   Sample prediction:")
            print(f"   - Match: {pred['match']['home_team']['name']} vs {pred['match']['away_team']['name']}")
            print(f"   - Home win: {pred['prediction']['home_win']*100:.1f}%")
            print(f"   - Draw: {pred['prediction']['draw']*100:.1f}%")
            print(f"   - Away win: {pred['prediction']['away_win']*100:.1f}%")
    except Exception as e:
        print(f"   Error checking predictions: {e}")
    
    # 5. Check teams
    print("\n5. Checking teams endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/teams?page_size=5")
        data = response.json()
        if 'data_source' in data:
            print(f"   Data source: {data['data_source']}")
        print(f"   Teams count: {len(data.get('teams', []))}")
    except Exception as e:
        print(f"   Error checking teams: {e}")
    
    print("\n=== Test Complete ===\n")

if __name__ == "__main__":
    test_sportmonks_sync()