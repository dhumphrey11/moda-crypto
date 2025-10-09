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
        
        # Start background monitoring
        try:
            from .monitoring import start_background_monitoring
            
            monitoring_started = await start_background_monitoring()
            
            if monitoring_started:
                logging.info("Background monitoring started successfully")
            else:
                logging.warning("Background monitoring was already running")
                
        except Exception as monitor_error:
            logging.error(f"Failed to start background monitoring: {monitor_error}")
            # Don't raise - allow the app to start even if monitoring fails
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
    """Enhanced health check endpoint with comprehensive system analysis."""
    try:
        from .firestore_client import get_system_health
        from .monitoring import get_monitoring_status
        
        # Get comprehensive system health
        health_data = get_system_health()
        
        # Get monitoring scheduler status
        monitoring_status = get_monitoring_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": health_data,
            "monitoring": monitoring_status
        }
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event - cleanup monitoring."""
    try:
        from .monitoring import stop_background_monitoring
        
        # Stop background monitoring
        await stop_background_monitoring()
        logging.info("Background monitoring stopped")
        
        logging.info("Application shutdown completed")
        
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")


@app.get("/monitoring/status")
async def monitoring_status():
    """Get current monitoring system status."""
    try:
        from .monitoring import get_monitoring_status
        
        status = get_monitoring_status()
        
        return {
            "status": "success",
            "monitoring": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting monitoring status: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
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
