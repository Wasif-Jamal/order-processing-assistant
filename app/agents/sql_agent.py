"""SQL Agent.

The SqlAgent is responsible for orchestrating the SQL generation workflow.

It wires together the SQL tools and exposes a compiled LangGraph node through
the public ``node`` attribute. The business logic itself lives inside the
individual SQL tools and service layer.
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.env_config import settings
from app.config.log_config import config as log_config
from app.orchestration.state import WorkflowState
from app.prompts.sql_prompt import SQL_SYSTEM_PROMPT
from app.services.database_service import DatabaseService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.sql_cache_service import SQLCacheService
from app.services.sql_template_service import SQLTemplateService
from app.tools.sql_tools import SqlTools

logger = log_config.get_logger(__name__)


class SqlAgent:
    """SQL Agent for the Order Processing Assistant."""

    _DEFAULT_RETRY_LIMIT = 3

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        sql_cache_service: SQLCacheService | None = None,
        sql_template_service: SQLTemplateService | None = None,
        knowledge_base_service: KnowledgeBaseService | None = None,
        database_service: DatabaseService | None = None,
        retry_limit: int | None = None,
    ) -> None:
        """Initialize the SQL Agent.

        Args:
            llm: Language model.
            sql_cache_service: SQL cache service.
            sql_template_service: SQL template repository service.
            knowledge_base_service: Knowledge base (RAG) service.
            database_service: Database execution service.
            retry_limit: Maximum SQL self-correction attempts.
        """
        self._retry_limit = (
            retry_limit
            if retry_limit is not None
            else getattr(
                settings,
                "sql_retry_limit",
                self._DEFAULT_RETRY_LIMIT,
            )
        )

        logger.info(
            "Initializing SqlAgent (retry_limit=%d).",
            self._retry_limit,
        )

        sql_tools = SqlTools(
            llm=llm,
            sql_cache_service=sql_cache_service,
            sql_template_service=sql_template_service,
            knowledge_base_service=knowledge_base_service,
            database_service=database_service,
        )

        # Public node consumed by LangGraph
        self.node = create_agent(
            model=llm,
            tools=[
                sql_tools.retrieve_cached_sql,
                sql_tools.retrieve_sql_template,
                sql_tools.retrieve_schema,
                sql_tools.generate_sql,
                sql_tools.validate_sql,
                sql_tools.execute_sql,
                sql_tools.save_sql_cache,
            ],
            system_prompt=SQL_SYSTEM_PROMPT,
            state_schema=WorkflowState,
            name="sql_agent",
        ).with_config(
            {
                "recursion_limit": self._retry_limit * 5 + 10,
            }
        )

        logger.info("SqlAgent initialized successfully.")
