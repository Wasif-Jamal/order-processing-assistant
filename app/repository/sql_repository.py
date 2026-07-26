"""Repository for executing validated read-only SQL queries.

Thin data-access layer that executes validated SELECT statements and returns
query results. SQL generation, retrieval, caching, and validation are handled
upstream by the SQL agent and related services.
"""

from sqlalchemy import Engine
from sqlalchemy import text

from app.config.db_config import database
from app.config.log_config import config as log_config
from app.schemas.sql_result_schema import QueryResult

logger = log_config.get_logger(__name__)


class SQLRepository:
    """Executes validated SQL queries against the database."""

    def __init__(self, db_engine: Engine = database.engine) -> None:
        """Initialize the repository.

        Args:
            db_engine: SQLAlchemy engine.
        """
        self._engine = db_engine

    def execute_select(
        self,
        sql: str,
        params: dict | None = None,
    ) -> QueryResult:
        """Execute a validated SELECT statement.

        Args:
            sql: Validated SQL query.
            params: Optional SQL parameters.

        Returns:
            Query execution result.
        """
        logger.info("Executing SQL query.")

        with self._engine.connect() as connection:
            cursor = connection.execute(
                text(sql),
                params or {},
            )

            columns = list(cursor.keys())
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        result = QueryResult(
            rows=rows,
            columns=columns,
            row_count=len(rows),
        )

        logger.info(
            "Query returned %d row(s).",
            result.row_count,
        )

        return result
