"""Versioned API router registration."""

from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.debug import router as debug_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(debug_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(analytics_router)