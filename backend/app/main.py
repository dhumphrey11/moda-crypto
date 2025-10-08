from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
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
    version="1.0.0",
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
        # Initialize Firestore client
        init_db()
        logging.info("Application startup completed successfully")
    except Exception as e:
        logging.error(f"Startup failed: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Moda Crypto API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint that aggregates system status.
    Returns status of recent runs and overall system health.
    """
    try:
        from .firestore_client import get_recent_runs

        # Get recent runs from last 24 hours
        recent_runs = get_recent_runs(hours=24)

        # Analyze system health
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
                overall_healthy = False

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": service_status,
            "total_runs_24h": len(recent_runs),
            "environment": settings.environment
        }

    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


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
