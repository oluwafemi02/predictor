"""
Centralized error handling module for consistent error management
"""

import logging
import functools
import traceback
from typing import Callable, Dict, Any, Optional, Tuple
from flask import jsonify, request
from datetime import datetime
from exceptions import (
    FootballAPIError, 
    ValidationError, 
    APIKeyError, 
    DataNotFoundError,
    ExternalAPIError
)
from models import db

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response structure"""
    
    @staticmethod
    def create(
        error: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        """Create a standardized error response"""
        response = {
            'status': 'error',
            'error': error,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path if request else None,
            'method': request.method if request else None
        }
        
        if details:
            response['details'] = details
            
        if request_id:
            response['request_id'] = request_id
            
        return response, status_code


def handle_api_errors(func: Callable) -> Callable:
    """
    Decorator for handling API errors consistently
    Wraps function calls and converts exceptions to proper API responses
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        request_id = request.headers.get('X-Request-ID', None)
        
        try:
            return func(*args, **kwargs)
            
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e.message}")
            return ErrorResponse.create(
                error='validation_error',
                message=e.message,
                status_code=e.status_code,
                details={'field': e.field} if e.field else None,
                request_id=request_id
            )
            
        except APIKeyError as e:
            logger.error(f"API key error in {func.__name__}: {e.message}")
            return ErrorResponse.create(
                error='authentication_error',
                message=e.message,
                status_code=e.status_code,
                request_id=request_id
            )
            
        except DataNotFoundError as e:
            logger.info(f"Data not found in {func.__name__}: {e.message}")
            return ErrorResponse.create(
                error='not_found',
                message=e.message,
                status_code=e.status_code,
                details={'resource': e.resource} if e.resource else None,
                request_id=request_id
            )
            
        except ExternalAPIError as e:
            logger.error(f"External API error in {func.__name__}: {e.message}")
            return ErrorResponse.create(
                error='external_service_error',
                message=e.message,
                status_code=e.status_code,
                details={'service': e.service} if e.service else None,
                request_id=request_id
            )
            
        except FootballAPIError as e:
            logger.error(f"Football API error in {func.__name__}: {e.message}")
            return ErrorResponse.create(
                error='api_error',
                message=e.message,
                status_code=e.status_code,
                details=e.payload,
                request_id=request_id
            )
            
        except Exception as e:
            # Log full traceback for unexpected errors
            logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            
            # Rollback any pending database transactions
            try:
                db.session.rollback()
            except:
                pass
            
            # Return generic error in production, detailed in development
            if request and request.app.config.get('DEBUG'):
                return ErrorResponse.create(
                    error='internal_error',
                    message=str(e),
                    status_code=500,
                    details={'traceback': traceback.format_exc()},
                    request_id=request_id
                )
            else:
                return ErrorResponse.create(
                    error='internal_error',
                    message='An unexpected error occurred. Please try again later.',
                    status_code=500,
                    request_id=request_id
                )
                
    return wrapper


def validate_request_data(schema: Dict[str, Any]) -> Callable:
    """
    Decorator for validating request data against a schema
    
    Args:
        schema: Dictionary defining expected fields and their types
        
    Example:
        @validate_request_data({
            'team_id': {'type': int, 'required': True},
            'season': {'type': str, 'required': False, 'default': '2023'}
        })
        def create_team_stats():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json() if request.is_json else {}
            
            # Validate each field in schema
            for field, rules in schema.items():
                field_type = rules.get('type', str)
                required = rules.get('required', False)
                default = rules.get('default', None)
                
                value = data.get(field)
                
                # Check required fields
                if required and value is None:
                    raise ValidationError(f"Field '{field}' is required", field=field)
                
                # Set default if not provided
                if value is None and default is not None:
                    data[field] = default
                    continue
                
                # Type validation
                if value is not None:
                    try:
                        if field_type == int:
                            data[field] = int(value)
                        elif field_type == float:
                            data[field] = float(value)
                        elif field_type == bool:
                            data[field] = bool(value)
                        elif field_type == str:
                            data[field] = str(value)
                    except (ValueError, TypeError):
                        raise ValidationError(
                            f"Field '{field}' must be of type {field_type.__name__}",
                            field=field
                        )
            
            # Store validated data for use in the function
            request.validated_data = data
            return func(*args, **kwargs)
            
        return wrapper
    return decorator


def rate_limit_handler(error):
    """Handle rate limit errors"""
    return ErrorResponse.create(
        error='rate_limit_exceeded',
        message='Too many requests. Please try again later.',
        status_code=429,
        details={
            'retry_after': error.description if hasattr(error, 'description') else 60
        }
    )


def handle_database_errors(func: Callable) -> Callable:
    """
    Decorator specifically for database operations
    Ensures proper rollback on errors
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            
            # Check for common database errors
            error_str = str(e).lower()
            
            if 'duplicate key' in error_str or 'unique constraint' in error_str:
                return ErrorResponse.create(
                    error='duplicate_entry',
                    message='A record with this information already exists',
                    status_code=409
                )
            elif 'foreign key' in error_str:
                return ErrorResponse.create(
                    error='invalid_reference',
                    message='Referenced record does not exist',
                    status_code=400
                )
            elif 'not null' in error_str:
                return ErrorResponse.create(
                    error='missing_required_field',
                    message='A required field is missing',
                    status_code=400
                )
            else:
                # Re-raise to be handled by general error handler
                raise
                
    return wrapper


def log_performance(func: Callable) -> Callable:
    """
    Decorator to log function performance
    Useful for identifying slow operations
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow operations
            if execution_time > 1.0:  # Log if takes more than 1 second
                logger.warning(
                    f"Slow operation: {func.__name__} took {execution_time:.2f}s"
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Error in {func.__name__} after {execution_time:.2f}s: {str(e)}"
            )
            raise
            
    return wrapper