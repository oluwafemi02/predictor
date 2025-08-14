"""
Logging configuration for the Football Prediction App
Provides structured logging with different handlers for development and production
"""

import os
import logging
import logging.handlers
from datetime import datetime
import json
from typing import Dict, Any


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 
                          'funcName', 'levelname', 'levelno', 'lineno', 
                          'module', 'msecs', 'pathname', 'process', 
                          'processName', 'relativeCreated', 'thread', 
                          'threadName', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Add color to log levels"""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


def setup_logging(app_name: str = 'football_prediction') -> None:
    """
    Set up logging configuration based on environment
    
    Args:
        app_name: Name of the application for log identification
    """
    # Get configuration from environment
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_file = os.environ.get('LOG_FILE', 'backend.log')
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler - always present
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    if flask_env == 'production':
        # Production: structured JSON logs
        console_formatter = StructuredFormatter()
    else:
        # Development: colored human-readable logs
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler - rotating logs
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # Always use structured format for file logs
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Production-specific handlers
    if flask_env == 'production':
        # Sentry integration if available
        sentry_dsn = os.environ.get('SENTRY_DSN')
        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.logging import LoggingIntegration
                
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR   # Send errors as events
                )
                
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[sentry_logging],
                    environment=flask_env,
                    traces_sample_rate=0.1,
                )
                
                logger.info("Sentry integration initialized")
            except ImportError:
                logger.warning("Sentry SDK not installed, skipping Sentry integration")
    
    # Log configuration
    logger.info(f"Logging configured - Level: {log_level}, Environment: {flask_env}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_request(request_data: Dict[str, Any]) -> None:
    """
    Log HTTP request details
    
    Args:
        request_data: Dictionary containing request information
    """
    logger = get_logger('request')
    logger.info(
        "HTTP Request",
        extra={
            'method': request_data.get('method'),
            'path': request_data.get('path'),
            'ip': request_data.get('ip'),
            'user_agent': request_data.get('user_agent'),
            'request_id': request_data.get('request_id'),
        }
    )


def log_response(response_data: Dict[str, Any]) -> None:
    """
    Log HTTP response details
    
    Args:
        response_data: Dictionary containing response information
    """
    logger = get_logger('response')
    logger.info(
        "HTTP Response",
        extra={
            'status_code': response_data.get('status_code'),
            'duration_ms': response_data.get('duration_ms'),
            'request_id': response_data.get('request_id'),
        }
    )


def log_database_query(query_data: Dict[str, Any]) -> None:
    """
    Log database query details
    
    Args:
        query_data: Dictionary containing query information
    """
    logger = get_logger('database')
    logger.debug(
        "Database Query",
        extra={
            'query': query_data.get('query'),
            'duration_ms': query_data.get('duration_ms'),
            'rows_affected': query_data.get('rows_affected'),
        }
    )


def log_api_call(api_data: Dict[str, Any]) -> None:
    """
    Log external API call details
    
    Args:
        api_data: Dictionary containing API call information
    """
    logger = get_logger('api_client')
    logger.info(
        "External API Call",
        extra={
            'service': api_data.get('service'),
            'endpoint': api_data.get('endpoint'),
            'method': api_data.get('method'),
            'status_code': api_data.get('status_code'),
            'duration_ms': api_data.get('duration_ms'),
        }
    )


def log_prediction(prediction_data: Dict[str, Any]) -> None:
    """
    Log ML prediction details
    
    Args:
        prediction_data: Dictionary containing prediction information
    """
    logger = get_logger('prediction')
    logger.info(
        "Match Prediction Generated",
        extra={
            'match_id': prediction_data.get('match_id'),
            'model_version': prediction_data.get('model_version'),
            'confidence': prediction_data.get('confidence'),
            'processing_time_ms': prediction_data.get('processing_time_ms'),
        }
    )


# Initialize logging when module is imported
setup_logging()