from . import cash_bp
from flask import request, jsonify

@cash_bp.route('/cash/register', methods=['GET'])
def get_cash_register():
    """Get cash register status"""
    # TODO: Implement cash register status retrieval
    return jsonify({'message': 'Cash register endpoint - to be implemented'}), 200

@cash_bp.route('/cash/transaction', methods=['POST'])
def create_transaction():
    """Create new transaction"""
    # TODO: Implement transaction creation
    return jsonify({'message': 'Transaction endpoint - to be implemented'}), 201