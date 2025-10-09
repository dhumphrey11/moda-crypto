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
    print()
    
    # Check environment variables
    print("=== Environment Variables ===")
    required_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_CLIENT_EMAIL', 
        'FIREBASE_PRIVATE_KEY',
        'FIREBASE_STORAGE_BUCKET',
        'PORT'
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if 'PRIVATE_KEY' in var:
                print(f"{var}: [SET - length: {len(value)}]")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: [NOT SET] ❌")
    
    print()
    
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
        
    print("\n=== All Checks Passed! ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)