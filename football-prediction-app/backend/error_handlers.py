"""
Enhanced Error Handlers for Football Prediction App
Provides user-friendly error messages and proper logging
"""

import logging
from flask import jsonify, request
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from exceptions import FootballAPIError, ValidationError, APIKeyError
import traceback

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register all error handlers with the Flask app"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors with friendly messages"""
        logger.warning(f"Validation error: {str(error)} - Request: {request.url}")
        
        response = {
            'error': 'Validation Error',
            'message': str(error),
            'details': 'Please check your input and try again.',
            'status_code': 400
        }
        
        # Add field-specific errors if available
        if hasattr(error, 'field'):
            response['field'] = error.field
            response['hint'] = get_validation_hint(error.field)
        
        return jsonify(response), 400
    
    @app.errorhandler(APIKeyError)
    def handle_api_key_error(error):
        """Handle API key errors"""
        logger.warning(f"API key error: {str(error)} - IP: {request.remote_addr}")
        
        return jsonify({
            'error': 'Authentication Error',
            'message': 'Invalid or missing API key.',
            'details': 'Please provide a valid API key in the X-API-Key header.',
            'status_code': 401
        }), 401
    
    @app.errorhandler(FootballAPIError)
    def handle_football_api_error(error):
        """Handle external Football API errors"""
        logger.error(f"Football API error: {str(error)}")
        
        # Provide user-friendly messages based on error type
        if 'rate limit' in str(error).lower():
            message = "We're receiving too many requests. Please try again in a few minutes."
            details = "Our data provider has rate limits to ensure service quality."
        elif 'not found' in str(error).lower():
            message = "The requested data could not be found."
            details = "This match or team data may not be available yet."
        else:
            message = "We're having trouble fetching the latest data."
            details = "Please try again later or contact support if the issue persists."
        
        return jsonify({
            'error': 'Data Provider Error',
            'message': message,
            'details': details,
            'status_code': error.status_code if hasattr(error, 'status_code') else 503
        }), error.status_code if hasattr(error, 'status_code') else 503
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        """Handle database errors"""
        logger.error(f"Database error: {str(error)}", exc_info=True)
        
        # Don't expose internal database details
        return jsonify({
            'error': 'Database Error',
            'message': 'We encountered a problem accessing our database.',
            'details': 'Our team has been notified. Please try again later.',
            'status_code': 500
        }), 500
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors with helpful messages"""
        logger.info(f"404 error: {request.url}")
        
        # Provide helpful suggestions based on the URL
        path = request.path
        suggestions = []
        
        if '/api/teams' in path:
            suggestions.append("Try /api/teams to list all teams")
            suggestions.append("Use /api/teams?search=name to search teams")
        elif '/api/matches' in path:
            suggestions.append("Try /api/matches/upcoming for upcoming matches")
            suggestions.append("Use /api/matches?date=YYYY-MM-DD for specific date")
        elif '/api/predictions' in path:
            suggestions.append("Try /api/predictions/main for main predictions")
            suggestions.append("POST to /api/predictions/{match_id} to create prediction")
        
        return jsonify({
            'error': 'Not Found',
            'message': f"The requested URL {path} was not found.",
            'details': 'Please check the URL and try again.',
            'suggestions': suggestions,
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 method not allowed errors"""
        logger.info(f"405 error: {request.method} {request.url}")
        
        return jsonify({
            'error': 'Method Not Allowed',
            'message': f"The {request.method} method is not allowed for this endpoint.",
            'details': f"Allowed methods: {', '.join(error.valid_methods) if hasattr(error, 'valid_methods') else 'See API documentation'}",
            'status_code': 405
        }), 405
    
    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle rate limiting errors"""
        logger.warning(f"Rate limit exceeded: {request.remote_addr}")
        
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'You have made too many requests.',
            'details': 'Please wait a moment before making more requests.',
            'retry_after': error.retry_after if hasattr(error, 'retry_after') else 60,
            'status_code': 429
        }), 429
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors"""
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        
        # Log the full traceback for debugging
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Oops! Something went wrong on our end.',
            'details': 'Our team has been notified and is working on it.',
            'reference': request.headers.get('X-Request-ID', 'N/A'),
            'status_code': 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Catch-all handler for unexpected errors"""
        logger.error(f"Unexpected error: {type(error).__name__}: {str(error)}", exc_info=True)
        
        # Handle HTTPException
        if isinstance(error, HTTPException):
            return jsonify({
                'error': error.name,
                'message': error.description,
                'status_code': error.code
            }), error.code
        
        # Generic error response
        return jsonify({
            'error': 'Unexpected Error',
            'message': 'An unexpected error occurred.',
            'details': 'Please try again or contact support if the issue persists.',
            'status_code': 500
        }), 500
    
    @app.before_request
    def log_request_info():
        """Log incoming request information"""
        logger.debug(f"Request: {request.method} {request.url} - IP: {request.remote_addr}")
    
    @app.after_request
    def log_response_info(response):
        """Log response information"""
        logger.debug(f"Response: {response.status_code} - Size: {response.content_length or 0}")
        return response


def get_validation_hint(field):
    """Get helpful hints for validation errors"""
    hints = {
        'date': 'Date should be in YYYY-MM-DD format',
        'team_id': 'Team ID should be a positive integer',
        'match_id': 'Match ID should be a positive integer',
        'page': 'Page number should be a positive integer',
        'per_page': 'Items per page should be between 1 and 100',
        'search': 'Search term should be at least 2 characters long',
        'season': 'Season should be in YYYY/YYYY format (e.g., 2023/2024)',
        'league_id': 'League ID should be a positive integer',
        'confidence': 'Confidence should be between 0 and 100'
    }
    
    return hints.get(field, 'Please check the format of your input')


def create_error_response(error_type, message, details=None, status_code=400, **kwargs):
    """Create a standardized error response"""
    response = {
        'error': error_type,
        'message': message,
        'status_code': status_code
    }
    
    if details:
        response['details'] = details
    
    # Add any additional fields
    response.update(kwargs)
    
    return jsonify(response), status_code


# Custom exception classes for better error handling
class PredictionError(Exception):
    """Raised when prediction generation fails"""
    def __init__(self, message="Failed to generate prediction", details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class DataNotFoundError(Exception):
    """Raised when required data is not found"""
    def __init__(self, resource, identifier=None):
        self.resource = resource
        self.identifier = identifier
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message)


class ExternalAPIError(Exception):
    """Raised when external API calls fail"""
    def __init__(self, api_name, message, status_code=None):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(f"{api_name} API error: {message}")