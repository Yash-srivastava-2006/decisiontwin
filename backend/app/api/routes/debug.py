"""Temporary database debug endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.database.diagnostics import build_database_diagnostics
from app.database.session import ping_database

router = APIRouter(tags=["debug"])


@router.get("/debug/database")
def debug_database() -> dict[str, object]:
    """Return safe diagnostics for the configured PostgreSQL connection."""
    try:
        connection_success = ping_database()
        return build_database_diagnostics(connection_success=connection_success, error="")
    except Exception as exc:
        return build_database_diagnostics(connection_success=False, error=f"{type(exc).__name__}: {exc}")