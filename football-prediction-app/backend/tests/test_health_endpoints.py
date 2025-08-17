"""
Test health check endpoints
"""
import pytest
from app import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


def test_healthz_endpoint(client):
    """Test simple health check endpoint"""
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_version_endpoint(client):
    """Test version endpoint"""
    response = client.get('/api/version')
    assert response.status_code == 200
    
    data = response.json
    assert 'version' in data
    assert 'environment' in data
    assert 'features' in data
    assert data['version'] == '1.0.0'


def test_api_health_endpoint(client):
    """Test detailed health endpoint"""
    response = client.get('/api/health')
    assert response.status_code in [200, 503]  # Can be unhealthy if DB not connected
    
    data = response.json
    assert 'status' in data
    assert 'services' in data
    assert 'timestamp' in data