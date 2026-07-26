"""SQL tools used by the SQL Agent.

This module provides the tool methods exposed to the SQL Agent. The current
implementation contains placeholders so the application structure can be
assembled before the remaining services are implemented.
"""

from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.log_config import config as log_config

logger = log_config.get_logger(__name__)


class SqlTools:
    """Collection of tools available to the SQL Agent."""

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        api_base_url: str,
    ) -> None:
        """Initialize the SQL tools.

        Args:
            llm: Language model used for SQL generation.
            api_base_url: Base URL of the application.
        """
        self._llm = llm
        self._api_base_url = api_base_url

    @tool
    def retrieve_cached_sql(self, question: str) -> str:
        """Retrieve a cached SQL query matching the user's question."""
        logger.info("retrieve_cached_sql() called.")
        return "Cache retrieval not implemented."

    @tool
    def retrieve_sql_template(self, question: str) -> str:
        """Retrieve a matching SQL template."""
        logger.info("retrieve_sql_template() called.")
        return "Template retrieval not implemented."

    @tool
    def generate_sql(self, question: str) -> str:
        """Generate SQL for the user's question."""
        logger.info("generate_sql() called.")
        return "SQL generation not implemented."

    @tool
    def validate_sql(self, sql: str) -> str:
        """Validate a generated SQL query."""
        logger.info("validate_sql() called.")
        return "SQL validation not implemented."

    @tool
    def execute_sql(self, sql: str) -> str:
        """Execute a validated SQL query."""
        logger.info("execute_sql() called.")
        return "SQL execution not implemented."
