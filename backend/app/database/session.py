"""SQLAlchemy engine and session management."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create the SQLAlchemy engine using the configured PostgreSQL URL."""
    settings = get_settings()
    engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)
    logger.info("Resolved DATABASE_URL: %s", settings.masked_database_url)
    logger.info("Resolved SQLAlchemy URL: %s", engine.url.render_as_string(hide_password=True))
    logger.info("Resolved SQLAlchemy driver: %s", engine.dialect.driver)
    return engine


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Create the SQLAlchemy session factory."""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for dependency injection."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def ping_database() -> bool:
    """Execute a simple query to validate PostgreSQL connectivity."""
    engine = get_engine()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception(
            "Database connection failed for %s",
            engine.url.render_as_string(hide_password=True),
        )
        raise