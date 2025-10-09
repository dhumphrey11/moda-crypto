#!/bin/bash
# Startup script for Cloud Run
# Uses PORT environment variable provided by Cloud Run, defaults to 8080 for local development

PORT=${PORT:-8080}
echo "Starting FastAPI server on port $PORT"
echo "Environment: ${ENVIRONMENT:-development}"
echo "Firebase Project ID: ${FIREBASE_PROJECT_ID:-not-set}"

# Run debug checks if in development or if DEBUG=true
if [[ "${ENVIRONMENT}" == "development" || "${DEBUG}" == "true" ]]; then
    echo "Running startup debug checks..."
    python debug_startup.py
    if [ $? -ne 0 ]; then
        echo "Debug checks failed, but continuing..."
    fi
fi

echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 300