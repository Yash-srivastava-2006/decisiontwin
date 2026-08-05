"""Health check routes."""

from fastapi import APIRouter, Response, status
from starlette.concurrency import run_in_threadpool

from app.database.session import ping_database
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application and database health check",
    status_code=status.HTTP_200_OK,
)
async def health_check(response: Response) -> HealthResponse:
    """Check service and PostgreSQL connectivity."""
    try:
        database_connected = await run_in_threadpool(ping_database)
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unhealthy", database="disconnected")

    return HealthResponse(status="healthy", database="connected" if database_connected else "disconnected")