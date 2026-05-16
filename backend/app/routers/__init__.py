"""FastAPI routers for Conforma-AI."""

from app.routers.agents import router as agents_router
from app.routers.artifacts import router as artifacts_router
from app.routers.audits import router as audits_router
from app.routers.health import router as health_router

__all__ = ["agents_router", "artifacts_router", "audits_router", "health_router"]
