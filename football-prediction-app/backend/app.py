import os
from flask import Flask, request
from flask_cors import CORS
from models import db
from config import config
from api_routes import api_bp

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure CORS with more specific settings
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         allow_headers=app.config.get('CORS_ALLOW_HEADERS', ['Content-Type']),
         methods=app.config.get('CORS_ALLOW_METHODS', ['GET', 'POST']),
         supports_credentials=app.config.get('CORS_SUPPORTS_CREDENTIALS', False))
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Try to import and register real_data_bp
    try:
        from real_data_routes import real_data_bp
        app.register_blueprint(real_data_bp)
    except ImportError:
        print("Warning: real_data_routes not available")
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin and any(origin.startswith(allowed) or (allowed == '*') for allowed in app.config['CORS_ORIGINS']):
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Create database tables only if not in production or if explicitly requested
    # In production, we'll handle this separately to avoid startup issues
    if config_name != 'production':
        with app.app_context():
            try:
                db.create_all()
                print("Database tables created successfully")
            except Exception as e:
                print(f"Warning: Could not create database tables: {e}")
    
    @app.route('/')
    def index():
        return {
            'message': 'Football Prediction API',
            'version': '1.0',
            'status': 'running',
            'environment': config_name,
            'database': 'PostgreSQL' if 'postgresql' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'SQLite',
            'endpoints': {
                'odds': {
                    'leagues': '/api/v1/odds/leagues',
                    'bookmakers': '/api/v1/odds/bookmakers',
                    'league_odds': '/api/v1/odds/league/<league_id>',
                    'fixture_odds': '/api/v1/odds/fixture/<fixture_id>',
                    'date_odds': '/api/v1/odds/date/<YYYY-MM-DD>',
                    'match_odds': '/api/v1/odds/match/<match_id>',
                    'sync_league': '/api/v1/odds/sync/league/<league_id>',
                    'sync_match': '/api/v1/odds/sync/match/<match_id>'
                },
                'core': {
                    'matches': '/api/v1/matches',
                    'teams': '/api/v1/teams',
                    'predictions': '/api/v1/predictions',
                    'model_status': '/api/v1/model/status',
                    'model_train': '/api/v1/model/train'
                },
                'data': {
                    'initialize': '/api/v1/data/initialize',
                    'stats': '/api/v1/data/stats'
                }
            }
        }
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        db_status = 'unknown'
        db_error = None
        
        try:
            # Test database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            db_status = 'connected'
        except Exception as e:
            db_status = 'disconnected'
            db_error = str(e)
            
        return {
            'status': 'healthy',
            'environment': config_name,
            'database': {
                'status': db_status,
                'error': db_error,
                'uri_configured': bool(app.config.get('SQLALCHEMY_DATABASE_URI')),
                'is_postgresql': 'postgresql' in str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
            },
            'api_key_configured': bool(app.config.get('FOOTBALL_API_KEY'))
        }
    
    return app

# Create app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)