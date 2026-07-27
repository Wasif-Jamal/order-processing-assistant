"""SQL Agent.

The SqlAgent is responsible only for wiring together the SQL pipeline.
It contains no business logic.

Responsibilities:
* Receive service dependencies.
* Instantiate tool classes.
* Register tools with LangChain's create_agent().
* Expose a LangGraph node.
"""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.env_config import settings
from app.config.log_config import config as log_config
from app.orchestration.state import WorkflowState
from app.prompts.sql_prompt import SQL_SYSTEM_PROMPT

from app.services.database_service import DatabaseService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.sql_cache_service import SQLCacheService
from app.services.sql_template_service import SQLTemplateService

from app.tools.cache_tools import CacheTools
from app.tools.execution_tools import ExecutionTools
from app.tools.generation_tools import GenerationTools
from app.tools.rag_tools import RagTools
from app.tools.template_tools import TemplateTools
from app.tools.validation_tools import validate_sql

logger = log_config.get_logger(__name__)


class SqlAgent:
    """SQL Agent."""

    _DEFAULT_RETRY_LIMIT = 3

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        sql_cache_service: SQLCacheService,
        sql_template_service: SQLTemplateService,
        knowledge_base_service: KnowledgeBaseService,
        database_service: DatabaseService,
        retry_limit: int | None = None,
    ) -> None:
        """Initialize the SQL Agent."""

        self._retry_limit = (
            retry_limit
            if retry_limit is not None
            else getattr(
                settings,
                "sql_retry_limit",
                self._DEFAULT_RETRY_LIMIT,
            )
        )

        logger.info("Initializing SqlAgent.")

        #
        # Tool instances
        #

        cache_tools = CacheTools(sql_cache_service)

        template_tools = TemplateTools(sql_template_service)

        rag_tools = RagTools(knowledge_base_service)

        generation_tools = GenerationTools(llm)

        execution_tools = ExecutionTools(
            database_service=database_service,
            sql_cache_service=sql_cache_service,
        )

        #
        # Internal ReAct Agent
        #

        self._agent = create_agent(
            model=llm,
            tools=[
                cache_tools.retrieve_cached_sql,
                template_tools.retrieve_sql_template,
                rag_tools.retrieve_schema,
                generation_tools.generate_sql,
                validate_sql,
                execution_tools.execute_sql,
            ],
            system_prompt=SQL_SYSTEM_PROMPT,
            state_schema=WorkflowState,
            name="sql_agent",
        ).with_config(
            {
                "recursion_limit": self._retry_limit * 5 + 10,
            }
        )

        logger.info("SqlAgent initialized.")

    def node(
        self,
        state: WorkflowState,
    ) -> dict[str, Any]:
        """Execute the SQL Agent."""

        logger.info("Running SQL Agent.")

        result = self._agent.invoke(
            {
                "messages": [
                    HumanMessage(content=state["question"]),
                ],
            }
        )

        logger.info("SQL Agent completed.")

        return result