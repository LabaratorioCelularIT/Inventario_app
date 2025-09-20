"""
Authentication Routes
Handles user registration, login, and logout
"""
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.auth_service import AuthService
from . import auth_bp

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate registration data
        is_valid, errors = AuthService.validate_registration_data(data)
        if not is_valid:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        # Register user
        success, result = AuthService.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'user')
        )
        
        if success:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User authentication endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Authenticate user
        success, result = AuthService.authenticate_user(username, password)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    try:
        # In a more complex implementation, you might want to blacklist the token
        # For now, we'll just return a success message
        # The client should remove the token from storage
        
        return jsonify({
            'message': 'Logged out successfully',
            'note': 'Please remove the access token from your client storage'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        user_id = get_jwt_identity()
        from app.models.user import User
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_token():
    """Verify if token is valid"""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        return jsonify({
            'valid': True,
            'user_id': user_id,
            'username': claims.get('username'),
            'role': claims.get('role')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token verification error: {e}")
        return jsonify({'error': 'Invalid token'}), 401