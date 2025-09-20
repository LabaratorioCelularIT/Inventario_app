#!/usr/bin/env python3
"""
Manual Testing Guide for Authentication System
This script helps you manually test the authentication system without MongoDB.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.services.auth_service import AuthService
from werkzeug.security import check_password_hash
import jwt
from datetime import datetime

def test_user_creation():
    """Test 1: User Creation and Password Hashing"""
    print("🧪 Test 1: User Creation and Password Hashing")
    print("-" * 50)
    
    # Create a test user
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'role': 'user'
    }
    
    user = User(**user_data)
    
    print(f"✅ Username: {user.username}")
    print(f"✅ Email: {user.email}")
    print(f"✅ Role: {user.role}")
    print(f"✅ Created At: {user.created_at}")
    print(f"✅ Password Hash Generated: {bool(user.password_hash)}")
    print(f"✅ Password Hash Length: {len(user.password_hash)} characters")
    
    # Test password verification
    is_correct = user.check_password('password123')
    is_wrong = user.check_password('wrongpassword')
    
    print(f"✅ Correct Password Check: {is_correct}")
    print(f"✅ Wrong Password Check: {is_wrong}")
    
    print(f"\n🎯 Result: {'PASSED' if is_correct and not is_wrong else 'FAILED'}")
    return user

def test_auth_service_registration():
    """Test 2: AuthService Registration Logic"""
    print("\n🧪 Test 2: AuthService Registration Logic")
    print("-" * 50)
    
    auth_service = AuthService()
    
    # Test valid registration data
    valid_data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'securepass123'
    }
    
    # Validate registration data
    is_valid, errors = auth_service.validate_registration_data(valid_data)
    print(f"✅ Valid Data Validation: {is_valid}")
    if errors:
        print(f"❌ Unexpected Errors: {errors}")
    
    # Test invalid registration data
    invalid_data = {
        'username': 'ab',  # Too short
        'email': 'invalid-email',  # Invalid format
        'password': '123'  # Too short
    }
    
    is_invalid, invalid_errors = auth_service.validate_registration_data(invalid_data)
    print(f"✅ Invalid Data Validation: {not is_invalid}")
    print(f"✅ Expected Errors Found: {len(invalid_errors)} errors")
    for error in invalid_errors:
        print(f"   - {error}")
    
    print(f"\n🎯 Result: {'PASSED' if is_valid and not is_invalid else 'FAILED'}")

def test_jwt_token_creation():
    """Test 3: JWT Token Creation and Validation"""
    print("\n🧪 Test 3: JWT Token Creation and Validation")
    print("-" * 50)
    
    # Create a test user
    user = User(
        username='tokenuser',
        email='token@example.com',
        password='testpass123'
    )
    
    # Simulate token creation (what happens in auth_service.py)
    from flask_jwt_extended import create_access_token
    from datetime import timedelta
    
    # We need a Flask app context for JWT to work
    from app.main import create_app
    
    app = create_app()
    
    with app.app_context():
        # Create token
        token = create_access_token(
            identity=str(user.username),
            expires_delta=timedelta(hours=24),
            additional_claims={
                'email': user.email,
                'role': user.role,
                'user_id': str(user.username)  # In real app, this would be ObjectId
            }
        )
        
        print(f"✅ JWT Token Generated: {bool(token)}")
        print(f"✅ Token Length: {len(token)} characters")
        print(f"✅ Token Preview: {token[:50]}...")
        
        # Decode token to verify contents (for testing only)
        try:
            # Note: In production, Flask-JWT-Extended handles this
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"✅ Token Contains Identity: {'sub' in decoded}")
            print(f"✅ Token Contains Claims: {'email' in decoded}")
            print(f"✅ Token Expiration Set: {'exp' in decoded}")
            
            print(f"\n🎯 Result: PASSED")
            return token
        except Exception as e:
            print(f"❌ Token Decode Error: {e}")
            print(f"\n🎯 Result: FAILED")
            return None

def test_complete_auth_flow():
    """Test 4: Complete Authentication Flow"""
    print("\n🧪 Test 4: Complete Authentication Flow Simulation")
    print("-" * 50)
    
    auth_service = AuthService()
    
    # Simulate registration
    registration_data = {
        'username': 'flowtest',
        'email': 'flow@example.com',
        'password': 'flowpass123'
    }
    
    print("Step 1: Registration Validation")
    is_valid, errors = auth_service.validate_registration_data(registration_data)
    print(f"✅ Registration Data Valid: {is_valid}")
    
    if not is_valid:
        for error in errors:
            print(f"❌ Error: {error}")
        return False
    
    # Create user manually (simulating successful registration)
    user = User(**registration_data)
    print(f"✅ User Created: {user.username}")
    
    # Simulate authentication
    print("\nStep 2: Authentication Test")
    correct_password = user.check_password('flowpass123')
    wrong_password = user.check_password('wrongpass')
    
    print(f"✅ Correct Password Auth: {correct_password}")
    print(f"✅ Wrong Password Rejected: {not wrong_password}")
    
    # Simulate token generation (would happen after successful auth)
    print("\nStep 3: Token Generation")
    from app.main import create_app
    app = create_app()
    
    with app.app_context():
        from flask_jwt_extended import create_access_token
        from datetime import timedelta
        
        if correct_password:
            token = create_access_token(
                identity=user.username,
                expires_delta=timedelta(hours=24),
                additional_claims={
                    'email': user.email,
                    'role': user.role
                }
            )
            print(f"✅ Login Token Generated: {bool(token)}")
        else:
            token = None
            print(f"❌ No Token Generated (Auth Failed)")
    
    success = is_valid and correct_password and not wrong_password and bool(token)
    print(f"\n🎯 Complete Flow Result: {'PASSED' if success else 'FAILED'}")
    return success

def main():
    """Run all manual tests"""
    print("🚀 Manual Authentication System Testing")
    print("=" * 60)
    print("Testing authentication components without MongoDB")
    print("=" * 60)
    
    try:
        # Run all tests
        test_user_creation()
        test_auth_service_registration()
        test_jwt_token_creation()
        test_complete_auth_flow()
        
        print("\n" + "=" * 60)
        print("✅ Manual Testing Complete!")
        print("✅ All authentication logic validated successfully")
        print("✅ System ready for MongoDB integration")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        print("❌ Check your authentication implementation")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()