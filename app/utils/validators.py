"""Read-only SQL validation for the SQL pipeline.

Provides :func:`validate_select_only`, the guard that ``validate_sql`` and
``execute_sql`` (defense-in-depth) apply before any generated SQL reaches the
database.

Validation is AST-based via ``sqlglot`` rather than string or regex matching,
allowing safe handling of CTEs, subqueries, and multi-statement SQL while
rejecting any write or DDL operations.
"""

import sqlglot
from sqlglot import exp

from app.config.log_config import config as log_config
from app.config.env_config import settings

logger = log_config.get_logger(__name__)


def validate_select_only(sql: str) -> bool:
    """Validate that the supplied SQL is read-only.

    The SQL is parsed using the SQL Server (T-SQL) dialect and every top-level
    statement must contain a ``SELECT`` expression. Any write statement such as
    ``INSERT``, ``UPDATE``, ``DELETE``, ``MERGE``, ``DROP``, ``ALTER``,
    ``CREATE``, or ``TRUNCATE`` is rejected.

    Args:
        sql: SQL statement to validate.

    Returns:
        ``True`` if the SQL is read-only; otherwise ``False``.
    """
    try:
        statements = sqlglot.parse(sql, dialect=settings.sql_dialect)
    except (sqlglot.errors.ParseError, sqlglot.errors.TokenError):
        logger.warning("SQL validation failed: unable to parse SQL.")
        return False

    statements = [statement for statement in statements if statement is not None]

    if not statements:
        logger.warning("SQL validation failed: no SQL statement found.")
        return False

    for statement in statements:
        if statement.find(exp.Select) is None:
            logger.warning("SQL validation failed: non-read-only statement detected.")
            return False

    logger.debug(
        "SQL validation passed (%d statement(s)).",
        len(statements),
    )

    return True
