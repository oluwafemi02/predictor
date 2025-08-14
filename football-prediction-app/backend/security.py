import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TokenManager:
    """
    Secure token management with encryption
    """
    
    def __init__(self):
        # Get or generate encryption key
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or create one"""
        # Try to get from environment
        key_str = os.environ.get('TOKEN_ENCRYPTION_KEY')
        
        if key_str:
            try:
                # Decode from base64
                return base64.urlsafe_b64decode(key_str)
            except Exception as e:
                logger.error(f"Invalid encryption key in environment: {str(e)}")
        
        # Generate new key from password
        password = os.environ.get('TOKEN_ENCRYPTION_PASSWORD')
        salt = os.environ.get('TOKEN_ENCRYPTION_SALT')
        
        if not password or not salt:
            # Only allow defaults in development
            if os.environ.get('FLASK_ENV') == 'production':
                raise ValueError("TOKEN_ENCRYPTION_PASSWORD and TOKEN_ENCRYPTION_SALT must be set in production!")
            else:
                logger.warning("Using default encryption settings - NOT SAFE FOR PRODUCTION!")
                password = 'dev-only-password'
                salt = 'dev-only-salt'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        return key
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt an API token"""
        try:
            encrypted = self.cipher.encrypt(token.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt token: {str(e)}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt an API token"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_token)
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {str(e)}")
            raise
    
    def mask_token(self, token: str) -> str:
        """Mask a token for logging/display (show first 4 and last 4 chars)"""
        if len(token) <= 10:
            return "*" * len(token)
        return f"{token[:4]}...{token[-4:]}"
    
    def validate_token_format(self, token: str) -> bool:
        """Validate token format"""
        # SportMonks tokens are typically 60-64 characters
        if not token or not isinstance(token, str):
            return False
        
        # Check length
        if len(token) < 20 or len(token) > 100:
            return False
        
        # Check for valid characters (alphanumeric)
        if not token.isalnum():
            return False
        
        return True
    
    def generate_api_key(self) -> str:
        """Generate a secure API key for internal use"""
        return secrets.token_urlsafe(32)

# Security headers middleware
def add_security_headers(response):
    """Add security headers to responses"""
    # Prevent XSS attacks
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    
    # Strict Transport Security (for HTTPS)
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# Rate limiting decorator
from functools import wraps
from flask import request, jsonify
import time

class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def cleanup(self):
        """Remove old entries"""
        if time.time() - self.last_cleanup > self.cleanup_interval:
            current_time = time.time()
            self.requests = {
                key: times for key, times in self.requests.items()
                if any(t > current_time - 3600 for t in times)  # Keep last hour
            }
            self.last_cleanup = current_time
    
    def is_allowed(self, identifier: str, max_requests: int = 60, window: int = 60) -> bool:
        """Check if request is allowed"""
        self.cleanup()
        
        current_time = time.time()
        window_start = current_time - window
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Filter requests within window
        self.requests[identifier] = [
            t for t in self.requests[identifier] if t > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True

rate_limiter = RateLimiter()

def rate_limit(max_requests=60, window=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as identifier
            identifier = request.remote_addr
            
            if not rate_limiter.is_allowed(identifier, max_requests, window):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {window} seconds'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# API key validation
def validate_api_key(api_key: str) -> bool:
    """Validate internal API key"""
    # For now, check against environment variable
    valid_keys = os.environ.get('INTERNAL_API_KEYS', '').split(',')
    return api_key in valid_keys

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide X-API-Key header'
            }), 401
        
        if not validate_api_key(api_key):
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function