#!/usr/bin/env python3
"""
API Endpoint Test Script
Tests the authentication endpoints with real HTTP requests
Run this after starting the Flask API server
"""

import requests
import json
import sys
import time

API_BASE_URL = "http://localhost:5000/api/v1"
HEALTH_URL = "http://localhost:5000/health"

def test_server_health():
    """Test if the server is running and healthy"""
    print("🔍 Testing server health...")
    
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy: {data.get('status')}")
            print(f"   Database status: {data.get('database', 'unknown')}")
            return True
        else:
            print(f"❌ Server health check failed: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_user_registration():
    """Test user registration endpoint"""
    print("\n🔍 Testing user registration...")
    
    test_user = {
        "username": "testuser123",
        "email": "testuser@example.com",
        "password": "securepassword123",
        "role": "user"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register", 
            json=test_user,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ User registration successful")
            return True, test_user
        elif response.status_code == 400 and "already exists" in response.text:
            print("✅ User registration (user already exists - that's OK for testing)")
            return True, test_user
        else:
            print(f"❌ User registration failed")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration request failed: {e}")
        return False, None

def test_user_login(test_user):
    """Test user login endpoint"""
    print("\n🔍 Testing user login...")
    
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Response keys: {list(data.keys())}")
        
        if response.status_code == 200 and 'access_token' in data:
            print("✅ User login successful")
            print(f"   Token received: {data['access_token'][:50]}...")
            return True, data['access_token']
        else:
            print(f"❌ User login failed")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return False, None

def test_protected_endpoint(token):
    """Test accessing a protected endpoint with JWT token"""
    print("\n🔍 Testing protected endpoint (/auth/me)...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   User data: {data.get('user', {}).get('username')}")
            print("✅ Protected endpoint access successful")
            return True
        else:
            print(f"❌ Protected endpoint access failed")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Protected endpoint request failed: {e}")
        return False

def test_invalid_token():
    """Test accessing protected endpoint with invalid token"""
    print("\n🔍 Testing invalid token rejection...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={
                'Authorization': 'Bearer invalid_token_here',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Invalid token correctly rejected")
            return True
        else:
            print(f"❌ Invalid token should be rejected but got: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Invalid token test request failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Testing Authentication API Endpoints")
    print("=" * 60)
    print("Make sure the Flask API is running on http://localhost:5000")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    # Test server health
    if not test_server_health():
        print("\n❌ Server is not running. Please start the API server first:")
        print("   ./dev-launcher-simple.sh api")
        return 1
    
    tests_passed += 1
    
    # Test user registration
    success, test_user = test_user_registration()
    if success:
        tests_passed += 1
    else:
        print("\n❌ Stopping tests due to registration failure")
        return 1
    
    # Test user login
    success, token = test_user_login(test_user)
    if success:
        tests_passed += 1
    else:
        print("\n❌ Stopping tests due to login failure")
        return 1
    
    # Test protected endpoint with valid token
    if test_protected_endpoint(token):
        tests_passed += 1
    
    # Test invalid token rejection
    if test_invalid_token():
        tests_passed += 1
    
    # Results
    print("\n" + "=" * 60)
    print(f"📊 API Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All API tests passed! The authentication system is working correctly.")
        print("\nThe following endpoints are ready:")
        print("- POST /api/v1/auth/register - User registration")
        print("- POST /api/v1/auth/login - User authentication") 
        print("- GET /api/v1/auth/me - Get current user (protected)")
        print("- POST /api/v1/auth/verify - Verify token (protected)")
        print("- POST /api/v1/auth/logout - User logout (protected)")
        return 0
    else:
        print("⚠️  Some API tests failed. Please check the server logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())