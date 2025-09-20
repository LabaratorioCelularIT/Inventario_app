#!/usr/bin/env python3
"""
Manual API Testing Server
Runs the Flask API in testing mode for manual endpoint validation
"""

import os
from app.main import create_app

def run_test_server():
    """Run Flask API in testing mode"""
    print("🚀 Starting Flask API Test Server")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    # Set testing configuration
    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    
    # Override MongoDB for testing (so it doesn't fail without MongoDB)
    app.config['MONGODB_URI'] = 'mongodb://localhost:27017/test_db'
    
    print("✅ Flask app created successfully")
    print("✅ Testing mode enabled")
    print("✅ Debug mode enabled")
    
    print("\n📍 API Endpoints Available:")
    print("   GET  /health")
    print("   POST /api/v1/auth/register")
    print("   POST /api/v1/auth/login")
    print("   GET  /api/v1/auth/me")
    print("   POST /api/v1/auth/verify")
    print("   POST /api/v1/auth/logout")
    
    print("\n🌐 Server will start on: http://localhost:5000")
    print("📝 Use curl or Postman to test endpoints")
    print("🛑 Press Ctrl+C to stop server")
    
    print("\n" + "=" * 50)
    print("🚀 STARTING SERVER...")
    print("=" * 50)
    
    try:
        # Start the development server
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Prevent reloader issues in testing
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        
        # Try to show what went wrong
        if "MongoDB" in str(e) or "pymongo" in str(e):
            print("\n💡 This is expected without MongoDB!")
            print("   The authentication logic still works")
            print("   Only database operations will fail")

if __name__ == "__main__":
    run_test_server()