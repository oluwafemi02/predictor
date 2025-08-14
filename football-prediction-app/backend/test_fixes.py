#!/usr/bin/env python
"""
Test script to verify the fixes for:
1. API data storage issue
2. Page refresh routing issue
"""

import os
import sys
import requests
import time
from datetime import datetime

# Configuration
BASE_URL = os.environ.get('API_URL', 'http://localhost:5000')
API_KEY = os.environ.get('TEST_API_KEY', 'test-api-key')

def test_database_connection():
    """Test database connection and basic operations"""
    print("\n🔍 Testing Database Connection...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sync/test-database")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database connection successful")
            print(f"   - Team count: {data.get('team_count', 0)}")
            return True
        else:
            print(f"❌ Database test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Database test error: {str(e)}")
        return False

def test_sync_status():
    """Check current sync status"""
    print("\n📊 Checking Sync Status...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sync/status")
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            db_stats = stats.get('database', {})
            
            print(f"✅ Sync status retrieved:")
            print(f"   - Teams: {db_stats.get('teams', 0)}")
            print(f"   - Matches: {db_stats.get('matches', 0)}")
            print(f"   - SportMonks Fixtures: {db_stats.get('sportmonks_fixtures', 0)}")
            print(f"   - SportMonks Predictions: {db_stats.get('sportmonks_predictions', 0)}")
            
            return db_stats
        else:
            print(f"❌ Sync status failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Sync status error: {str(e)}")
        return None

def test_manual_sync():
    """Test manual data sync"""
    print("\n🔄 Testing Manual Data Sync...")
    
    headers = {'X-API-Key': API_KEY}
    
    try:
        # Test football-data.org sync
        print("   Syncing football-data.org...")
        response = requests.post(
            f"{BASE_URL}/api/sync/football-data/all",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', {})
            print(f"   ✅ Football data synced:")
            print(f"      - Teams: {results.get('teams', {})}")
            print(f"      - Matches: {results.get('matches', {})}")
        else:
            print(f"   ❌ Football data sync failed: {response.status_code}")
            if response.status_code == 401:
                print("      Note: API key required for sync endpoints")
        
        # Test SportMonks sync
        print("\n   Syncing SportMonks fixtures...")
        response = requests.post(
            f"{BASE_URL}/api/sync/sportmonks/fixtures",
            headers=headers,
            json={'days_ahead': 7}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SportMonks fixtures synced")
            stats = data.get('stats', {})
            print(f"      - Total fixtures: {stats.get('total_fixtures', 0)}")
        else:
            print(f"   ❌ SportMonks sync failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Manual sync error: {str(e)}")

def test_data_retrieval():
    """Test that synced data can be retrieved"""
    print("\n📥 Testing Data Retrieval...")
    
    # Test teams endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/teams")
        if response.status_code == 200:
            data = response.json()
            team_count = len(data.get('teams', []))
            print(f"✅ Teams endpoint working: {team_count} teams")
        else:
            print(f"❌ Teams endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Teams endpoint error: {str(e)}")
    
    # Test matches endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/matches")
        if response.status_code == 200:
            data = response.json()
            match_count = len(data.get('matches', []))
            print(f"✅ Matches endpoint working: {match_count} matches")
        else:
            print(f"❌ Matches endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Matches endpoint error: {str(e)}")

def test_spa_routing():
    """Test SPA routing for page refresh"""
    print("\n🌐 Testing SPA Routing...")
    
    routes_to_test = [
        '/',
        '/teams',
        '/matches',
        '/predictions',
        '/sportmonks',
        '/league-table',
        '/model-status'
    ]
    
    for route in routes_to_test:
        try:
            response = requests.get(f"{BASE_URL}{route}")
            if response.status_code == 200:
                # Check if we get HTML (React app) or JSON (API)
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type:
                    print(f"✅ Route {route} -> HTML (React app)")
                elif 'application/json' in content_type:
                    print(f"⚠️  Route {route} -> JSON (API response)")
                else:
                    print(f"❓ Route {route} -> {content_type}")
            else:
                print(f"❌ Route {route} -> {response.status_code}")
        except Exception as e:
            print(f"❌ Route {route} error: {str(e)}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Football Prediction App - Fix Verification")
    print(f"API URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test 1: Database and Data Storage
    print("\n🗄️  TESTING DATA STORAGE FIX")
    print("-" * 40)
    
    # Check database connection
    if test_database_connection():
        # Check current data status
        initial_stats = test_sync_status()
        
        # Try manual sync
        test_manual_sync()
        
        # Check status again
        print("\n📊 Re-checking Sync Status...")
        final_stats = test_sync_status()
        
        # Test data retrieval
        test_data_retrieval()
        
        # Summary
        if initial_stats and final_stats:
            print("\n📈 Data Storage Summary:")
            for key in ['teams', 'matches']:
                initial = initial_stats.get(key, 0)
                final = final_stats.get(key, 0)
                if final > initial:
                    print(f"   ✅ {key.capitalize()}: {initial} -> {final} (+{final-initial})")
                elif final == initial and final > 0:
                    print(f"   ✅ {key.capitalize()}: {final} (unchanged)")
                else:
                    print(f"   ⚠️  {key.capitalize()}: No data")
    
    # Test 2: Page Refresh / SPA Routing
    print("\n\n🔄 TESTING PAGE REFRESH FIX")
    print("-" * 40)
    test_spa_routing()
    
    # Final Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION COMPLETE")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("1. If data storage tests failed, check:")
    print("   - Database connection (DATABASE_URL)")
    print("   - API keys are configured")
    print("   - Scheduler worker is running")
    print("\n2. If page refresh tests show JSON instead of HTML:")
    print("   - Frontend might be on a different URL")
    print("   - Check https://football-prediction-frontend.onrender.com")
    print("\n3. Deploy changes to Render:")
    print("   - Commit and push changes")
    print("   - Monitor deployment logs")
    print("   - Run this test against production URL")

if __name__ == '__main__':
    main()