"""Filesystem helpers for stored uploads."""

from __future__ import annotations

import uuid
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
STORAGE_ROOT = BACKEND_ROOT / "storage"
UPLOADS_DIR = STORAGE_ROOT / "uploads"


def ensure_uploads_dir() -> Path:
    """Create the upload directory if it does not exist."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOADS_DIR


def build_unique_csv_path() -> tuple[str, Path]:
    """Generate a unique CSV filename and absolute storage path."""
    ensure_uploads_dir()
    file_id = uuid.uuid4()
    filename = f"{file_id}.csv"
    return filename, UPLOADS_DIR / filename


def delete_file_if_exists(file_path: str) -> None:
    """Remove a stored file if it exists."""
    path = Path(file_path)
    if path.exists():
        path.unlink()
