from flask import Flask
from flask_cors import CORS
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app)
    
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