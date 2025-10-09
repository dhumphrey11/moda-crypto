#!/usr/bin/env python3
"""
Debug script to check backend startup requirements
"""
import os
import sys
from pydantic import ValidationError

def main():
    print("=== Backend Startup Debug ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print()
    
    # Check critical imports first
    print("=== Import Tests ===")
    try:
        import fastapi
        print(f"✓ FastAPI {fastapi.__version__} imported successfully")
    except Exception as e:
        print(f"✗ FastAPI import failed: {e}")
        return 1
        
    try:
        import uvicorn
        print(f"✓ Uvicorn imported successfully")
    except Exception as e:
        print(f"✗ Uvicorn import failed: {e}")
        return 1
        
    try:
        import firebase_admin
        print(f"✓ Firebase Admin SDK imported successfully")
    except Exception as e:
        print(f"✗ Firebase Admin SDK import failed: {e}")
        return 1
    
    # Check environment variables
    print("\n=== Environment Variables ===")
    required_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_CLIENT_EMAIL', 
        'FIREBASE_PRIVATE_KEY',
        'FIREBASE_STORAGE_BUCKET',
        'PORT'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if 'PRIVATE_KEY' in var:
                # Check if it looks like a valid private key
                if value.strip().startswith('-----BEGIN'):
                    print(f"✓ {var}: [Valid format - length: {len(value)}]")
                else:
                    print(f"⚠ {var}: [SET but may need formatting - length: {len(value)}]")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: [NOT SET]")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {missing_vars}")
        return False
    
    
    # Try to load settings
    print("=== Loading Settings ===")
    try:
        from app.config import settings
        print("✅ Settings loaded successfully")
        print(f"Environment: {settings.environment}")
        print(f"Backend URL: {settings.backend_url}")
        print(f"Firebase Project: {settings.firebase_project_id}")
    except ValidationError as e:
        print(f"❌ Settings validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return False
    
    # Try to initialize Firestore
    print("\n=== Testing Firestore Connection ===")
    try:
        from app.firestore_client import init_db
        init_db()
        print("✅ Firestore client initialized successfully")
    except Exception as e:
        print(f"❌ Firestore initialization error: {e}")
        return False
    
    # Try to create FastAPI app
    print("\n=== Testing FastAPI App ===")
    try:
        from app.main import app
        print("✅ FastAPI app created successfully")
        print(f"App title: {app.title}")
        print(f"App version: {app.version}")
    except Exception as e:
        print(f"❌ FastAPI app creation error: {e}")
        return False
    
    # Test port binding
    print("\n=== Testing Port Binding ===")
    try:
        import socket
        port = int(os.environ.get('PORT', '8080'))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', port))
        sock.close()
        print(f"✅ Port {port} is available for binding")
    except Exception as e:
        print(f"⚠ Port {port} binding test failed: {e}")
        # This is not necessarily fatal, could be permission issue
        
    print("\n=== All Checks Passed! ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)