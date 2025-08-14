"""
Authentication module for Football Prediction API
Implements JWT-based authentication with secure password hashing
"""

import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any

from flask import request, jsonify, current_app
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    get_jwt_identity, verify_jwt_in_request, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.exc import IntegrityError

from models import db
from exceptions import ValidationError, APIKeyError
import logging

logger = logging.getLogger(__name__)


class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(64), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password: str):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify the user's password"""
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self) -> str:
        """Generate a unique API key for the user"""
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


def init_jwt(app):
    """Initialize JWT manager with the Flask app"""
    app.config['JWT_SECRET_KEY'] = app.config.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    jwt = JWTManager(app)
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        # Check if token is in revoked list (implement Redis-based blocklist)
        jti = jwt_payload["jti"]
        # TODO: Check Redis for revoked tokens
        return False
    
    return jwt


def require_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required',
                'type': 'auth_error'
            }), 401
    return decorated_function


def require_admin(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims.get('is_admin', False):
                return jsonify({
                    'status': 'error',
                    'message': 'Admin privileges required',
                    'type': 'permission_error'
                }), 403
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required',
                'type': 'auth_error'
            }), 401
    return decorated_function


def optional_auth(f):
    """Decorator for optional authentication (different behavior for authenticated users)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
        except:
            pass
        return f(*args, **kwargs)
    return decorated_function


def validate_api_key_auth(f):
    """Decorator to validate API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'API key required',
                'type': 'auth_error'
            }), 401
        
        user = User.query.filter_by(api_key=api_key, is_active=True).first()
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'Invalid API key',
                'type': 'auth_error'
            }), 403
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function


class AuthService:
    """Service class for authentication operations"""
    
    @staticmethod
    def register_user(username: str, email: str, password: str) -> User:
        """Register a new user"""
        # Validate inputs
        if not username or len(username) < 3:
            raise ValidationError("Username must be at least 3 characters", field="username")
        
        if not email or '@' not in email:
            raise ValidationError("Invalid email address", field="email")
        
        if not password or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters", field="password")
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            raise ValidationError("Username already exists", field="username")
        
        if User.query.filter_by(email=email).first():
            raise ValidationError("Email already registered", field="email")
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        user.generate_api_key()
        
        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user registered: {username}")
            return user
        except IntegrityError:
            db.session.rollback()
            raise ValidationError("Failed to create user")
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password"""
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if not user or not user.check_password(password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def create_tokens(user: User) -> Dict[str, str]:
        """Create access and refresh tokens for user"""
        # Add custom claims
        additional_claims = {
            'username': user.username,
            'is_admin': user.is_admin
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get current authenticated user"""
        try:
            user_id = get_jwt_identity()
            if user_id:
                return User.query.get(int(user_id))
        except:
            pass
        return None