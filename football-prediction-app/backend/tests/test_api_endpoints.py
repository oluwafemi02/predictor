"""
Tests for API Endpoints
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock
from app import create_app
from models import db, Team, Match, Prediction


class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers"""
        return {
            'X-API-Key': 'test-api-key',
            'Content-Type': 'application/json'
        }
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_get_teams(self, client, app):
        """Test get teams endpoint"""
        # Add test teams
        with app.app_context():
            team1 = Team(name="Manchester United", code="MUN")
            team2 = Team(name="Liverpool", code="LIV")
            db.session.add_all([team1, team2])
            db.session.commit()
        
        response = client.get('/api/teams')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]['name'] == "Manchester United"
    
    def test_get_teams_with_search(self, client, app):
        """Test get teams with search parameter"""
        with app.app_context():
            team1 = Team(name="Manchester United", code="MUN")
            team2 = Team(name="Manchester City", code="MCI")
            team3 = Team(name="Liverpool", code="LIV")
            db.session.add_all([team1, team2, team3])
            db.session.commit()
        
        response = client.get('/api/teams?search=Manchester')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
    
    @patch('unified_prediction_engine.UnifiedPredictionEngine')
    def test_create_prediction(self, mock_engine, client, app):
        """Test create prediction endpoint"""
        # Mock prediction result
        mock_instance = mock_engine.return_value
        mock_instance.predict_match.return_value = Mock(
            home_win_probability=0.6,
            draw_probability=0.25,
            away_win_probability=0.15,
            predicted_outcome='home',
            confidence=60.0,
            predicted_score=(2, 1),
            over_25_probability=0.65,
            btts_yes_probability=0.55,
            key_factors=['Home advantage', 'Good form'],
            reasoning=['Team A in excellent form'],
            risk_assessment='low',
            value_bet_suggestions=[]
        )
        
        # Create teams and match
        with app.app_context():
            team1 = Team(id=1, name="Team A", code="TMA")
            team2 = Team(id=2, name="Team B", code="TMB")
            match = Match(
                id=1,
                home_team_id=1,
                away_team_id=2,
                match_date=datetime.utcnow()
            )
            db.session.add_all([team1, team2, match])
            db.session.commit()
        
        response = client.post(
            '/api/predictions/1',
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert 'prediction' in data
        assert data['prediction']['home_win_probability'] == 0.6
    
    def test_get_predictions(self, client, app):
        """Test get predictions endpoint"""
        with app.app_context():
            # Create test data
            team1 = Team(id=1, name="Team A", code="TMA")
            team2 = Team(id=2, name="Team B", code="TMB")
            match = Match(
                id=1,
                home_team_id=1,
                away_team_id=2,
                match_date=datetime.utcnow()
            )
            prediction = Prediction(
                match_id=1,
                home_win_probability=0.5,
                draw_probability=0.3,
                away_win_probability=0.2,
                predicted_outcome='home',
                confidence_score=0.7,
                prediction_data=json.dumps({
                    'key_factors': ['Test factor']
                })
            )
            db.session.add_all([team1, team2, match, prediction])
            db.session.commit()
        
        response = client.get('/api/predictions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) > 0
    
    def test_get_upcoming_matches(self, client, app):
        """Test get upcoming matches endpoint"""
        with app.app_context():
            team1 = Team(id=1, name="Team A", code="TMA")
            team2 = Team(id=2, name="Team B", code="TMB")
            
            # Create future match
            future_match = Match(
                home_team_id=1,
                away_team_id=2,
                match_date=datetime.utcnow().replace(year=2025)
            )
            
            db.session.add_all([team1, team2, future_match])
            db.session.commit()
        
        response = client.get('/api/matches/upcoming')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options('/api/teams')
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_error_handling(self, client):
        """Test error handling for non-existent resource"""
        response = client.get('/api/matches/99999')
        assert response.status_code == 404
    
    @patch('requests.get')
    def test_sportmonks_fixtures(self, mock_get, client):
        """Test SportMonks fixtures endpoint"""
        # Mock SportMonks API response
        mock_get.return_value.json.return_value = {
            'data': [{
                'id': 123,
                'home_team_id': 1,
                'away_team_id': 2,
                'starting_at': '2024-08-17 15:00:00'
            }]
        }
        mock_get.return_value.status_code = 200
        
        response = client.get('/api/sportmonks/fixtures/today')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'fixtures' in data
    
    def test_pagination(self, client, app):
        """Test pagination parameters"""
        with app.app_context():
            # Create multiple teams
            for i in range(25):
                team = Team(name=f"Team {i}", code=f"T{i}")
                db.session.add(team)
            db.session.commit()
        
        # Test default pagination
        response = client.get('/api/teams')
        data = json.loads(response.data)
        assert len(data) <= 20  # Default page size
        
        # Test custom page size
        response = client.get('/api/teams?page=2&per_page=10')
        data = json.loads(response.data)
        assert len(data) <= 10


class TestAuthentication:
    """Test authentication and authorization"""
    
    @pytest.fixture
    def app(self):
        """Create test app with auth enabled"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['REQUIRE_API_KEY'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @patch('security.validate_api_key')
    def test_valid_api_key(self, mock_validate, client):
        """Test request with valid API key"""
        mock_validate.return_value = True
        
        response = client.get(
            '/api/teams',
            headers={'X-API-Key': 'valid-key'}
        )
        assert response.status_code == 200
    
    @patch('security.validate_api_key')
    def test_invalid_api_key(self, mock_validate, client):
        """Test request with invalid API key"""
        mock_validate.return_value = False
        
        response = client.get(
            '/api/teams',
            headers={'X-API-Key': 'invalid-key'}
        )
        assert response.status_code == 401
    
    def test_missing_api_key(self, client):
        """Test request without API key"""
        response = client.get('/api/teams')
        assert response.status_code == 401


class TestDataValidation:
    """Test data validation"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app('testing')
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_invalid_match_id(self, client):
        """Test prediction with invalid match ID"""
        response = client.post(
            '/api/predictions/invalid',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
    
    def test_invalid_date_format(self, client):
        """Test invalid date format in query"""
        response = client.get('/api/matches?date=invalid-date')
        assert response.status_code == 400
    
    def test_invalid_pagination(self, client):
        """Test invalid pagination parameters"""
        response = client.get('/api/teams?page=-1')
        assert response.status_code == 400
        
        response = client.get('/api/teams?per_page=1000')
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])