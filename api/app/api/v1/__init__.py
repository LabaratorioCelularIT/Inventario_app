from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__)
inventory_bp = Blueprint('inventory', __name__)
cash_bp = Blueprint('cash', __name__)

# For compatibility with main app registration
sales_bp = cash_bp  # Alias cash_bp as sales_bp
reports_bp = Blueprint('reports', __name__)  # Create reports blueprint
users_bp = Blueprint('users', __name__)  # Create users blueprint

# Import routes after blueprint creation to avoid circular imports
from . import auth_routes, inventory_routes, cash_routes