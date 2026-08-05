"""Dataset request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatasetUploadResponse(BaseModel):
    """Response payload after dataset upload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_filename: str
    description: str | None = None
    file_type: str
    file_size: int
    total_rows: int
    total_columns: int
    file_path: str
    columns: list[str]
    dtypes: dict[str, str]
    missing_values: dict[str, int]
    uploaded_at: datetime
    updated_at: datetime


class DatasetListItem(BaseModel):
    """Compact dataset list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_filename: str
    description: str | None = None
    file_type: str
    file_size: int
    total_rows: int
    total_columns: int
    file_path: str
    uploaded_at: datetime
    updated_at: datetime


class DatasetDetailResponse(DatasetUploadResponse):
    """Complete dataset metadata response."""


class DatasetPreviewResponse(BaseModel):
    """Dataset preview response."""

    model_config = ConfigDict(from_attributes=True)

    columns: list[str]
    dtypes: dict[str, str]
    preview: list[dict[str, object]]
    summary: dict[str, int]


class DatasetCreateMetadata(BaseModel):
    """Validated dataset upload metadata."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
