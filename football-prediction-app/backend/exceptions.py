"""
Custom exception classes for the Football Prediction API
"""

class FootballAPIError(Exception):
    """Base exception for all football API errors"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

class ValidationError(FootballAPIError):
    """Exception for input validation errors"""
    def __init__(self, message, field=None):
        super().__init__(message, status_code=400)
        self.field = field

class APIKeyError(FootballAPIError):
    """Exception for API key related errors"""
    def __init__(self, message="API key not configured or invalid"):
        super().__init__(message, status_code=401)

class ModelNotTrainedError(FootballAPIError):
    """Exception when ML model is not trained"""
    def __init__(self, message="Machine learning model is not trained"):
        super().__init__(message, status_code=503)

class DataNotFoundError(FootballAPIError):
    """Exception when requested data is not found"""
    def __init__(self, message, resource=None):
        super().__init__(message, status_code=404)
        self.resource = resource

class ExternalAPIError(FootballAPIError):
    """Exception for external API failures"""
    def __init__(self, message="External API service unavailable", service=None):
        super().__init__(message, status_code=502)
        self.service = service