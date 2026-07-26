"""Application bootstrap / app factory.

Builds the FastAPI application
``app/main.py`` exposes the result as the ASGI entry point for Uvicorn.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.db_config import Base
from app.config.db_config import database
from app.config.log_config import config
from app.orchestration import graph
from app.routes.health_routes import HealthRouter
from app.routes.chat_routes import ChatRouter
from app.services.chat_service import ChatService
from app.utils.database.database_initializer import DatabaseInitializer
from app.utils.database.knowledge_base_initializer import KnowledgeBaseInitializer
from app.utils.database.sql_template_initializer import SQLTemplateInitializer

logger = config.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application resources."""

    logger.info("Initializing database")

    initializer = DatabaseInitializer()
    initializer.initialize()

    logger.info("Database initialized.")

    logger.info("Initializing Knowledge Base vector store.")
    kb_initializer = KnowledgeBaseInitializer()
    kb_initializer.initialize()
    logger.info("Knowledge Base initialized.")

    logger.info("Initializing SQL Templates vector repository.")
    template_initializer = SQLTemplateInitializer()
    template_initializer.initialize()
    logger.info("SQL Templates initialized.")

    chat_service = ChatService(graph)

    app.include_router(ChatRouter(chat_service).router)
    app.include_router(HealthRouter().router)

    yield

    logger.info("Application shutdown.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Order Processing Assistant",
        lifespan=lifespan,
    )

    return app
