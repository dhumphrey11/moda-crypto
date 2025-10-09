#!/bin/bash
# Startup         echo "WARNING: Startup validation failed with exit code $result"
        echo "Continuing with startup - will retry Firebase initialization on first request..."
        # Always continue in production to allow Cloud Run health checksfor Cloud Run
# Uses PORT environment variable provided by Cloud Run, defaults to 8080 for local development

PORT=${PORT:-8080}
echo "=== Container Startup ==="
echo "Starting FastAPI server on port $PORT"
echo "Environment: ${ENVIRONMENT:-development}"
echo "Firebase Project ID: ${FIREBASE_PROJECT_ID:-not-set}"
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Available files:"
ls -la
echo "App directory contents:"
ls -la app/
echo "=========================="

# Always run basic startup checks in production to catch issues early
echo "Running startup validation..."
python debug_startup.py
startup_result=$?
if [ $startup_result -ne 0 ]; then
    echo "WARNING: Startup validation failed with exit code $startup_result"
    if [[ "${ENVIRONMENT}" == "production" ]]; then
        echo "In production, continuing despite validation warnings..."
    else
        echo "In development, exiting due to validation failure"
        exit $startup_result
    fi
fi

# Test basic Python imports
echo "Testing critical imports..."
python -c "
import sys
print(f'Python path: {sys.path}')
try:
    import fastapi
    print('✓ FastAPI imported successfully')
    import uvicorn  
    print('✓ Uvicorn imported successfully')
    import firebase_admin
    print('✓ Firebase Admin imported successfully')
    from app.main import app
    print('✓ App module imported successfully')
except Exception as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Critical import test failed!"
    exit 1
fi

echo "All startup checks passed. Starting uvicorn server..."
echo "Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300"

# Start the server
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300