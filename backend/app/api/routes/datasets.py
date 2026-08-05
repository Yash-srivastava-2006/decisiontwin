"""Dataset management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.dataset import (
    DatasetCreateMetadata,
    DatasetDetailResponse,
    DatasetListItem,
    DatasetPreviewResponse,
    DatasetUploadResponse,
)
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_dataset_service(session: Session = Depends(get_db)) -> DatasetService:
    """Return the dataset service for the current request."""
    return DatasetService(session)


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    summary="Upload a CSV dataset",
    description="Accepts a CSV upload, validates it, stores the file on disk, and persists metadata in PostgreSQL.",
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str | None = Form(default=None),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetUploadResponse:
    """Upload and register a dataset from a CSV file."""
    metadata = DatasetCreateMetadata(name=name, description=description)
    dataset = service.create_dataset(file=file, metadata=metadata)
    return DatasetUploadResponse.model_validate(dataset)


@router.get(
    "",
    response_model=list[DatasetListItem],
    summary="List uploaded datasets",
    description="Returns all uploaded datasets ordered by newest upload first.",
)
def list_datasets(service: DatasetService = Depends(get_dataset_service)) -> list[DatasetListItem]:
    """List all datasets."""
    return [DatasetListItem.model_validate(dataset) for dataset in service.list_datasets()]


@router.get(
    "/{dataset_id}",
    response_model=DatasetDetailResponse,
    summary="Get dataset details",
    description="Returns the full dataset metadata record for the requested dataset ID.",
)
def get_dataset(dataset_id: UUID, service: DatasetService = Depends(get_dataset_service)) -> DatasetDetailResponse:
    """Fetch a single dataset by identifier."""
    return DatasetDetailResponse.model_validate(service.get_dataset(dataset_id))


@router.get(
    "/{dataset_id}/preview",
    response_model=DatasetPreviewResponse,
    summary="Preview a dataset",
    description="Returns the first 20 rows, column names, dtypes, and a compact summary.",
)
def preview_dataset(dataset_id: UUID, service: DatasetService = Depends(get_dataset_service)) -> DatasetPreviewResponse:
    """Return a preview for a stored dataset."""
    return DatasetPreviewResponse.model_validate(service.preview_dataset(dataset_id))


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dataset",
    description="Deletes the dataset metadata from PostgreSQL and removes the stored CSV file.",
)
def delete_dataset(
    dataset_id: UUID,
    response: Response,
    service: DatasetService = Depends(get_dataset_service),
) -> None:
    """Delete a dataset and its stored file."""
    service.delete_dataset(dataset_id)
    response.status_code = status.HTTP_204_NO_CONTENT
