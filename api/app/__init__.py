# Flask Application Factory
from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import get_config

# Initialize extensions
mongo = PyMongo()
jwt = JWTManager()
cors = CORS()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_instance = get_config(config_name)
    app.config.from_object(config_instance)
    
    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request', 'message': str(error)}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden', 'message': 'Insufficient permissions'}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error', 'message': 'An unexpected error occurred'}, 500

def register_blueprints(app):
    """Register application blueprints"""
    from app.api.v1 import auth_bp, inventory_bp, sales_bp, reports_bp, users_bp
    
    # API v1 routes
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(inventory_bp, url_prefix='/api/v1/inventory')
    app.register_blueprint(sales_bp, url_prefix='/api/v1/sales')
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'version': '1.0.0',
            'database': 'connected' if mongo.db else 'disconnected'
        }