import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# Helper function to get database URL
def get_database_url():
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    return database_url

class Config:
    # Generate secure secret key - use environment variable in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = get_database_url() or 'sqlite:///football_predictions.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database connection pooling for better performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # API Configuration
    FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')
    FOOTBALL_API_BASE_URL = 'https://api.football-data.org/v4/'  # Example API
    
    # SportMonks API Configuration
    SPORTMONKS_API_KEY = os.environ.get('SPORTMONKS_API_KEY')
    SPORTMONKS_API_BASE_URL = 'https://api.sportmonks.com/v3/football'
    
    # RapidAPI Football Odds Configuration - REQUIRED in production
    RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
    if not RAPIDAPI_KEY and os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("RAPIDAPI_KEY environment variable must be set in production")
    RAPIDAPI_HOST = 'api-football-v1.p.rapidapi.com'
    RAPIDAPI_ODDS_BASE_URL = 'https://api-football-v1.p.rapidapi.com/v2/odds'
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # CORS Configuration - secure origins only
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else [
        'http://localhost:3000', 
        'http://localhost:5173',
        'https://football-prediction-frontend.onrender.com',  # Specific production domain
        'https://football-prediction-frontend-2cvi.onrender.com',  # Current production domain
        'https://football-prediction-frontend-zx5z.onrender.com'  # Your frontend domain
    ]
    
    # Scheduler Configuration
    ENABLE_SCHEDULER = os.environ.get('ENABLE_SCHEDULER', 'false').lower() == 'true'
    
    # Pagination
    MATCHES_PER_PAGE = 20
    PREDICTIONS_PER_PAGE = 10
    
    # Model Configuration
    MODEL_UPDATE_INTERVAL = 3600  # Update model every hour
    PREDICTION_CONFIDENCE_THRESHOLD = 0.6
    
    # Cache Configuration
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_LIVE_SCORES_TIMEOUT = 30  # 30 seconds for live data
    CACHE_PREDICTIONS_TIMEOUT = 1800  # 30 minutes for predictions
    CACHE_STATIC_DATA_TIMEOUT = 86400  # 24 hours for static data

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
    # For production, use database URL or raise error
    SQLALCHEMY_DATABASE_URI = get_database_url()
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL must be set in production!")
    
    # Ensure we have a secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production!")
    
    # Ensure we have encryption keys in production
    if not os.environ.get('TOKEN_ENCRYPTION_PASSWORD'):
        raise ValueError("TOKEN_ENCRYPTION_PASSWORD must be set in production!")
    if not os.environ.get('TOKEN_ENCRYPTION_SALT'):
        raise ValueError("TOKEN_ENCRYPTION_SALT must be set in production!")
    
    # Stricter CORS in production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []
    if not CORS_ORIGINS:
        raise ValueError("CORS_ORIGINS must be set in production!")

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}