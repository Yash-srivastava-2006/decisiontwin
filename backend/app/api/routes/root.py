"""Root service route."""

from fastapi import APIRouter

from app.schemas.common import MessageResponse

router = APIRouter(tags=["root"])


@router.get("/", response_model=MessageResponse, summary="Service status")
def read_root() -> MessageResponse:
    """Return the service running message."""
    return MessageResponse(message="DecisionTwin AI Backend Running")