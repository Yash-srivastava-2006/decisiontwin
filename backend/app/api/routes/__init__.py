"""Route modules for DecisionTwin AI."""

from app.api.routes.analytics import router as analytics_router
from app.api.routes.debug import router as debug_router
from app.api.routes.health import router as health_router
from app.api.routes.root import router as root_router

__all__ = ["analytics_router", "debug_router", "health_router", "root_router"]