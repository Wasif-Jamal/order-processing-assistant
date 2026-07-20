"""Application bootstrap / app factory.

Builds the FastAPI application
``app/main.py`` exposes the result as the ASGI entry point for Uvicorn.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.db_config import Base
from app.config.db_config import database
from app.config.log_config import config

logger = config.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application resources."""

    logger.info("Intializing resources")

    logger.info("Resources initialized.")

    yield

    logger.info("Application shutdown.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Order Processing Assistant",
        lifespan=lifespan,
    )

    return app
