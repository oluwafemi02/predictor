"""
Authentication routes for the Football Prediction API
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from auth import AuthService, User, require_auth, require_admin
from exceptions import ValidationError
from validators import sanitize_text_input
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("No data provided")
        
        # Sanitize inputs
        username = sanitize_text_input(data.get('username'), max_length=80)
        email = sanitize_text_input(data.get('email'), max_length=120)
        password = data.get('password')  # Don't sanitize password
        
        # Register user
        user = AuthService.register_user(username, email, password)
        
        # Create tokens
        tokens = AuthService.create_tokens(user)
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'tokens': tokens
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': e.message,
            'field': e.field
        }), 400
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Registration failed'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with username/password"""
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("No data provided")
        
        username = sanitize_text_input(data.get('username'), max_length=80)
        password = data.get('password')
        
        if not username or not password:
            raise ValidationError("Username and password required")
        
        # Authenticate user
        user = AuthService.authenticate_user(username, password)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'Invalid username or password'
            }), 401
        
        # Create tokens
        tokens = AuthService.create_tokens(user)
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'user': user.to_dict(),
            'tokens': tokens
        })
        
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': e.message
        }), 400
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Login failed'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user or not user.is_active:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user'
            }), 401
        
        # Create new tokens
        tokens = AuthService.create_tokens(user)
        
        return jsonify({
            'status': 'success',
            'tokens': tokens
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Token refresh failed'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information"""
    try:
        user = AuthService.get_current_user()
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get user information'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user (revoke token)"""
    try:
        # Get token JTI to add to blocklist
        jti = get_jwt()["jti"]
        
        # TODO: Add token to Redis blocklist
        # redis_client.setex(f"blocklist:{jti}", 3600, "revoked")
        
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Logout failed'
        }), 500


@auth_bp.route('/api-key', methods=['POST'])
@require_auth
def generate_api_key():
    """Generate new API key for current user"""
    try:
        user = AuthService.get_current_user()
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        # Generate new API key
        api_key = user.generate_api_key()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'API key generated successfully',
            'api_key': api_key
        })
        
    except Exception as e:
        logger.error(f"API key generation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate API key'
        }), 500


@auth_bp.route('/users', methods=['GET'])
@require_admin
def list_users():
    """List all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Limit per_page
        per_page = min(per_page, 100)
        
        # Query users
        users = User.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'status': 'success',
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': users.page,
                'per_page': users.per_page,
                'total': users.total,
                'pages': users.pages
            }
        })
        
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to list users'
        }), 500