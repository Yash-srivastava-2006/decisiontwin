"""Database diagnostics helpers for safe debugging output."""

from __future__ import annotations

from typing import Any

from sqlalchemy.engine import Engine

from app.database.session import get_engine


def build_database_diagnostics(connection_success: bool, error: str | None = None) -> dict[str, Any]:
    """Return a safe, structured snapshot of the active database connection settings."""
    engine: Engine = get_engine()
    url = engine.url

    return {
        "host": url.host or "",
        "port": str(url.port or ""),
        "database": url.database or "",
        "username": url.username or "",
        "driver": engine.dialect.driver,
        "database_url_masked": url.render_as_string(hide_password=True),
        "connection_success": connection_success,
        "error": error or "",
    }
