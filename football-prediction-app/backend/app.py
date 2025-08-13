import os
from flask import Flask
from flask_cors import CORS
from models import db
from config import config
from api_routes import api_bp
# from real_data_routes import real_data_bp  # Temporarily disabled

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Register blueprints
    app.register_blueprint(api_bp)
    # app.register_blueprint(real_data_bp)  # Temporarily disabled
    
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
                }
            }
        }
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {'status': 'healthy', 'environment': config_name}
    
    return app

# Create app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)