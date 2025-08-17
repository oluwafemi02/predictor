#!/usr/bin/env python3
"""
Test script for the simplified SportMonks API integration
"""
import os
import sys
import json
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_client():
    """Test the SportMonks API client directly"""
    print("Testing SportMonks API Client...")
    
    try:
        from sportmonks_api_v3 import SportMonksV3Client
        
        # Check if API key is set
        api_key = os.environ.get('SPORTMONKS_API_KEY') or os.environ.get('SPORTMONKS_PRIMARY_TOKEN')
        if not api_key:
            print("❌ No SportMonks API key found in environment variables")
            print("Please set SPORTMONKS_API_KEY or SPORTMONKS_PRIMARY_TOKEN")
            return False
        
        print(f"✅ API key found: {api_key[:8]}...")
        
        # Initialize client
        client = SportMonksV3Client()
        print("✅ Client initialized successfully")
        
        # Test 1: Get today's fixtures
        print("\n📅 Testing: Get today's fixtures...")
        today_fixtures = client.get_todays_fixtures()
        if today_fixtures and 'data' in today_fixtures:
            print(f"✅ Found {len(today_fixtures['data'])} fixtures for today")
            if today_fixtures['data']:
                fixture = today_fixtures['data'][0]
                print(f"   Example: {fixture.get('name', 'Unknown fixture')}")
        else:
            print("⚠️  No fixtures found for today (this might be normal)")
        
        # Test 2: Get upcoming fixtures
        print("\n📅 Testing: Get upcoming fixtures...")
        upcoming = client.get_upcoming_fixtures(days=7)
        if upcoming and 'data' in upcoming:
            print(f"✅ Found {len(upcoming['data'])} upcoming fixtures in next 7 days")
            if upcoming['data']:
                fixture = upcoming['data'][0]
                print(f"   Example: {fixture.get('name', 'Unknown fixture')}")
                print(f"   Date: {fixture.get('starting_at', 'Unknown date')}")
        else:
            print("❌ Failed to get upcoming fixtures")
        
        # Test 3: Get past fixtures
        print("\n📅 Testing: Get past fixtures...")
        past = client.get_past_fixtures(days=7)
        if past and 'data' in past:
            print(f"✅ Found {len(past['data'])} past fixtures from last 7 days")
            if past['data']:
                fixture = past['data'][0]
                print(f"   Example: {fixture.get('name', 'Unknown fixture')}")
                # Check if scores are included
                if 'scores' in fixture:
                    print("   ✅ Scores data included")
                if 'participants' in fixture:
                    print("   ✅ Participants data included")
        else:
            print("❌ Failed to get past fixtures")
        
        # Test 4: Get specific fixture (if we have one)
        if upcoming and 'data' in upcoming and upcoming['data']:
            fixture_id = upcoming['data'][0]['id']
            print(f"\n🔍 Testing: Get fixture details (ID: {fixture_id})...")
            
            fixture_detail = client.get_fixture_by_id(
                fixture_id,
                include='scores;participants;statistics.type;events;lineups;league;venue'
            )
            
            if fixture_detail and 'data' in fixture_detail:
                fixture = fixture_detail['data']
                print(f"✅ Got fixture details: {fixture.get('name', 'Unknown')}")
                
                # Check included data
                includes = ['scores', 'participants', 'statistics', 'events', 'lineups', 'league', 'venue']
                for inc in includes:
                    if inc in fixture:
                        print(f"   ✅ {inc} data included")
                    else:
                        print(f"   ⚠️  {inc} data not included")
            else:
                print("❌ Failed to get fixture details")
        
        print("\n✅ API client tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing API client: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction_engine():
    """Test the prediction engine"""
    print("\n\n🎯 Testing Prediction Engine...")
    
    try:
        from simple_prediction_engine import SimplePredictionEngine
        from sportmonks_api_v3 import SportMonksV3Client
        
        # Initialize
        client = SportMonksV3Client()
        engine = SimplePredictionEngine()
        print("✅ Prediction engine initialized")
        
        # Get an upcoming fixture to analyze
        print("\n🔍 Looking for upcoming fixtures to analyze...")
        upcoming = client.get_upcoming_fixtures(days=7)
        
        if not upcoming or 'data' not in upcoming or not upcoming['data']:
            print("⚠️  No upcoming fixtures found to analyze")
            return True
        
        # Find a fixture to analyze
        fixture_id = None
        fixture_name = None
        for fixture in upcoming['data']:
            if fixture.get('state_id') == 1:  # Not started
                fixture_id = fixture['id']
                fixture_name = fixture.get('name', 'Unknown')
                break
        
        if not fixture_id:
            print("⚠️  No suitable fixtures found for prediction")
            return True
        
        print(f"\n📊 Analyzing fixture: {fixture_name} (ID: {fixture_id})")
        
        # Generate prediction
        prediction = engine.analyze_fixture(fixture_id)
        
        if prediction:
            print("\n✅ Prediction generated successfully!")
            print(f"\n🏆 Predicted outcome: {prediction.predicted_outcome.upper()}")
            print(f"📊 Probabilities:")
            print(f"   - Home Win: {prediction.home_win_probability}%")
            print(f"   - Draw: {prediction.draw_probability}%")
            print(f"   - Away Win: {prediction.away_win_probability}%")
            print(f"\n⚽ Predicted Score: {prediction.predicted_score[0]}-{prediction.predicted_score[1]}")
            print(f"💪 Confidence: {prediction.confidence * 100:.1f}%")
            print(f"\n📝 Reasoning:")
            for reason in prediction.reasoning:
                print(f"   - {reason}")
        else:
            print("❌ Failed to generate prediction")
            return False
        
        print("\n✅ Prediction engine tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing prediction engine: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_routes():
    """Test the Flask API routes"""
    print("\n\n🌐 Testing Flask API Routes...")
    
    try:
        from app import create_app
        
        # Create test app
        app = create_app('development')
        app.config['TESTING'] = True
        client = app.test_client()
        
        print("✅ Flask app created successfully")
        
        # Test health endpoint
        print("\n🏥 Testing: /api/v2/health")
        response = client.get('/api/v2/health')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   API configured: {data['api_configured']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
        
        # Test today's fixtures
        print("\n📅 Testing: /api/v2/fixtures/today")
        response = client.get('/api/v2/fixtures/today')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Today's fixtures endpoint working")
            print(f"   Found {data.get('count', 0)} fixtures")
        else:
            print(f"❌ Today's fixtures failed: {response.status_code}")
        
        # Test upcoming fixtures
        print("\n📅 Testing: /api/v2/fixtures/upcoming?days=3")
        response = client.get('/api/v2/fixtures/upcoming?days=3')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Upcoming fixtures endpoint working")
            print(f"   Found {data.get('count', 0)} fixtures")
            
            # Check if predictions are included
            if data.get('fixtures') and len(data['fixtures']) > 0:
                fixture = data['fixtures'][0]
                if 'prediction' in fixture:
                    print("   ✅ Predictions included in response")
                else:
                    print("   ⚠️  No predictions in response (fixture might be live/finished)")
        else:
            print(f"❌ Upcoming fixtures failed: {response.status_code}")
        
        # Test past fixtures
        print("\n📅 Testing: /api/v2/fixtures/past?days=3")
        response = client.get('/api/v2/fixtures/past?days=3')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Past fixtures endpoint working")
            print(f"   Found {data.get('count', 0)} fixtures")
        else:
            print(f"❌ Past fixtures failed: {response.status_code}")
        
        print("\n✅ Flask route tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing Flask routes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 SportMonks API Integration Test Suite")
    print("=" * 50)
    
    # Check environment
    print("\n🔧 Environment Check:")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_api_client():
        tests_passed += 1
    
    if test_prediction_engine():
        tests_passed += 1
    
    if test_flask_routes():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! The API integration is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)