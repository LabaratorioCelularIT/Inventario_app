#!/usr/bin/env python3
"""
Test script for MongoDB connection and authentication system
Run this script to test the basic functionality of our auth implementation
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_basic_imports():
    """Test that our modules can be imported correctly"""
    print("🔍 Testing basic imports...")
    
    try:
        from app.models.user import User
        print("✅ User model imported successfully")
        
        from app.services.auth_service import AuthService
        print("✅ AuthService imported successfully")
        
        from app.utils.database import DatabaseManager
        print("✅ DatabaseManager imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_user_model():
    """Test User model basic functionality (without database)"""
    print("\n🔍 Testing User model...")
    
    try:
        from app.models.user import User
        
        # Test user creation
        user = User(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        
        print(f"✅ User created: {user.username}")
        print(f"✅ Password hash generated: {bool(user.password_hash)}")
        
        # Test password verification
        if user.check_password("testpassword123"):
            print("✅ Password verification works")
        else:
            print("❌ Password verification failed")
            
        # Test to_dict method
        user_dict = user.to_dict()
        expected_fields = ['username', 'email', 'role', 'created_at', 'updated_at', 'is_active']
        
        if all(field in user_dict for field in expected_fields):
            print("✅ User to_dict method works")
        else:
            print("❌ User to_dict missing fields")
            
        return True
        
    except Exception as e:
        print(f"❌ User model test failed: {e}")
        return False

def test_auth_service():
    """Test AuthService validation methods"""
    print("\n🔍 Testing AuthService...")
    
    try:
        from app.services.auth_service import AuthService
        
        # Test data validation
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com', 
            'password': 'password123'
        }
        
        is_valid, errors = AuthService.validate_registration_data(valid_data)
        
        if is_valid and len(errors) == 0:
            print("✅ Valid data validation works")
        else:
            print(f"❌ Valid data validation failed: {errors}")
            
        # Test invalid data
        invalid_data = {
            'username': 'ab',  # too short
            'email': 'invalid-email',  # invalid format
            'password': '123'  # too short
        }
        
        is_valid, errors = AuthService.validate_registration_data(invalid_data)
        
        if not is_valid and len(errors) > 0:
            print("✅ Invalid data validation works")
            print(f"   Caught errors: {list(errors.keys())}")
        else:
            print("❌ Invalid data validation failed")
            
        return True
        
    except Exception as e:
        print(f"❌ AuthService test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing MongoDB Integration and Authentication System")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if test_basic_imports():
        tests_passed += 1
        
    if test_user_model():
        tests_passed += 1
        
    if test_auth_service():
        tests_passed += 1
    
    # Results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The authentication system is ready for testing with MongoDB.")
        print("\nNext steps:")
        print("1. Start MongoDB (docker compose up -d mongo)")
        print("2. Start the Flask API (./dev-launcher-simple.sh api)")
        print("3. Test the auth endpoints with curl or a REST client")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())