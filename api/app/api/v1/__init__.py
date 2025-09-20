from flask import Blueprint

# Create blueprints
auth_bp = Blueprint('auth', __name__)
inventory_bp = Blueprint('inventory', __name__)
cash_bp = Blueprint('cash', __name__)

# Import routes after blueprint creation to avoid circular imports
from . import auth_routes, inventory_routes, cash_routes