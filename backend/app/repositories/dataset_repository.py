"""Dataset repository for database persistence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset


class DatasetRepository:
    """Persistence operations for datasets."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, dataset: Dataset) -> Dataset:
        """Persist a new dataset record."""
        self.session.add(dataset)
        self.session.flush()
        return dataset

    def list_all(self) -> list[Dataset]:
        """Return all datasets ordered by newest first."""
        stmt = select(Dataset).order_by(Dataset.uploaded_at.desc())
        return list(self.session.scalars(stmt).all())

    def get(self, dataset_id: UUID) -> Dataset | None:
        """Return a dataset by identifier."""
        return self.session.get(Dataset, dataset_id)

    def delete(self, dataset_id: UUID) -> bool:
        """Delete a dataset by identifier."""
        result = self.session.execute(delete(Dataset).where(Dataset.id == dataset_id))
        return bool(result.rowcount)
