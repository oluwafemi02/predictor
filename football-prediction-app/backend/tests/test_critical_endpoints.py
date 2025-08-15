"""
Test cases for critical API endpoints
Ensures core functionality works correctly with live APIs
"""

import pytest
import os
from datetime import datetime, timedelta
from app import create_app
from models import db, Match, Team, Prediction
from sportmonks_client import SportMonksAPIClient


class TestCriticalEndpoints:
    """Test suite for critical endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test app instance"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers if needed"""
        api_key = os.environ.get('TEST_API_KEY', 'test-key')
        return {'X-API-Key': api_key}
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] in ['healthy', 'unhealthy']
        assert 'services' in data
        assert 'timestamp' in data
    
    def test_cors_configuration(self, client):
        """Test CORS is properly configured"""
        response = client.options('/api/test-cors', headers={
            'Origin': 'https://football-prediction-frontend-zx5z.onrender.com',
            'Access-Control-Request-Method': 'GET'
        })
        
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_sportmonks_fixtures_endpoint(self, client):
        """Test SportMonks fixtures endpoint"""
        # Skip if no API key configured
        if not os.environ.get('SPORTMONKS_API_KEY') and not os.environ.get('SPORTMONKS_PRIMARY_TOKEN'):
            pytest.skip("SportMonks API key not configured")
        
        response = client.get('/api/sportmonks/fixtures/upcoming?days=1')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'fixtures' in data
        assert isinstance(data['fixtures'], list)
    
    def test_predictions_endpoint(self, client, app):
        """Test predictions endpoint with mock data"""
        with app.app_context():
            # Create test data
            team1 = Team(id=1, name='Test Team 1')
            team2 = Team(id=2, name='Test Team 2')
            db.session.add_all([team1, team2])
            
            match = Match(
                id=1,
                home_team_id=1,
                away_team_id=2,
                match_date=datetime.utcnow() + timedelta(days=1),
                status='scheduled',
                competition='Test League'
            )
            db.session.add(match)
            
            prediction = Prediction(
                match_id=1,
                home_win_probability=0.5,
                draw_probability=0.3,
                away_win_probability=0.2,
                confidence_score=0.75,
                model_version='test-v1'
            )
            db.session.add(prediction)
            db.session.commit()
        
        response = client.get('/api/v1/predictions')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'predictions' in data
        assert 'pagination' in data
    
    def test_matches_endpoint_filters(self, client, app):
        """Test matches endpoint with various filters"""
        with app.app_context():
            # Create test matches
            team1 = Team(id=1, name='Home Team')
            team2 = Team(id=2, name='Away Team')
            db.session.add_all([team1, team2])
            
            # Finished match
            finished_match = Match(
                home_team_id=1,
                away_team_id=2,
                match_date=datetime.utcnow() - timedelta(days=1),
                status='finished',
                home_score=2,
                away_score=1,
                competition='Premier League'
            )
            
            # Scheduled match
            scheduled_match = Match(
                home_team_id=1,
                away_team_id=2,
                match_date=datetime.utcnow() + timedelta(days=1),
                status='scheduled',
                competition='Premier League'
            )
            
            db.session.add_all([finished_match, scheduled_match])
            db.session.commit()
        
        # Test status filter
        response = client.get('/api/v1/matches?status=finished')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['matches']) == 1
        assert data['matches'][0]['status'] == 'finished'
        
        # Test date filter
        date_from = (datetime.utcnow() - timedelta(days=2)).isoformat()
        response = client.get(f'/api/v1/matches?date_from={date_from}')
        assert response.status_code == 200
    
    def test_error_handling(self, client):
        """Test error handling for invalid requests"""
        # Test 404
        response = client.get('/api/v1/matches/99999')
        assert response.status_code == 404
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'message' in data
        
        # Test invalid endpoint
        response = client.get('/api/v1/invalid-endpoint')
        assert response.status_code == 404
    
    def test_database_connection_pooling(self, client, app):
        """Test database connection pooling works correctly"""
        with app.app_context():
            from db_utils import ConnectionPoolManager
            
            # Get pool status
            pool_status = ConnectionPoolManager.get_pool_status()
            assert 'size' in pool_status
            assert 'checked_in' in pool_status
            assert pool_status['checked_in'] >= 0
    
    def test_sportmonks_client_initialization(self):
        """Test SportMonks client initializes correctly"""
        client = SportMonksAPIClient()
        
        # Check token configuration
        assert client.primary_token is not None or len(client.fallback_tokens) > 0
        
        # Test health check
        health_status = client.health_check()
        assert 'status' in health_status
        assert 'api_configured' in health_status
    
    @pytest.mark.integration
    def test_end_to_end_prediction_flow(self, client):
        """Test complete prediction flow from fixture to prediction"""
        # This test requires API keys to be configured
        if not os.environ.get('SPORTMONKS_API_KEY'):
            pytest.skip("Integration test requires API keys")
        
        # Get upcoming fixtures
        response = client.get('/api/sportmonks/fixtures/upcoming?days=1&limit=1')
        assert response.status_code == 200
        
        fixtures = response.get_json()['fixtures']
        if not fixtures:
            pytest.skip("No upcoming fixtures available")
        
        fixture_id = fixtures[0]['id']
        
        # Get predictions for fixture
        response = client.get(f'/api/sportmonks/predictions/{fixture_id}')
        # Should return data or gracefully handle if predictions not available
        assert response.status_code in [200, 404]
    
    def test_cache_functionality(self, client):
        """Test Redis caching works correctly"""
        # Make same request twice
        response1 = client.get('/api/sportmonks/leagues')
        response2 = client.get('/api/sportmonks/leagues')
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Second request should be faster (cached)
        # This is a simple test - in production you'd check Redis directly


@pytest.mark.performance
class TestPerformance:
    """Performance tests for critical endpoints"""
    
    def test_response_times(self, client):
        """Test that critical endpoints respond within acceptable time"""
        import time
        
        endpoints = [
            '/api/health',
            '/api/v1/matches',
            '/api/sportmonks/leagues',
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            response_time = time.time() - start_time
            
            # Should respond within 2 seconds
            assert response_time < 2.0, f"{endpoint} took {response_time}s"
            
            # Check for response time header
            if 'X-Response-Time' in response.headers:
                reported_time = float(response.headers['X-Response-Time'])
                assert reported_time < 2.0