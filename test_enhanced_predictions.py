#!/usr/bin/env python3
"""
Test script for the enhanced prediction system
"""

import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:5000"  # Update this to your backend URL
API_VERSION = "/api/v1/predictions"

def test_health_check():
    """Test the health check endpoint"""
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}{API_VERSION}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_single_fixture_prediction(fixture_id=19427455):
    """Test enhanced prediction for a single fixture"""
    print(f"\n2. Testing single fixture prediction (ID: {fixture_id})...")
    try:
        response = requests.get(f"{BASE_URL}{API_VERSION}/enhanced/{fixture_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFixture: {data['fixture']['home_team']} vs {data['fixture']['away_team']}")
            print(f"Date: {data['fixture']['date']}")
            print(f"\nPrediction:")
            print(f"  Home Win: {data['prediction']['match_result']['home_win']:.1f}%")
            print(f"  Draw: {data['prediction']['match_result']['draw']:.1f}%")
            print(f"  Away Win: {data['prediction']['match_result']['away_win']:.1f}%")
            print(f"\nExpected Goals:")
            print(f"  Home: {data['prediction']['goals']['predicted_home']}")
            print(f"  Away: {data['prediction']['goals']['predicted_away']}")
            print(f"\nConfidence Score: {data['confidence_score']:.1f}%")
            print(f"\nAI Summary: {data['summary']}")
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_upcoming_predictions():
    """Test upcoming predictions endpoint"""
    print("\n3. Testing upcoming predictions...")
    try:
        # Get predictions for next 7 days
        params = {
            'date_from': datetime.now().strftime('%Y-%m-%d'),
            'date_to': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'min_confidence': 60,
            'league_id': 8  # Premier League
        }
        
        response = requests.get(f"{BASE_URL}{API_VERSION}/enhanced/upcoming", params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFound {data['count']} predictions")
            print(f"Date Range: {data['date_range']['from']} to {data['date_range']['to']}")
            
            # Show first 3 predictions
            for i, pred in enumerate(data['predictions'][:3]):
                print(f"\n--- Prediction {i+1} ---")
                print(f"Match: {pred['fixture']['home_team']} vs {pred['fixture']['away_team']}")
                print(f"Date: {pred['fixture']['date']}")
                print(f"Confidence: {pred['confidence']:.1f}%")
                
                if pred.get('recommended_bet'):
                    bet = pred['recommended_bet']
                    print(f"Best Bet: {bet['type']} - {bet['selection']} ({bet['probability']:.1f}%)")
            
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_batch_predictions():
    """Test batch predictions endpoint"""
    print("\n4. Testing batch predictions...")
    try:
        # Test with multiple fixture IDs
        fixture_ids = [19427455, 19427473, 19427500]  # Use actual fixture IDs
        
        response = requests.post(
            f"{BASE_URL}{API_VERSION}/enhanced/batch",
            json={'fixture_ids': fixture_ids}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nRequested: {data['requested']} fixtures")
            print(f"Successful: {data['successful']}")
            print(f"Failed: {data['failed']}")
            
            # Show summary of predictions
            for pred in data['predictions']:
                print(f"\n{pred['home_team']} vs {pred['away_team']}")
                print(f"  Confidence: {pred['confidence']:.1f}%")
                print(f"  Summary: {pred['summary']}")
            
            return True
        else:
            print(f"Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Enhanced Prediction System Test ===")
    print(f"Testing against: {BASE_URL}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Single Fixture", test_single_fixture_prediction),
        ("Upcoming Predictions", test_upcoming_predictions),
        ("Batch Predictions", test_batch_predictions)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\nTest '{name}' failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n\n=== Test Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The enhanced prediction system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()