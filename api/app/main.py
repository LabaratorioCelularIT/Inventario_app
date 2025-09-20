from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import get_config

def create_app():
    app = Flask(__name__)
    config_instance = get_config('development')
    app.config.from_object(config_instance)
    
    # Initialize extensions
    CORS(app)
    jwt = JWTManager(app)
    
    # Simple root route
    @app.route('/')
    def root():
        return jsonify({
            'message': 'Inventario API is running',
            'version': '2.0',
            'status': 'active',
            'endpoints': {
                'health': '/health',
                'auth': '/api/v1/auth/',
                'inventory': '/api/v1/inventory/',
                'cash': '/api/v1/cash/'
            }
        })
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'API is running successfully',
            'timestamp': '2025-09-20',
            'services': {
                'api': 'running',
                'database': 'not connected (testing mode)'
            }
        })
    
    # Register blueprints
    from app.api.v1 import auth_bp, inventory_bp, cash_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1')
    app.register_blueprint(inventory_bp, url_prefix='/api/v1')
    app.register_blueprint(cash_bp, url_prefix='/api/v1')
    
    return app

# For development server
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)