"""FastAPI entry point for the Conforma-AI backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routers import agents_router, audits_router, health_router

settings = get_settings()


def create_app() -> FastAPI:
    """Create the FastAPI application instance."""

    configure_logging()
    app = FastAPI(
        title="Conforma-AI API",
        version=settings.app_version,
        description="Local backend for the Conforma-AI multi-agent compliance demo.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(audits_router)
    return app


app = create_app()
