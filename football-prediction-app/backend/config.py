import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///football_predictions.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Configuration
    FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')
    FOOTBALL_API_BASE_URL = 'https://api.football-data.org/v4/'  # Example API
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # CORS Configuration
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']  # React dev servers
    
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
    # Override any production-specific settings here

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}