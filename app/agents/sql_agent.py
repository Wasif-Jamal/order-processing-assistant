"""SQL Agent.

``SqlAgent`` is a lightweight LangGraph node orchestrator. It:

* Accepts injected service dependencies.
* Instantiates :class:`~app.tools.sql_tools.SqlTools` with those dependencies.
* Registers the tools with ``create_agent()``.
* Exposes the compiled node as ``self.node``.

All SQL pipeline business logic lives in the service layer.
The agent itself contains no SQL logic.
"""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

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
    """Lightweight LangGraph SQL Agent for the Order Processing Assistant.

    The agent owns no SQL logic.  It wires service dependencies into
    :class:`~app.tools.sql_tools.SqlTools`, registers those tools with
    ``create_agent()``, and exposes a compiled LangGraph node at
    ``self.node``.

    Args:
        llm: Chat model passed to SqlTools for dynamic SQL generation.
        sql_cache_service: Optional pre-configured cache service.
        sql_template_service: Optional pre-configured template service.
        knowledge_base_service: Optional pre-configured knowledge base service.
        database_service: Optional pre-configured database service.
        retry_limit: Maximum number of self-correction iterations.
            Defaults to ``settings.sql_retry_limit`` when not supplied.
    """

    _DEFAULT_RETRY_LIMIT: int = 3

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        sql_cache_service: SQLCacheService | None = None,
        sql_template_service: SQLTemplateService | None = None,
        knowledge_base_service: KnowledgeBaseService | None = None,
        database_service: DatabaseService | None = None,
        retry_limit: int | None = None,
    ) -> None:
        """Initialize the SqlAgent with injected service dependencies.

        Args:
            llm: Language model passed to SqlTools for SQL generation.
            sql_cache_service: Two-layer Qdrant + SQL Server cache service.
            sql_template_service: Qdrant + SQL Server template search service.
            knowledge_base_service: Qdrant RAG schema metadata service.
            database_service: Validated SELECT query execution service.
            retry_limit: Maximum self-correction iterations for SQL validation
                failures.  Defaults to ``settings.sql_retry_limit`` if defined,
                otherwise :attr:`_DEFAULT_RETRY_LIMIT`.
        """
        self._retry_limit = (
            retry_limit
            if retry_limit is not None
            else getattr(settings, "sql_retry_limit", self._DEFAULT_RETRY_LIMIT)
        )

        logger.info("Initializing SqlAgent (retry_limit=%d).", self._retry_limit)

        sql_tools = SqlTools(
            llm=llm,
            sql_cache_service=sql_cache_service,
            sql_template_service=sql_template_service,
            knowledge_base_service=knowledge_base_service,
            database_service=database_service,
        )

        self._agent = create_agent(
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
            state_schema=WorkflowState,
            prompt=SQL_SYSTEM_PROMPT,
            name="sql_agent",
        ).with_config(
            {
                "recursion_limit": self._retry_limit * 5 + 10,
            }
        )

        logger.info("SqlAgent initialized successfully.")
