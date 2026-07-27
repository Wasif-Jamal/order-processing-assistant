"""SQL tools used by the SQL Agent.

Each tool is a thin wrapper that delegates entirely to an existing service.
No business logic lives inside this module; all SQL pipeline behaviour is
owned by the service layer.

Tools registered here:

* ``retrieve_cached_sql``  → :class:`~app.services.sql_cache_service.SQLCacheService`
* ``retrieve_sql_template`` → :class:`~app.services.sql_template_service.SQLTemplateService`
* ``retrieve_schema``       → :class:`~app.services.knowledge_base_service.KnowledgeBaseService`
* ``generate_sql``          → :class:`~langchain_google_genai.ChatGoogleGenerativeAI` (LLM direct call)
* ``validate_sql``          → :func:`~app.utils.validators.validate_select_only`
* ``execute_sql``           → :class:`~app.services.database_service.DatabaseService`
* ``save_sql_cache``        → :class:`~app.services.sql_cache_service.SQLCacheService`
"""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.env_config import settings
from app.config.log_config import config as log_config
from app.prompts.sql_prompt import SQL_SYSTEM_PROMPT
from app.schemas.sql_result_schema import QueryResult
from app.services.database_service import DatabaseService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.sql_cache_service import SQLCacheService
from app.services.sql_template_service import SQLTemplateService
from app.utils.validators import validate_select_only

logger = log_config.get_logger(__name__)


class SqlTools:
    """Thin tool wrappers for the SQL Agent.

    Each method is decorated with ``@tool`` so LangGraph can register it.
    The methods contain no SQL logic; they simply forward calls to the
    appropriate service and surface a plain string result for the agent.

    Args:
        llm: Chat model used exclusively for the ``generate_sql`` tool.
        sql_cache_service: Service managing two-layer SQL caching.
        sql_template_service: Service managing curated SQL template search.
        knowledge_base_service: Service providing schema metadata via RAG.
        database_service: Service executing validated read-only SQL queries.
    """

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        sql_cache_service: SQLCacheService | None = None,
        sql_template_service: SQLTemplateService | None = None,
        knowledge_base_service: KnowledgeBaseService | None = None,
        database_service: DatabaseService | None = None,
    ) -> None:
        """Initialize SqlTools with injected service dependencies.

        Args:
            llm: Language model for dynamic SQL generation.
            sql_cache_service: Manages Qdrant + SQL Server SQL caching.
            sql_template_service: Manages Qdrant + SQL Server template search.
            knowledge_base_service: Provides schema metadata from Qdrant RAG layer.
            database_service: Executes validated SELECT queries against SQL Server.
        """
        self._llm = llm
        if sql_cache_service is None:
            raise ValueError("SQLCacheService is required")
        self._cache_service = sql_cache_service

        if sql_template_service is None:
            raise ValueError("SQLTemplateService is required")
        self._template_service = sql_template_service

        if knowledge_base_service is None:
            raise ValueError("KnowledgeBaseService is required")
        self._kb_service = knowledge_base_service

        if database_service is None:
            raise ValueError("DatabaseService is required")
        self._db_service = database_service

        logger.info("SqlTools initialized with all service dependencies.")

    # ------------------------------------------------------------------
    # Tool 1 – SQL Cache
    # ------------------------------------------------------------------

    @tool
    def retrieve_cached_sql(self, question: str) -> str:
        """Retrieve a cached SQL query that matches the user's natural language question.

        Searches the Qdrant vector cache and SQL Server for a previously generated
        and validated SQL query.  Returns the cached SQL string when a match is
        found above the configured similarity threshold, or an empty string when
        no suitable cache entry exists.

        Args:
            question: The user's natural language question.

        Returns:
            Cached SQL statement string, or empty string on cache miss.
        """
        logger.info("Tool: retrieve_cached_sql called for question: '%s'.", question)

        result = self._cache_service.search(question=question)

        if result is None:
            logger.info("Cache miss for question: '%s'.", question)
            return ""

        logger.info(
            "Cache hit (cache_id=%s, score=%.4f, hits=%d).",
            result.cache_id,
            result.similarity_score,
            result.hit_count,
        )
        return result.generated_sql

    # ------------------------------------------------------------------
    # Tool 2 – SQL Template
    # ------------------------------------------------------------------

    @tool
    def retrieve_sql_template(self, question: str) -> str:
        """Retrieve a pre-defined SQL template matching the user's natural language question.

        Searches the Qdrant template collection for a curated SELECT template.
        Returns the SQL query string of the best matching template, or an empty
        string when no template meets the similarity threshold.

        Args:
            question: The user's natural language question.

        Returns:
            Template SQL string, or empty string when no match is found.
        """
        logger.info("Tool: retrieve_sql_template called for question: '%s'.", question)

        template = self._template_service.search_template(question=question)

        if template is None:
            logger.info("No template match for question: '%s'.", question)
            return ""

        logger.info("Template match found: '%s'.", template.name)
        return template.sql_query

    # ------------------------------------------------------------------
    # Tool 3 – Schema / RAG
    # ------------------------------------------------------------------

    @tool
    def retrieve_schema(self, question: str, limit: int = 5) -> str:
        """Retrieve relevant database schema metadata for a natural language question.

        Uses the Knowledge Base RAG layer (Qdrant) to find the most relevant
        table definitions for the given question.  Returns a JSON-formatted
        string of schema metadata for use in dynamic SQL generation.

        Args:
            question: The user's natural language question.
            limit: Maximum number of table schemas to return.

        Returns:
            JSON string containing a list of relevant schema metadata objects.
        """
        logger.info("Tool: retrieve_schema called for question: '%s'.", question)

        schemas = self._kb_service.search_schema(question=question, limit=limit)

        if not schemas:
            logger.warning("No schema metadata found for question: '%s'.", question)
            return json.dumps([])

        schema_data = [s.model_dump() for s in schemas]
        logger.info("Retrieved %d schema record(s).", len(schema_data))
        return json.dumps(schema_data, default=str)

    # ------------------------------------------------------------------
    # Tool 4 – Dynamic SQL Generation
    # ------------------------------------------------------------------

    @tool
    def generate_sql(self, question: str, schema_context: str) -> str:
        """Generate a SQL query dynamically using the LLM and retrieved schema context.

        Calls the language model with the SQL system prompt, the user question,
        and the schema context returned by ``retrieve_schema``.  Returns the
        generated SQL string only (no explanations, no markdown).

        Args:
            question: The user's natural language question.
            schema_context: JSON string of relevant schema metadata from ``retrieve_schema``.

        Returns:
            Generated SQL SELECT statement as a plain string.
        """
        logger.info("Tool: generate_sql called for question: '%s'.", question)

        user_message = (
            f"Schema Context:\n{schema_context}\n\n"
            f"User Question: {question}\n\n"
            "Generate a single read-only SQL SELECT statement."
        )

        response = self._llm.invoke(
            [
                HumanMessage(content=SQL_SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ]
        )

        sql = response.content.strip()

        # Strip markdown fences if the model included them despite instructions
        if sql.startswith("```"):
            lines = sql.splitlines()
            sql = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        logger.info("SQL generated successfully (length=%d chars).", len(sql))
        return sql

    # ------------------------------------------------------------------
    # Tool 5 – SQL Validation
    # ------------------------------------------------------------------

    @tool
    def validate_sql(self, sql: str) -> str:
        """Validate that a SQL statement is a safe read-only SELECT query.

        Uses the AST-based sqlglot validator to reject any INSERT, UPDATE,
        DELETE, DROP, ALTER, CREATE, MERGE, EXEC, or other non-SELECT statements.

        Args:
            sql: SQL statement to validate.

        Returns:
            ``"VALID"`` if the SQL is safe; ``"INVALID"`` otherwise.
        """
        logger.info("Tool: validate_sql called.")

        is_valid = validate_select_only(sql)

        if is_valid:
            logger.info("SQL validation passed.")
            return "VALID"

        logger.warning("SQL validation failed – non-SELECT statement rejected.")
        return "INVALID"

    # ------------------------------------------------------------------
    # Tool 6 – SQL Execution
    # ------------------------------------------------------------------

    @tool
    def execute_sql(self, sql: str) -> str:
        """Execute a validated SELECT query against the SQL Server database.

        Delegates to :class:`~app.services.database_service.DatabaseService`
        which applies a second validation layer before executing the query.
        Returns a JSON-formatted string containing the rows, columns, and
        row count of the result set.

        Args:
            sql: Validated SELECT statement to execute.

        Returns:
            JSON string with ``rows``, ``columns``, and ``row_count`` keys.

        Raises:
            ValueError: If ``DatabaseService`` rejects the SQL as non-SELECT.
        """
        logger.info("Tool: execute_sql called.")

        result: QueryResult = self._db_service.execute_query(sql=sql)

        output = {
            "columns": result.columns,
            "row_count": result.row_count,
            "rows": result.rows,
        }

        logger.info("SQL executed successfully (%d row(s) returned).", result.row_count)
        return json.dumps(output, default=str)

    # ------------------------------------------------------------------
    # Tool 7 – Save to Cache
    # ------------------------------------------------------------------

    @tool
    def save_sql_cache(
        self,
        question: str,
        sql: str,
        explanation: Optional[str] = None,
    ) -> str:
        """Persist a successfully executed SQL query to the SQL cache.

        Stores the question embedding in Qdrant (vector layer) and the full
        record in SQL Server (storage layer) so that future identical or
        semantically similar questions can be answered without re-generating SQL.

        Args:
            question: The original user question.
            sql: Validated and executed SQL statement.
            explanation: Optional plain-English explanation of the query logic.

        Returns:
            ``"SAVED"`` on success; ``"SAVE_FAILED"`` if an error occurs.
        """
        logger.info("Tool: save_sql_cache called for question: '%s'.", question)

        try:
            self._cache_service.save_cache(
                user_question=question,
                generated_sql=sql,
                sql_explanation=explanation,
            )
            logger.info("SQL query cached successfully.")
            return "SAVED"
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to save SQL cache entry: %s", exc)
            return "SAVE_FAILED"
