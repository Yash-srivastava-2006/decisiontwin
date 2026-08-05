"""Common response schemas."""

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    """Standard message response."""

    model_config = ConfigDict(from_attributes=True)

    message: str