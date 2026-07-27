"""SQL execution tools used by the SQL Agent.

This module exposes LangChain tools for executing validated SQL queries
against the database. The tool delegates execution to DatabaseService and,
upon successful execution, stores the query in the SQL cache.

Responsibilities:

* Execute validated SELECT statements.
* Persist successful queries to the SQL cache.
* Update WorkflowState.

The tool updates the shared LangGraph ``WorkflowState`` using
``Command(update=...)``.
"""

from __future__ import annotations
from typing_extensions import Annotated

from langchain_core.tools import tool
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId

from app.config.log_config import config as log_config
from app.schemas.sql_result_schema import QueryResult
from app.services.database_service import DatabaseService
from app.services.sql_cache_service import SQLCacheService

logger = log_config.get_logger(__name__)


class ExecutionTools:
    """Database execution tools."""

    def __init__(
        self,
        database_service: DatabaseService,
        sql_cache_service: SQLCacheService,
    ) -> None:
        """Initialize execution tools.

        Args:
            database_service: Database execution service.
            sql_cache_service: SQL cache service.
        """
        self._database_service = database_service
        self._cache_service = sql_cache_service

        @tool
        def execute_sql(
            question: str,
            validated_sql: str,
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            """Execute validated SQL.

            Args:
                question: Original user question.
                validated_sql: SQL that has passed validation.

            Returns:
                Command updating WorkflowState.
            """
            logger.info("Executing validated SQL.")

            try:
                result: QueryResult = self._database_service.execute_query(
                    sql=validated_sql,
                )

                logger.info(
                    "Returned %d row(s).",
                    result.row_count,
                )

                # Cache only successful executions.
                self._cache_service.save_cache(
                    user_question=question,
                    generated_sql=validated_sql,
                )

                return Command(
                    update={
                        "query_result": result,
                        "messages": [
                            ToolMessage(
                                content="SQL executed successfully.",
                                tool_call_id=tool_call_id,
                            )
                        ],
                    }
                )

            except Exception:
                logger.exception("Database execution failed.")

                return Command(
                    update={
                        "error_message": "Query execution failed.",
                        "messages": [
                            ToolMessage(
                                content="Query execution failed.",
                                tool_call_id=tool_call_id,
                            )
                        ],
                    }
                )

        self.execute_sql = execute_sql
