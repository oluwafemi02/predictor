import os
from dotenv import load_dotenv

load_dotenv()

# Helper function to get database URL
def get_database_url():
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    return database_url

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = get_database_url() or 'sqlite:///football_predictions.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Configuration
    FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')
    FOOTBALL_API_BASE_URL = 'https://api.football-data.org/v4/'  # Example API
    
    # RapidAPI Football Odds Configuration
    RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY') or '7de1fabbd3msh5a337f636c66c3dp144f56jsn18f9de3aa911'
    RAPIDAPI_HOST = 'api-football-v1.p.rapidapi.com'
    RAPIDAPI_ODDS_BASE_URL = 'https://api-football-v1.p.rapidapi.com/v2/odds'
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else [
        'http://localhost:3000',
        'http://localhost:5173',
        'https://football-prediction-frontend-zx5z.onrender.com',
        'https://*.onrender.com'
    ]
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'Access-Control-Allow-Origin']
    CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_SUPPORTS_CREDENTIALS = True
    
    # Pagination
    MATCHES_PER_PAGE = 20
    PREDICTIONS_PER_PAGE = 10
    
    # Model Configuration
    MODEL_UPDATE_INTERVAL = 3600  # Update model every hour
    PREDICTION_CONFIDENCE_THRESHOLD = 0.6
    
    # Cache Configuration
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
    # For production, use database URL or fall back to SQLite with warning
    SQLALCHEMY_DATABASE_URI = get_database_url() or 'sqlite:///football_predictions_temp.db'
    
    # Ensure we have a secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production!")

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}