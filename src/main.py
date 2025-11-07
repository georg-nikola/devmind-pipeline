"""
DevMind Pipeline - AI-Enhanced DevOps Automation Platform
Main application entry point for Python AI/ML services
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.routers import build_optimizer, failure_predictor, test_intelligence
from core.config import get_settings
from core.logging import setup_logging
from core.monitoring import setup_monitoring
from services.ml_service_manager import MLServiceManager

# Configure structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global service manager instance
ml_service_manager: MLServiceManager = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    global ml_service_manager

    logger.info("Starting DevMind Pipeline ML Services")

    # Initialize ML service manager
    ml_service_manager = MLServiceManager()
    await ml_service_manager.initialize()

    # Setup monitoring
    setup_monitoring()

    logger.info("ML Services initialized successfully")

    yield

    # Cleanup
    logger.info("Shutting down ML Services")
    if ml_service_manager:
        await ml_service_manager.cleanup()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="DevMind Pipeline ML Services",
        description="AI-Enhanced DevOps Automation Platform",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(
        build_optimizer.router,
        prefix="/api/v1/build-optimizer",
        tags=["Build Optimization"],
    )
    app.include_router(
        failure_predictor.router,
        prefix="/api/v1/failure-predictor",
        tags=["Failure Prediction"],
    )
    app.include_router(
        test_intelligence.router,
        prefix="/api/v1/test-intelligence",
        tags=["Test Intelligence"],
    )

    return app


app = create_app()


@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with service information."""
    return {
        "service": "DevMind Pipeline ML Services",
        "version": "1.0.0",
        "status": "healthy",
        "features": [
            "AI-powered build optimization",
            "Predictive failure analysis",
            "Intelligent test selection",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global ml_service_manager

    if not ml_service_manager:
        raise HTTPException(status_code=503, detail="ML services not initialized")

    health_status = await ml_service_manager.health_check()

    if not health_status["healthy"]:
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()


@app.get("/models/status")
async def models_status():
    """Get status of all ML models."""
    global ml_service_manager

    if not ml_service_manager:
        raise HTTPException(status_code=503, detail="ML services not initialized")

    return await ml_service_manager.get_models_status()


@app.post("/models/retrain/{model_name}")
async def retrain_model(model_name: str):
    """Trigger model retraining."""
    global ml_service_manager

    if not ml_service_manager:
        raise HTTPException(status_code=503, detail="ML services not initialized")

    try:
        result = await ml_service_manager.retrain_model(model_name)
        return {"message": f"Retraining triggered for {model_name}", "task_id": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to trigger retraining", model=model_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger retraining")


if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.ENVIRONMENT == "development",
        workers=1 if settings.ENVIRONMENT == "development" else settings.WORKERS,
    )
