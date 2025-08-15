import requests
import time
import statistics
from datetime import datetime

# Test endpoints
BASE_URL = "https://football-prediction-backend-2cvi.onrender.com"
FRONTEND_ORIGIN = "https://football-prediction-frontend-zx5z.onrender.com"

endpoints = [
    "/api/sportmonks/fixtures/upcoming?days=7&predictions=true",
    "/api/sportmonks/fixtures/upcoming?days=7&predictions=false",
    "/api/sportmonks/test-cors"
]

def test_endpoint(url, headers):
    """Test a single endpoint and return response time"""
    start_time = time.time()
    try:
        response = requests.get(url, headers=headers, timeout=30)
        end_time = time.time()
        response_time = end_time - start_time
        
        return {
            'url': url,
            'status': response.status_code,
            'time': response_time,
            'headers': dict(response.headers),
            'error': None
        }
    except Exception as e:
        end_time = time.time()
        return {
            'url': url,
            'status': None,
            'time': end_time - start_time,
            'headers': {},
            'error': str(e)
        }

def main():
    print(f"Testing API Performance - {datetime.now()}")
    print("=" * 80)
    
    # Headers to simulate frontend request
    headers = {
        'Origin': FRONTEND_ORIGIN,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    for endpoint in endpoints:
        url = BASE_URL + endpoint
        print(f"\nTesting: {endpoint}")
        
        # Test multiple times
        times = []
        for i in range(3):
            result = test_endpoint(url, headers)
            times.append(result['time'])
            
            print(f"  Attempt {i+1}:")
            print(f"    Status: {result['status']}")
            print(f"    Time: {result['time']:.2f}s")
            if result['error']:
                print(f"    Error: {result['error']}")
            
            # Check CORS headers
            cors_headers = {k: v for k, v in result['headers'].items() if 'access-control' in k.lower()}
            if cors_headers:
                print(f"    CORS Headers: {cors_headers}")
            else:
                print(f"    CORS Headers: None found!")
            
            time.sleep(1)  # Wait between requests
        
        # Calculate statistics
        if times:
            print(f"  Average response time: {statistics.mean(times):.2f}s")
            print(f"  Min/Max: {min(times):.2f}s / {max(times):.2f}s")

if __name__ == "__main__":
    main()