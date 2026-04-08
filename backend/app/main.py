"""
FastAPI application entry-point.

Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.models.ml_model import awg_model

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan (startup / shutdown hooks)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Load the persisted ML model on startup (if it exists).

    Falls back to auto-training on first prediction if the artefact is not
    found — so the service is always usable out of the box.
    """
    logger.info("Starting %s …", settings.app_name)
    loaded = awg_model.load(settings.model_path_resolved)
    if loaded:
        logger.info("Pre-trained model loaded from %s", settings.model_path_resolved)
    else:
        logger.info(
            "No pre-trained model found at %s — will auto-train on first request.",
            settings.model_path_resolved,
        )
    yield
    logger.info("%s shutting down.", settings.app_name)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        description=(
            "Backend API for analysing Atmospheric Water Generation (AWG) suitability "
            "using real-time weather data and a machine-learning model."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — allow the configured frontend origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all API routes
    application.include_router(router)

    return application


# Module-level app instance (used by uvicorn)
app = create_app()


# ---------------------------------------------------------------------------
# Root and health-check endpoints
# ---------------------------------------------------------------------------


@app.get("/", tags=["Meta"], summary="Service information")
async def root() -> dict:
    """Return basic service metadata."""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Meta"], summary="Health check")
async def health() -> dict:
    """Return the operational status of the service and the ML model."""
    return {
        "status": "ok",
        "model_trained": awg_model.is_trained,
        "debug": settings.debug,
    }
