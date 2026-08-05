"""Health check response schema."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Health response for the API."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    database: str