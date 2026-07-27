"""Cache tools used by the SQL Agent.

This module exposes LangChain tools for interacting with the SQL cache.
The tools are thin wrappers around ``SQLCacheService`` and contain no
business logic themselves.

Responsibilities:

* Retrieve previously generated SQL from the cache.
* Save successful SQL executions back to the cache.

Both tools update the shared LangGraph ``WorkflowState`` using
``Command(update=...)``.
"""

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated

from langchain_core.tools import tool
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId

from app.config.log_config import config as log_config
from app.services.sql_cache_service import SQLCacheService


logger = log_config.get_logger(__name__)


class CacheTools:
    """Cache-related tools for the SQL Agent."""

    def __init__(
        self,
        sql_cache_service: SQLCacheService,
    ) -> None:
        """Initialize cache tools.

        Args:
            sql_cache_service: SQL cache service.
        """
        self._cache_service = sql_cache_service

        @tool
        def retrieve_cached_sql(
            question: str,
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            """Retrieve SQL from cache.

            Searches the vector cache for a semantically similar question.

            Args:
                question: User question.

            Returns:
                Command updating the workflow state.
            """
            logger.info(
                "Searching SQL cache for question: %s",
                question,
            )

            result = self._cache_service.search(question)

            if result is None:
                logger.info("SQL cache miss.")

                return Command(
                    update={
                        "generated_sql": None,
                        "sql_source": None,
                        "messages": [
                            ToolMessage(
                                content="SQL cache miss.",
                                tool_call_id=tool_call_id,
                            )
                        ],
                    }
                )

            logger.info(
                "SQL cache hit (score=%.3f).",
                result.similarity_score,
            )

            return Command(
                update={
                    "generated_sql": result.generated_sql,
                    "sql_source": "cache",
                    "sql_explanation": result.sql_explanation,
                    "messages": [
                        ToolMessage(
                            content="SQL cache hit.",
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )

        @tool
        def save_sql_cache(
            question: str,
            sql: str,
            explanation: Optional[str] = None,
        ) -> str:
            """Save a successful SQL query to cache.

            Args:
                question: Original user question.
                sql: Generated SQL.
                explanation: Optional SQL explanation.

            Returns:
                Status string.
            """
            logger.info(
                "Saving SQL to cache.",
            )

            try:
                self._cache_service.save_cache(
                    user_question=question,
                    generated_sql=sql,
                    sql_explanation=explanation,
                )

                logger.info("SQL cached successfully.")

                return "SAVED"

            except Exception:
                logger.exception("Unable to save SQL cache.")
                return "SAVE_FAILED"

        self.retrieve_cached_sql = retrieve_cached_sql
        self.save_sql_cache = save_sql_cache
