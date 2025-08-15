import os
import atexit
from datetime import datetime
from flask import Flask, jsonify, send_from_directory, request, make_response
from flask_cors import CORS
from models import db
from config import config
from api_routes import api_bp
from exceptions import FootballAPIError, ValidationError, APIKeyError
from security import add_security_headers
from logging_config import setup_logging, get_logger
import redis
from config import Config

# Initialize logging
setup_logging()
logger = get_logger(__name__)

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure CORS with explicit settings
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         allow_headers=['Content-Type', 'Authorization', 'Access-Control-Allow-Origin', 'X-API-Key', 'Accept'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
         supports_credentials=True,
         expose_headers=['Content-Type', 'Authorization'],
         send_wildcard=False,
         max_age=3600)  # Cache preflight requests for 1 hour
    
    # Log CORS configuration for debugging
    logger.info(f"CORS configured with origins: {app.config['CORS_ORIGINS']}")
    
    # Add explicit OPTIONS handler for preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            origin = request.headers.get('Origin')
            # Log the incoming origin for debugging
            logger.info(f"OPTIONS request from origin: {origin}")
            
            if origin and origin in app.config['CORS_ORIGINS']:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Headers'] = "Content-Type,Authorization,X-API-Key,Accept"
                response.headers['Access-Control-Allow-Methods'] = "GET,POST,PUT,DELETE,OPTIONS"
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Max-Age'] = '3600'
                logger.info(f"CORS headers set for origin: {origin}")
            else:
                logger.warning(f"Origin {origin} not in allowed origins: {app.config['CORS_ORIGINS']}")
            return response
    
    # Initialize JWT authentication
    try:
        from auth import init_jwt
        jwt = init_jwt(app)
    except ImportError:
        print("Warning: JWT authentication not available")
    
    # Add security headers to all responses
    app.after_request(add_security_headers)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Register auth routes
    try:
        from auth_routes import auth_bp
        from auth import User  # Import User model
        app.register_blueprint(auth_bp)
        print("Authentication routes registered successfully")
    except ImportError as e:
        print(f"Warning: Authentication routes not available: {str(e)}")
    
    # Try to import and register real_data_bp
    try:
        from real_data_routes import real_data_bp
        app.register_blueprint(real_data_bp)
    except ImportError:
        print("Warning: real_data_routes not available")
    
    # Try to import and register SportMonks routes
    try:
        from sportmonks_routes import sportmonks_bp
        app.register_blueprint(sportmonks_bp)
        print("SportMonks routes registered successfully")
    except ImportError as e:
        print(f"Warning: SportMonks routes not available: {str(e)}")
    
    # Register enhanced predictions blueprint
    try:
        from enhanced_predictions_route import enhanced_predictions_bp
        app.register_blueprint(enhanced_predictions_bp)
        print("Enhanced predictions routes registered successfully")
    except ImportError as e:
        print(f"Warning: Enhanced predictions routes not available: {str(e)}")
    
    # Register sync routes
    try:
        from sync_routes import sync_bp
        app.register_blueprint(sync_bp)
        print("Sync routes registered successfully")
    except ImportError as e:
        print(f"Warning: Sync routes not available: {str(e)}")
    
    # Error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = {
            'status': 'error',
            'message': error.message,
            'type': 'validation_error'
        }
        if error.field:
            response['field'] = error.field
        return jsonify(response), error.status_code
    
    @app.errorhandler(APIKeyError)
    def handle_api_key_error(error):
        return jsonify({
            'status': 'error',
            'message': error.message,
            'type': 'api_key_error'
        }), error.status_code
    
    @app.errorhandler(FootballAPIError)
    def handle_football_api_error(error):
        return jsonify({
            'status': 'error',
            'message': error.message,
            'type': 'api_error'
        }), error.status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        # Check if this is an API route
        if error.request.path.startswith('/api/'):
            return jsonify({
                'status': 'error',
                'message': 'Resource not found',
                'type': 'not_found_error'
            }), 404
        # For non-API routes, serve the React app
        return app.send_static_file('index.html')
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'type': 'internal_error'
        }), 500
    
    # Create database tables only if not in production or if explicitly requested
    # In production, we'll handle this separately to avoid startup issues
    if config_name != 'production':
        with app.app_context():
            try:
                db.create_all()
                print("Database tables created successfully")
            except Exception as e:
                print(f"Warning: Could not create database tables: {e}")
    
    # Import and initialize scheduler if enabled
    if app.config.get('ENABLE_SCHEDULER', False):
        try:
            from scheduler import init_scheduler
            scheduler = init_scheduler(app)
            app.scheduler = scheduler
            
            # Also initialize SportMonks scheduler
            from sportmonks_scheduler import sportmonks_scheduler
            sportmonks_scheduler.init_app(app)
            if not sportmonks_scheduler.scheduler.running:
                sportmonks_scheduler.start()
                app.sportmonks_scheduler = sportmonks_scheduler
                print("SportMonks scheduler initialized and started")
            
        except ImportError as e:
            print(f"Warning: Scheduler not available: {str(e)}")
        except Exception as e:
            print(f"Error initializing scheduler: {str(e)}")
    
    # Set up monitoring
    try:
        from monitoring import setup_monitoring
        monitor = setup_monitoring(app)
        print("Monitoring initialized successfully")
    except ImportError as e:
        print(f"Warning: Monitoring not available: {str(e)}")
    except Exception as e:
        print(f"Error initializing monitoring: {str(e)}")
    
    # CORS test endpoint
    @app.route('/api/test-cors', methods=['GET', 'OPTIONS'])
    def test_cors():
        """Simple endpoint to test CORS configuration"""
        import time
        start_time = time.time()
        response = jsonify({
            'status': 'success',
            'message': 'CORS is working correctly',
            'timestamp': datetime.utcnow().isoformat(),
            'origin': request.headers.get('Origin', 'No origin header'),
            'allowed_origins': app.config.get('CORS_ORIGINS', [])
        })
        response.headers['X-Response-Time'] = f"{time.time() - start_time:.3f}"
        return response
    
    @app.route('/')
    def index():
        # Serve React app for root route
        if os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return app.send_static_file('index.html')
        # Otherwise, return API info
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
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint to verify all services are configured and running"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Check database connection
        try:
            db.session.execute('SELECT 1')
            health_status['services']['database'] = {
                'status': 'connected',
                'type': 'PostgreSQL' if 'postgresql' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'SQLite'
            }
        except Exception as e:
            health_status['services']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Check Redis connection
        try:
            redis_client = redis.from_url(Config.REDIS_URL)
            redis_client.ping()
            health_status['services']['redis'] = {'status': 'connected'}
        except Exception as e:
            health_status['services']['redis'] = {
                'status': 'error',
                'error': 'Redis not available'
            }
        
        # Check SportMonks API configuration
        sportmonks_configured = bool(
            os.environ.get('SPORTMONKS_API_KEY') or 
            os.environ.get('SPORTMONKS_PRIMARY_TOKEN')
        )
        health_status['services']['sportmonks'] = {
            'status': 'configured' if sportmonks_configured else 'not_configured',
            'has_primary_token': bool(os.environ.get('SPORTMONKS_PRIMARY_TOKEN')),
            'has_fallback_tokens': bool(os.environ.get('SPORTMONKS_FALLBACK_TOKENS'))
        }
        
        # Check CORS configuration
        health_status['services']['cors'] = {
            'status': 'configured',
            'allowed_origins': app.config.get('CORS_ORIGINS', []),
            'frontend_configured': 'https://football-prediction-frontend-zx5z.onrender.com' in app.config.get('CORS_ORIGINS', [])
        }
        
        return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503
    
    # Catch-all route for React app - must be last
    @app.route('/<path:path>')
    def serve_react_app(path):
        # Serve static files if they exist
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        # Otherwise serve the React app
        return app.send_static_file('index.html')
    
    return app

# Create app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)