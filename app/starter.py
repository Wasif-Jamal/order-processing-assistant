"""Application bootstrap / app factory.

Builds the FastAPI application and initializes the database, vector stores,
workflow graph, and API routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.env_config import settings
from app.config.log_config import config
from app.orchestration.graph import OrderProcessingGraph
from app.routes.chat_routes import ChatRouter
from app.routes.health_routes import HealthRouter
from app.services.chat_service import ChatService
from app.utils.database.database_initializer import DatabaseInitializer
from app.utils.database.knowledge_base_initializer import (
    KnowledgeBaseInitializer,
)
from app.utils.database.sql_template_initializer import (
    SQLTemplateInitializer,
)

from app.services.database_service import DatabaseService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.sql_cache_service import SQLCacheService
from app.services.sql_template_service import SQLTemplateService

database_service = DatabaseService()
knowledge_base_service = KnowledgeBaseService()
sql_cache_service = SQLCacheService()
sql_template_service = SQLTemplateService()

logger = config.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application resources."""

    logger.info("Initializing database.")
    DatabaseInitializer().initialize()
    logger.info("Database initialized.")

    logger.info("Initializing knowledge base.")
    KnowledgeBaseInitializer().initialize()
    logger.info("Knowledge base initialized.")

    logger.info("Initializing SQL templates.")
    SQLTemplateInitializer().initialize()
    logger.info("SQL templates initialized.")

    yield

    logger.info("Application shutdown.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    config.configure_langchain_logging(
        verbose=settings.langchain_verbose,
        debug=settings.langchain_debug,
    )

    app = FastAPI(
        title="Order Processing Assistant",
        lifespan=lifespan,
    )

    logger.info("Creating language model.")

    llm = ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.google_api_key,
        temperature=0,
    )

    logger.info("Building workflow graph.")

    workflow = OrderProcessingGraph(
        llm=llm,
        sql_cache_service=sql_cache_service,
        sql_template_service=sql_template_service,
        knowledge_base_service=knowledge_base_service,
        database_service=database_service,
    ).build()

    chat_service = ChatService(workflow)

    app.include_router(ChatRouter(chat_service).router)
    app.include_router(HealthRouter().router)

    logger.info("Application created successfully.")

    return app
