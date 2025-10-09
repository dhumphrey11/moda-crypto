from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime

from .routers import fetch, compute, trade, admin
from .firestore_client import init_db
from .config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="Moda Crypto API",
    description="Personal crypto signal & paper trading system",
    version="1.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(fetch.router, prefix="/fetch", tags=["Data Fetching"])
app.include_router(compute.router, prefix="/compute",
                   tags=["Signal Computation"])
app.include_router(trade.router, prefix="/paper-trade", tags=["Paper Trading"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Initialize Firestore client with retry logic
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                init_db()
                logging.info("Firestore client initialized successfully")
                break
            except Exception as init_error:
                if attempt < max_retries - 1:
                    logging.warning(f"Firestore init attempt {attempt + 1} failed: {init_error}. Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    logging.error(f"Firestore initialization failed after {max_retries} attempts: {init_error}")
                    # Don't raise - let the app start anyway
                    pass
        
        logging.info("Application startup completed successfully")
    except Exception as e:
        logging.error(f"Startup error: {e}")
        # Don't raise - allow the app to start even if some initialization fails
        pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Moda Crypto API",
        "version": "1.0.1",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "port": os.environ.get('PORT', '8080')
    }


@app.get("/startup-check") 
async def startup_check():
    """Quick startup validation endpoint for Cloud Run health checks."""
    import os
    return {
        "status": "ok",
        "message": "Container is running and responding",
        "port": os.environ.get('PORT', '8080'),
        "environment": settings.environment,
        "firebase_project": settings.firebase_project_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint that aggregates system status.
    Returns status of recent runs and overall system health.
    """
    try:
        # Try to get recent runs but don't fail if Firestore is not available
        try:
            from .firestore_client import get_recent_runs
            recent_runs = get_recent_runs(hours=24)
            firestore_available = True
        except Exception as firestore_error:
            logging.warning(f"Firestore not available for health check: {firestore_error}")
            recent_runs = []
            firestore_available = False

        # Basic health check even if Firestore is down
        if not firestore_available:
            return {
                "status": "basic",
                "message": "API is running but Firestore unavailable",
                "timestamp": datetime.utcnow().isoformat(),
                "environment": settings.environment,
                "firestore_available": False
            }

        # Analyze system health if Firestore is available
        services = ['coingecko', 'moralis', 'covalent', 'lunarcrush',
                    'coinmarketcal', 'cryptopanic', 'feature_engineer',
                    'signal_compute', 'paper_trade']

        service_status = {}
        overall_healthy = True

        for service in services:
            service_runs = [r for r in recent_runs if r['service'] == service]
            if service_runs:
                latest_run = max(service_runs, key=lambda x: x['timestamp'])
                service_status[service] = {
                    'status': latest_run['status'],
                    'last_run': latest_run['timestamp'].isoformat(),
                    'count': latest_run['count'],
                    'duration': latest_run.get('duration', 0)
                }
                if latest_run['status'] != 'success':
                    overall_healthy = False
            else:
                service_status[service] = {
                    'status': 'no_data',
                    'last_run': None,
                    'count': 0,
                    'duration': 0
                }

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": service_status,
            "total_runs_24h": len(recent_runs),
            "environment": settings.environment,
            "firestore_available": True
        }

    except Exception as e:
        logging.error(f"Health check failed: {e}")
        # Return basic health status even if full health check fails
        return {
            "status": "basic",
            "message": "API is running with limited health info",
            "error": str(e) if settings.environment == "development" else "Health check error",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment
        }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logging.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
