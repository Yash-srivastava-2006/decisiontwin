"""Dataset business logic and CSV processing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from uuid import UUID

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import DatasetCreateMetadata
from app.utils.storage import build_unique_csv_path, delete_file_if_exists

logger = logging.getLogger(__name__)

MAX_DATASET_SIZE_BYTES = 50 * 1024 * 1024
PREVIEW_ROWS = 20


@dataclass(slots=True)
class ParsedDataset:
    """Normalized CSV payload and derived statistics."""

    dataframe: pd.DataFrame
    columns: list[str]
    dtypes: dict[str, str]
    missing_values: dict[str, int]


class DatasetService:
    """Coordinates validation, CSV parsing, storage, and persistence."""

    def __init__(self, session: Session) -> None:
        self.repository = DatasetRepository(session)
        self.session = session

    def list_datasets(self) -> list[Dataset]:
        return self.repository.list_all()

    def get_dataset(self, dataset_id: UUID) -> Dataset:
        dataset = self.repository.get(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset

    def create_dataset(self, file: UploadFile, metadata: DatasetCreateMetadata) -> Dataset:
        self._validate_upload_file(file)
        raw_bytes = file.file.read()
        if not raw_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
        if len(raw_bytes) > MAX_DATASET_SIZE_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="CSV file exceeds 50 MB")

        parsed = self._parse_csv(raw_bytes)
        stored_filename, stored_path = build_unique_csv_path()
        stored_path.write_bytes(raw_bytes)

        dataset = Dataset(
            name=metadata.name,
            original_filename=file.filename or stored_filename,
            description=metadata.description,
            file_type="csv",
            file_size=len(raw_bytes),
            total_rows=int(parsed.dataframe.shape[0]),
            total_columns=int(parsed.dataframe.shape[1]),
            file_path=str(stored_path),
            columns=parsed.columns,
            dtypes=parsed.dtypes,
            missing_values=parsed.missing_values,
        )

        try:
            self.repository.add(dataset)
            self.session.commit()
        except Exception:
            self.session.rollback()
            delete_file_if_exists(str(stored_path))
            logger.exception("Failed to persist dataset metadata")
            raise

        return dataset

    def delete_dataset(self, dataset_id: UUID) -> None:
        dataset = self.get_dataset(dataset_id)
        stored_path = dataset.file_path
        self.repository.delete(dataset_id)
        self.session.commit()
        delete_file_if_exists(stored_path)

    def preview_dataset(self, dataset_id: UUID) -> dict[str, object]:
        dataset = self.get_dataset(dataset_id)
        dataframe = self.load_dataset_dataframe(dataset)
        return {
            "columns": dataset.columns,
            "dtypes": dataset.dtypes,
            "preview": dataframe.head(PREVIEW_ROWS).to_dict(orient="records"),
            "summary": {"rows": dataset.total_rows, "columns": dataset.total_columns},
        }

    def load_dataset_dataframe(self, dataset: Dataset) -> pd.DataFrame:
        """Load the stored CSV for an existing dataset record."""
        return self._load_dataframe(Path(dataset.file_path))

    def _validate_upload_file(self, file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A CSV file is required")
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are allowed")
        content_type = (file.content_type or "").lower()
        if content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain", ""}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are allowed")

    def _read_csv(self, source: StringIO | Path) -> pd.DataFrame:
        """Read a CSV while automatically detecting common delimiters."""
        try:
            if isinstance(source, Path):
                return pd.read_csv(source, sep=None, engine="python")

            return pd.read_csv(source, sep=None, engine="python")

        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
            logger.exception("Failed to parse CSV")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed CSV file",
            ) from exc
        
    def _parse_csv(self, raw_bytes: bytes) -> ParsedDataset:
        try:
            dataframe = self._read_csv(StringIO(raw_bytes.decode("utf-8-sig")))
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file must be UTF-8 encoded") from exc
        except Exception as exc:
            logger.exception("Malformed CSV upload")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed CSV file") from exc

        if dataframe.empty and len(dataframe.columns) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file does not contain data")

        columns = [str(column) for column in dataframe.columns.tolist()]
        dtypes = {str(column): str(dtype) for column, dtype in dataframe.dtypes.items()}
        missing_values = {str(column): int(value) for column, value in dataframe.isna().sum().items()}
        return ParsedDataset(dataframe=dataframe, columns=columns, dtypes=dtypes, missing_values=missing_values)

    def _load_dataframe(self, file_path: Path) -> pd.DataFrame:
        if not file_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored dataset file not found")

        try:
            return self._read_csv(file_path)
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
            logger.exception("Malformed stored CSV at %s", file_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stored dataset CSV is invalid") from exc
        except Exception as exc:
            logger.exception("Failed to load dataset CSV from %s", file_path)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stored dataset could not be read") from exc
