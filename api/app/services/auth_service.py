"""
Authentication Service
Handles user authentication, JWT tokens, and related business logic
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, decode_token
from app.models.user import User

class AuthService:
    """Service class for authentication operations"""
    
    @staticmethod
    def register_user(username: str, email: str, password: str, 
                     role: str = 'user') -> Tuple[bool, Dict[str, Any]]:
        """
        Register a new user
        Returns (success: bool, result: dict)
        """
        try:
            # Check if user already exists
            if User.find_by_username(username):
                return False, {'error': 'Username already exists'}
            
            if User.find_by_email(email):
                return False, {'error': 'Email already exists'}
            
            # Create new user
            user = User(username=username, email=email, password=password, role=role)
            user_id = user.save()
            
            if user_id:
                return True, {
                    'message': 'User registered successfully',
                    'user': user.to_dict()
                }
            else:
                return False, {'error': 'Failed to create user'}
                
        except Exception as e:
            return False, {'error': f'Registration failed: {str(e)}'}
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Authenticate user credentials
        Returns (success: bool, result: dict)
        """
        try:
            # Find user by username or email
            user = User.find_by_username(username)
            if not user:
                user = User.find_by_email(username)
            
            if not user:
                return False, {'error': 'Invalid credentials'}
            
            if not user.is_active:
                return False, {'error': 'Account is disabled'}
            
            if not user.check_password(password):
                return False, {'error': 'Invalid credentials'}
            
            # Generate JWT token
            access_token = create_access_token(
                identity=str(user._id),
                additional_claims={
                    'username': user.username,
                    'role': user.role
                }
            )
            
            return True, {
                'message': 'Authentication successful',
                'access_token': access_token,
                'user': user.to_dict()
            }
            
        except Exception as e:
            return False, {'error': f'Authentication failed: {str(e)}'}
    
    @staticmethod
    def get_user_from_token(token: str) -> Optional[User]:
        """
        Get user object from JWT token
        Returns User object or None
        """
        try:
            token_data = decode_token(token)
            user_id = token_data['sub']
            return User.find_by_id(user_id)
        except Exception:
            return None
    
    @staticmethod
    def validate_registration_data(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate registration data
        Returns (is_valid: bool, errors: dict)
        """
        errors = {}
        
        # Required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                errors[field] = f'{field.title()} is required'
        
        # Username validation
        username = data.get('username', '')
        if username:
            if len(username) < 3:
                errors['username'] = 'Username must be at least 3 characters long'
            elif len(username) > 50:
                errors['username'] = 'Username must be less than 50 characters long'
        
        # Email validation (basic)
        email = data.get('email', '')
        if email:
            if '@' not in email or '.' not in email.split('@')[-1]:
                errors['email'] = 'Invalid email format'
        
        # Password validation
        password = data.get('password', '')
        if password:
            if len(password) < 6:
                errors['password'] = 'Password must be at least 6 characters long'
        
        return len(errors) == 0, errors
    
    @staticmethod
    def create_default_admin_user() -> bool:
        """
        Create default admin user if none exists
        Used for initial system setup
        """
        try:
            # Check if any admin user exists
            from app import mongo
            admin_exists = mongo.db.users.find_one({'role': 'admin'})
            
            if not admin_exists:
                # Create default admin
                admin_user = User(
                    username='admin',
                    email='admin@laboratoriocelular.net',
                    password='admin123',  # Should be changed on first login
                    role='admin'
                )
                user_id = admin_user.save()
                return user_id is not None
                
            return True  # Admin already exists
            
        except Exception as e:
            print(f"Error creating default admin user: {e}")
            return False