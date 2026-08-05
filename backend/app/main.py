"""FastAPI application entrypoint for DecisionTwin AI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.root import router as root_router
from app.api.router import api_v1_router
from app.core.config import ENV_FILE_PATH, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.database.session import ping_database

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Log service startup and shutdown events."""
    logger.info("Starting %s %s", settings.app_name, settings.app_version)
    logger.info("Using .env path: %s (exists=%s)", ENV_FILE_PATH, ENV_FILE_PATH.exists())
    logger.info("Resolved DATABASE_URL: %s", settings.masked_database_url)
    try:
        logger.info(
            "Startup database connectivity check: %s",
            "passed" if ping_database() else "failed",
        )
    except Exception as exc:  # pragma: no cover - startup logging path
        logger.warning("Startup database connectivity check failed: %s", exc)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(root_router)
app.include_router(api_v1_router)