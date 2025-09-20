"""
Database Management Utilities
Handles database initialization, indexes, and maintenance tasks
"""
from flask import current_app
from app.models.user import User
from app.services.auth_service import AuthService

class DatabaseManager:
    """Utilities for database management and initialization"""
    
    @staticmethod
    def initialize_database():
        """Initialize database with indexes and default data"""
        try:
            current_app.logger.info("Initializing database...")
            
            # Create indexes
            DatabaseManager.create_indexes()
            
            # Create default admin user
            DatabaseManager.create_default_users()
            
            current_app.logger.info("Database initialization completed successfully")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Database initialization failed: {e}")
            return False
    
    @staticmethod
    def create_indexes():
        """Create database indexes for optimal performance"""
        try:
            current_app.logger.info("Creating database indexes...")
            
            # Create User indexes
            User.create_indexes()
            
            current_app.logger.info("Database indexes created successfully")
            
        except Exception as e:
            current_app.logger.error(f"Failed to create indexes: {e}")
            raise
    
    @staticmethod
    def create_default_users():
        """Create default users for system initialization"""
        try:
            current_app.logger.info("Creating default users...")
            
            # Create default admin user
            if AuthService.create_default_admin_user():
                current_app.logger.info("Default admin user created/verified")
            else:
                current_app.logger.warning("Failed to create default admin user")
            
        except Exception as e:
            current_app.logger.error(f"Failed to create default users: {e}")
            raise
    
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            from app import mongo
            
            # Try to get database stats
            db_stats = mongo.db.command('dbstats')
            current_app.logger.info(f"Database connection successful. DB: {db_stats.get('db')}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Database connection failed: {e}")
            return False