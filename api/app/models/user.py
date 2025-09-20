"""
User Model for Authentication System
Uses MongoDB with PyMongo for data storage
"""
from datetime import datetime
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from flask_pymongo import PyMongo
from flask import current_app

# We'll import mongo from the main app
def get_mongo():
    """Get the MongoDB instance from current Flask app"""
    from app import mongo
    return mongo

class User:
    """User model for authentication and user management"""
    
    def __init__(self, username: str, email: str, password: str = None, 
                 role: str = 'user', _id: ObjectId = None, **kwargs):
        self._id = _id
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password) if password else None
        self.role = role
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.is_active = kwargs.get('is_active', True)
        
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user object to dictionary"""
        user_dict = {
            'id': str(self._id) if self._id else None,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active
        }
        
        if include_sensitive:
            user_dict['password_hash'] = self.password_hash
            
        return user_dict
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches user's password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password: str):
        """Set new password for user"""
        self.password_hash = generate_password_hash(password)
        self.updated_at = datetime.utcnow()
    
    def save(self) -> Optional[ObjectId]:
        """Save user to MongoDB"""
        mongo = get_mongo()
        user_data = self.to_dict(include_sensitive=True)
        user_data['updated_at'] = datetime.utcnow()
        
        if self._id:
            # Update existing user
            result = mongo.db.users.update_one(
                {'_id': ObjectId(self._id)},
                {'$set': user_data}
            )
            return self._id if result.modified_count > 0 else None
        else:
            # Create new user
            user_data.pop('id', None)  # Remove the string id
            result = mongo.db.users.insert_one(user_data)
            self._id = result.inserted_id
            return self._id
    
    @classmethod
    def find_by_id(cls, user_id: str) -> Optional['User']:
        """Find user by ID"""
        try:
            mongo = get_mongo()
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return cls._from_dict(user_data)
            return None
        except Exception:
            return None
    
    @classmethod  
    def find_by_username(cls, username: str) -> Optional['User']:
        """Find user by username"""
        mongo = get_mongo()
        user_data = mongo.db.users.find_one({'username': username})
        if user_data:
            return cls._from_dict(user_data)
        return None
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find user by email"""
        mongo = get_mongo()
        user_data = mongo.db.users.find_one({'email': email})
        if user_data:
            return cls._from_dict(user_data)
        return None
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User instance from dictionary"""
        user = cls.__new__(cls)
        user._id = data.get('_id')
        user.username = data.get('username')
        user.email = data.get('email')
        user.password_hash = data.get('password_hash')
        user.role = data.get('role', 'user')
        user.created_at = data.get('created_at')
        user.updated_at = data.get('updated_at')
        user.is_active = data.get('is_active', True)
        return user
    
    @classmethod
    def create_indexes(cls):
        """Create database indexes for optimal performance"""
        mongo = get_mongo()
        
        # Create unique indexes
        mongo.db.users.create_index('username', unique=True)
        mongo.db.users.create_index('email', unique=True)
        
        # Create regular indexes
        mongo.db.users.create_index('role')
        mongo.db.users.create_index('is_active')
        mongo.db.users.create_index('created_at')
    
    def __repr__(self):
        return f'<User {self.username}>'