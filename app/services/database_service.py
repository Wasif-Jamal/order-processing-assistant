"""Database service.

Provides the service layer for executing validated read-only SQL queries.
The service delegates database access to ``SQLRepository`` while enforcing
an additional validation layer before execution.
"""

from app.config.log_config import config as log_config
from app.repository.sql_repository import SQLRepository
from app.schemas.sql_result_schema import QueryResult
from app.utils.validators import validate_select_only

logger = log_config.get_logger(__name__)


class DatabaseService:
    """Service responsible for executing validated SQL queries."""

    def __init__(
        self,
        repository: SQLRepository | None = None,
    ) -> None:
        """Initialize the database service.

        Args:
            repository: Repository used to execute SQL queries.
        """
        self._repository = repository or SQLRepository()

    def execute_query(
        self,
        sql: str,
        params: dict | None = None,
    ) -> QueryResult:
        """Execute a validated SQL query.

        Args:
            sql: Read-only SQL statement.
            params: Optional SQL parameters.

        Returns:
            Query execution result.

        Raises:
            ValueError:
                If the SQL statement is not a valid SELECT query.
        """
        logger.info("Executing validated SQL query.")

        if not validate_select_only(sql):
            logger.warning("SQL validation failed.")
            raise ValueError("Only SELECT statements are allowed.")

        result = self._repository.execute_select(
            sql=sql,
            params=params,
        )

        logger.info(
            "Successfully returned %d row(s).",
            result.row_count,
        )

        return result
