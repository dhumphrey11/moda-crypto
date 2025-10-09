#!/bin/bash
# Startup script for Cloud Run
# Uses PORT environment variable provided by Cloud Run, defaults to 8000 for local development

PORT=${PORT:-8000}
echo "Starting FastAPI server on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT